"""Plugin system"""
import functools
import os
import importlib.util
import asyncio
import inspect
import traceback
import shutil
import zipfile
import tempfile
from contextlib import contextmanager
from typing import Any, Optional

import nicegui
import yaml
from nicegui import ui

from core import I18N
from core.logging import logger
from core.plugin.register.handler import initialization
from core.plugin.register.filter import filter as plugin_filter
from ui import theme

PLUGIN_DIR: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "plugins")
)

PLUGIN_CONFIG_DIR: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "plugins_config.json")
)

MAX_PLUGIN_SIZE: int = 512 * 1024 * 1024


class PluginMeta:
    """Plugin metadata loaded from metadata.yaml."""

    def __init__(
        self,
        name: str,
        display_name: str = "",
        desc: str = "",
        version: str = "0.0.0",
        author: str = "",
        repo: str = "",
    ) -> None:
        self.name = name
        self.display_name = display_name or name
        self.desc = desc
        self.version = version
        self.author = author
        self.repo = repo

    @classmethod
    def from_yaml(cls, path: str) -> Optional["PluginMeta"]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return cls(
                name=data.get("name", ""),
                display_name=data.get("display_name", ""),
                desc=data.get("desc", ""),
                version=data.get("version", "0.0.0"),
                author=data.get("author", ""),
                repo=data.get("repo", ""),
            )
        except Exception:
            return None


class PluginInfo:
    """Full state for a single plugin."""

    def __init__(
        self,
        author: str,
        plugin_dir: str,
        meta: PluginMeta,
        module: Any,
        plugin_cls: Any,
        instance: Any,
    ) -> None:
        self.author = author
        self.dir = plugin_dir
        self.meta = meta
        self.module = module
        self.plugin_cls = plugin_cls
        self.instance = instance
        self.loaded = False
        self.error: Optional[str] = None


_plugin_cache: Optional[dict[str, PluginInfo]] = None
_running_tasks: set[asyncio.Task] = set()


def discover_plugins() -> dict[str, PluginInfo]:
    """Scan plugin directory and return {plugin_name: PluginInfo} dict."""
    global _plugin_cache
    if _plugin_cache is not None:
        return _plugin_cache

    plugins: dict[str, PluginInfo] = {}

    if not os.path.isdir(PLUGIN_DIR):
        logger.warning("Plugin directory does not exist: %s", PLUGIN_DIR)
        _plugin_cache = plugins
        return plugins

    for author in os.listdir(PLUGIN_DIR):
        author_path = os.path.join(PLUGIN_DIR, author)
        if not os.path.isdir(author_path):
            continue

        for plugin_name in os.listdir(author_path):
            plugin_path = os.path.join(author_path, plugin_name)
            if not os.path.isdir(plugin_path):
                continue

            info = _load_single_plugin(author, plugin_name, plugin_path)
            if info is not None:
                plugins[info.meta.name or plugin_name] = info

    _plugin_cache = plugins
    return plugins


@contextmanager
def _guarded_ui_page(plugin_key: str):
    """
    插件模块加载期间临时包装 nicegui 的 @ui.page。

    插件若直接使用 @ui.page 注册路由，这些路由不会经过统一的
    /plugin/{page_id} 入口。包装后，路由处理器会在请求时检查插件
    是否被禁用，禁用则跳转回插件页，从而保证禁用后页面不可访问。
    """
    page = getattr(nicegui.ui, "page", None)
    if page is None:
        yield
        return

    def _page_wrapper(path, *args, **kwargs):
        def decorator(func):
            @functools.wraps(func)
            async def _guarded(*a, **kw):
                if plugin_key in get_disabled_plugins():
                    ui.navigate.to('/plugins')
                    return
                result = func(*a, **kw)
                if inspect.isawaitable(result):
                    await result
            return page(path, *args, **kwargs)(_guarded)
        return decorator

    nicegui.ui.page = _page_wrapper
    try:
        yield
    finally:
        nicegui.ui.page = page


def _load_single_plugin(
    author: str, plugin_dir_name: str, plugin_path: str
) -> Optional[PluginInfo]:
    """Load a single plugin. Returns PluginInfo or None."""
    meta_path = os.path.join(plugin_path, "metadata.yaml")
    meta = PluginMeta.from_yaml(meta_path)
    if meta is None:
        meta = PluginMeta(name=plugin_dir_name, author=author)
    if not meta.author:
        meta.author = author

    plugin_key = meta.name or plugin_dir_name

    # 禁用插件：不执行任何模块代码（不加载、不注册页面），仅保留元信息。
    # 保证禁用后插件完全停止运行，且其 @ui.page 路由不会被重复注册。
    if plugin_key in get_disabled_plugins():
        logger.info("Plugin %s is disabled, skipping module load", plugin_key)
        return PluginInfo(
            author=author,
            plugin_dir=plugin_path,
            meta=meta,
            module=None,
            plugin_cls=None,
            instance=None,
        )

    module = None
    plugin_cls = None
    instance = None

    for filename in os.listdir(plugin_path):
        if not filename.endswith(".py"):
            continue

        module_name = filename[:-3]
        module_path = os.path.join(plugin_path, filename)

        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                continue

            module = importlib.util.module_from_spec(spec)
            # 加载期间拦截 @ui.page，使插件直接注册的路由也能感知禁用状态
            with _guarded_ui_page(plugin_key):
                spec.loader.exec_module(module)
            logger.debug(
                "Plugin module loaded: %s/%s [%s]",
                author, plugin_dir_name, filename,
            )
        except Exception:
            logger.error(
                "Failed to load module %s/%s/%s:\n%s",
                author, plugin_dir_name, filename, traceback.format_exc(),
            )
            continue

        plugin_cls = getattr(module, "Plugin", None)
        if plugin_cls is not None:
            break

    if plugin_cls is None:
        logger.warning(
            "Plugin %s/%s does not define a Plugin class, skipping",
            author, plugin_dir_name,
        )
        return None

    # Check if already registered via @initialization.register
    registered = initialization.get(meta.name)
    if registered is not None:
        logger.debug(
            "Plugin %s already registered via @initialization.register, "
            "skipping duplicate instantiation", meta.name,
        )
        plugin_cls = registered["class"]

    logger.warning(
        "SECURITY: Executing plugin code from %s/%s — "
        "plugins run arbitrary Python code with full host access. "
        "Only install plugins from trusted sources.",
        author, plugin_dir_name,
    )

    try:
        instance = plugin_cls()
    except TypeError as e:
        sig = inspect.signature(plugin_cls)
        params = list(sig.parameters.keys())
        logger.error(
            "Plugin %s/%s constructor %s() does not match signature %s. "
            "Plugin class must accept 0 arguments (got TypeError: %s)",
            author, plugin_dir_name, plugin_cls.__name__, params, e,
        )
        return None
    except Exception:
        logger.error(
            "Failed to instantiate plugin %s/%s:\n%s",
            author, plugin_dir_name, traceback.format_exc(),
        )
        return None

    info = PluginInfo(
        author=author,
        plugin_dir=plugin_path,
        meta=meta,
        module=module,
        plugin_cls=plugin_cls,
        instance=instance,
    )
    return info


def _run_async(coro: Any) -> Optional[asyncio.Task]:
    """
    在当前运行中的事件循环上调度协程
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        task = loop.create_task(coro)
        _running_tasks.add(task)
        task.add_done_callback(_running_tasks.discard)
        task.add_done_callback(_log_task_error)
        return task
    return asyncio.run(coro)


def _log_task_error(task: asyncio.Task) -> None:
    """记录后台任务未被捕获的异常。"""
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.error("Plugin async initialization task failed: %s", exc)


async def _initialize_plugin(info: PluginInfo, init_method: Any, mct: Any) -> None:
    """执行单个插件的 initialize，统一处理同步/异步返回与异常记录。"""
    try:
        sig = inspect.signature(init_method)
        if len(sig.parameters) > 1:
            result = init_method(mct)
        else:
            result = init_method()
        if inspect.isawaitable(result):
            await result

        info.loaded = True
        logger.info(
            "Plugin %s (%s) initialized successfully",
            info.meta.display_name, info.meta.version,
        )
    except Exception:
        info.error = traceback.format_exc()
        logger.error(
            "Plugin %s initialization failed:\n%s",
            info.meta.name, info.error,
        )


def run_plugins(mct: Any = None) -> None:
    """Initialize and run all discovered plugins."""
    plugins = discover_plugins()
    disabled = get_disabled_plugins()

    for name, info in plugins.items():
        if name in disabled:
            logger.info("Plugin %s is disabled, skipping initialization", name)
            continue

        init_method = getattr(info.instance, "initialize", None)
        if init_method is None:
            logger.warning("Plugin %s has no initialize method, skipping", name)
            continue

        if mct is not None and hasattr(info.instance, "mct"):
            info.instance.mct = mct

        _run_async(_initialize_plugin(info, init_method, mct))


def register_plugin_pages() -> None:
    """
    注册统一的插件页面入口 /plugin/{page_id}。

    采用单一 catch-all 路由 + 请求时动态分派：
    - 插件禁用状态在每次请求时检查，启用/禁用即时生效；
    - 不再为每个插件单独注册路由，避免禁用后旧路由残留。
    """
    @ui.page('/plugin/{page_id}')
    async def _plugin_page(page_id: str):
        if page_id in get_disabled_plugins():
            ui.notify(I18N('plugins.status.disabled'), type='warning')
            ui.navigate.to('/plugins')
            return

        handler = get_plugin_pages().get(page_id)
        if handler is None:
            ui.notify(I18N('plugins.page_not_found'), type='warning')
            ui.navigate.to('/plugins')
            return

        meta = None
        all_plugins = get_all_plugins()
        if page_id in all_plugins:
            meta = all_plugins[page_id].meta
        title = meta.display_name if meta else page_id

        with theme.frame(title):
            result = handler()
            if inspect.isawaitable(result):
                await result


def get_plugin_pages() -> dict[str, Any]:
    """Get all plugin page handlers {plugin_name: page_handler}."""
    plugins = discover_plugins()
    pages: dict[str, Any] = {}

    for name, info in plugins.items():
        page_handler = getattr(info.instance, "page", None)
        if page_handler is not None:
            pages[name] = page_handler

    return pages


def get_all_plugins() -> dict[str, PluginInfo]:
    """Get all discovered plugins."""
    return discover_plugins()


def get_plugin(name: str) -> Optional[PluginInfo]:
    """Get a single plugin by name."""
    return discover_plugins().get(name)


def _load_plugins_config() -> dict:
    """Read the plugins config file."""
    import json5
    if not os.path.exists(PLUGIN_CONFIG_DIR):
        return {"disabled": []}
    try:
        with open(PLUGIN_CONFIG_DIR, "r", encoding="utf-8") as f:
            return json5.load(f) or {"disabled": []}
    except Exception:
        return {"disabled": []}


def _save_plugins_config(config: dict) -> None:
    """Write the plugins config file."""
    import json5
    with open(PLUGIN_CONFIG_DIR, "w", encoding="utf-8") as f:
        json5.dump(config, f, ensure_ascii=False, indent=4, quote_keys=True)


def get_disabled_plugins() -> list[str]:
    """Get list of disabled plugin names."""
    return _load_plugins_config().get("disabled", [])


def set_plugin_disabled(name: str, disabled: bool) -> None:
    """Set the disabled state of a plugin."""
    config = _load_plugins_config()
    disabled_list = config.get("disabled", [])
    if disabled and name not in disabled_list:
        disabled_list.append(name)
    elif not disabled and name in disabled_list:
        disabled_list.remove(name)
    config["disabled"] = disabled_list
    _save_plugins_config(config)


def reload_plugins(mct: Any = None) -> dict[str, PluginInfo]:
    """Force reload all plugins."""
    global _plugin_cache
    _plugin_cache = None
    initialization.plugins.clear()
    plugin_filter.pages.clear()
    plugins = discover_plugins()
    run_plugins(mct)
    return plugins


def _invalidate_cache() -> None:
    """Clear the plugin discovery cache."""
    global _plugin_cache
    _plugin_cache = None


def _cleanup_import(target_dir: str) -> None:
    """删除导入失败时留下的插件目录，以及因此变为空的作者目录。"""
    shutil.rmtree(target_dir, ignore_errors=True)
    author_dir = os.path.dirname(target_dir)
    try:
        if os.path.isdir(author_dir) and not os.listdir(author_dir):
            os.rmdir(author_dir)
    except OSError:
        pass


def import_plugin(zip_path: str) -> tuple[bool, str]:
    """Import a plugin from a zip file. Returns (success, message)."""
    target_dir = None
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            meta_found = False
            author = None
            plugin_name = None

            for name in zf.namelist():
                if name.endswith('metadata.yaml'):
                    meta_found = True
                    with zf.open(name) as f:
                        data = yaml.safe_load(f) or {}
                    author = data.get("author", "")
                    plugin_name = data.get("name", "")
                    break

            if not meta_found or not author or not plugin_name:
                return False, "Invalid plugin: missing metadata.yaml or author/name"

            target_dir = os.path.join(PLUGIN_DIR, author, plugin_name)
            target_dir = os.path.abspath(target_dir)

            if not target_dir.startswith(os.path.abspath(PLUGIN_DIR) + os.sep) \
                    and target_dir != os.path.abspath(PLUGIN_DIR):
                return False, "Invalid plugin path: directory traversal detected"

            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)

            total_size = 0
            for member in zf.namelist():
                parts = member.split('/')
                if len(parts) <= 1:
                    continue
                relative = '/'.join(parts[1:])
                if not relative:
                    continue
                target_path = os.path.join(target_dir, relative)
                target_path = os.path.abspath(target_path)

                if not target_path.startswith(target_dir + os.sep) \
                        and target_path != target_dir:
                    logger.warning(
                        "Zip slip attempt blocked: %s tries to escape to %s",
                        member, target_path,
                    )
                    _cleanup_import(target_dir)
                    return False, f"Invalid path in zip: {member}"

                if member.endswith('/'):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    total_size += zf.getinfo(member).file_size
                    if total_size > MAX_PLUGIN_SIZE:
                        logger.warning(
                            "Plugin %s exceeds maximum unpacked size, aborting",
                            plugin_name,
                        )
                        _cleanup_import(target_dir)
                        return False, "Plugin exceeds maximum unpacked size"
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(member) as src, open(target_path, 'wb') as dst:
                        dst.write(src.read())

            # 校验
            if not os.path.isfile(os.path.join(target_dir, "metadata.yaml")):
                logger.warning(
                    "Plugin %s has an invalid zip structure "
                    "(expected a single '<plugin_name>/' folder), cleaning up",
                    plugin_name,
                )
                _cleanup_import(target_dir)
                return False, (
                    "Invalid plugin structure: zip must contain a single "
                    f"'{plugin_name}/' folder"
                )

        _invalidate_cache()

        logger.info("Plugin %s imported successfully", plugin_name)
        return True, plugin_name
    except Exception as e:
        logger.error("Plugin import failed: %s", traceback.format_exc())
        if target_dir is not None:
            _cleanup_import(target_dir)
        return False, str(e)


def export_plugin(name: str) -> Optional[str]:
    """Export a plugin to a zip file. Returns zip file path or None."""
    plugins = discover_plugins()
    if name not in plugins:
        return None

    info = plugins[name]
    plugin_dir = info.dir

    try:
        tmp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(tmp_dir, f"{name}.zip")

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(plugin_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(plugin_dir))
                    zf.write(file_path, arcname)

        logger.info("Plugin %s exported: %s", name, zip_path)
        return zip_path
    except Exception:
        logger.error("Plugin export failed:\n%s", traceback.format_exc())
        return None


def delete_plugin(name: str) -> tuple[bool, str]:
    """Delete a plugin directory. Returns (success, message)."""
    plugins = discover_plugins()
    if name not in plugins:
        return False, f"Plugin '{name}' not found"

    info = plugins[name]
    plugin_dir = info.dir

    try:
        set_plugin_disabled(name, True)
        shutil.rmtree(plugin_dir)

        author_dir = os.path.dirname(plugin_dir)
        if os.path.exists(author_dir) and not os.listdir(author_dir):
            os.rmdir(author_dir)

        # 清理注册表残留
        initialization.plugins.pop(name, None)
        plugin_filter.pages.pop(name, None)

        _invalidate_cache()

        logger.info("Plugin %s deleted", name)
        return True, name
    except Exception:
        logger.error("Plugin deletion failed:\n%s", traceback.format_exc())
        return False, traceback.format_exc()
