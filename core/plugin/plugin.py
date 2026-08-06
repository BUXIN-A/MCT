import os
import importlib.util
import asyncio
import inspect
import traceback
import shutil
import zipfile
import tempfile

import yaml

from core.logging import logger
from core.plugin.register.handler import initialization
from ui import theme

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "plugins")
PLUGIN_DIR = os.path.abspath(PLUGIN_DIR)

PLUGIN_CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "plugins_config.json")
PLUGIN_CONFIG_DIR = os.path.abspath(PLUGIN_CONFIG_DIR)


class PluginMeta:
    """插件元数据"""

    def __init__(self, name, display_name="", desc="", version="0.0.0", author="", repo=""):
        self.name = name
        self.display_name = display_name or name
        self.desc = desc
        self.version = version
        self.author = author
        self.repo = repo

    @classmethod
    def from_yaml(cls, path):
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
    """单个插件的完整信息"""

    def __init__(self, author, plugin_dir, meta, module, plugin_cls, instance):
        self.author = author
        self.dir = plugin_dir
        self.meta = meta
        self.module = module
        self.plugin_cls = plugin_cls
        self.instance = instance
        self.loaded = False
        self.error = None


_plugin_cache = None


def discover_plugins():
    """扫描插件目录，返回 {plugin_name: PluginInfo} 字典"""
    global _plugin_cache
    if _plugin_cache is not None:
        return _plugin_cache

    plugins = {}

    if not os.path.isdir(PLUGIN_DIR):
        logger.warning("插件目录不存在: %s", PLUGIN_DIR)
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


def _load_single_plugin(author, plugin_dir_name, plugin_path):
    """加载单个插件，返回 PluginInfo 或 None"""
    meta_path = os.path.join(plugin_path, "metadata.yaml")
    meta = PluginMeta.from_yaml(meta_path)
    if meta is None:
        meta = PluginMeta(name=plugin_dir_name, author=author)
    if not meta.author:
        meta.author = author

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
            spec.loader.exec_module(module)
        except Exception:
            logger.error("加载插件 %s/%s 的模块 %s 失败:\n%s", author, plugin_dir_name, filename, traceback.format_exc())
            continue

        plugin_cls = getattr(module, "Plugin", None)
        if plugin_cls is not None:
            break

    if plugin_cls is None:
        logger.warning("插件 %s/%s 没有定义 Plugin 类，跳过", author, plugin_dir_name)
        return None

    # 检查 initialization 注册表中是否已注册此插件
    registered = initialization.get(meta.name)
    if registered is not None:
        logger.debug("插件 %s 已通过 @initialization.register 注册，跳过重复实例化", meta.name)
        # 使用注册表中的类而非重新加载
        plugin_cls = registered["class"]

    try:
        instance = plugin_cls()
    except TypeError:
        try:
            instance = plugin_cls(None)
        except Exception:
            logger.error("实例化插件 %s/%s 失败:\n%s", author, plugin_dir_name, traceback.format_exc())
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


def _run_async(coro):
    """在已有或新的事件循环中运行协程"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        # 已有事件循环运行中（如 NiceGUI），使用 ensure_future 调度
        # 注意：调用方需自行 await 产生的 task
        import warnings
        warnings.warn("在已有事件循环中调用异步插件初始化，请确保在异步上下文中运行", RuntimeWarning)
        return asyncio.ensure_future(coro)
    else:
        # 无事件循环，直接运行
        return asyncio.run(coro)


def run_plugins(mct=None):
    """初始化并运行所有已发现的插件"""
    plugins = discover_plugins()
    disabled = get_disabled_plugins()

    for name, info in plugins.items():
        if name in disabled:
            logger.info("插件 %s 已禁用，跳过初始化", name)
            continue

        init_method = getattr(info.instance, "initialize", None)
        if init_method is None:
            logger.warning("插件 %s 没有定义 initialize 方法，跳过", name)
            continue

        try:
            sig = inspect.signature(init_method)
            if len(sig.parameters) > 1:
                result = init_method(mct)
            else:
                result = init_method()
            if inspect.isawaitable(result):
                _run_async(result)

            info.loaded = True
            logger.info("插件 %s (%s) 初始化成功", info.meta.display_name, info.meta.version)
        except Exception:
            info.error = traceback.format_exc()
            logger.error("插件 %s 初始化失败:\n%s", name, info.error)


def register_plugin_pages():
    """将所有插件页面注册为 NiceGUI 路由"""
    from nicegui import ui

    pages = get_plugin_pages()
    all_plugins = get_all_plugins()
    disabled = get_disabled_plugins()

    for page_id, page_handler in pages.items():
        if page_id in disabled:
            continue

        meta = all_plugins[page_id].meta if page_id in all_plugins else None
        title = meta.display_name if meta else page_id

        @ui.page(f'/plugin/{page_id}')
        async def _page_handler(_handler=page_handler, _title=title):
            with theme.frame(_title):
                result = _handler()
                if inspect.isawaitable(result):
                    await result


def get_plugin_pages():
    """获取所有插件的页面处理函数 {plugin_name: page_handler}"""
    plugins = discover_plugins()
    pages = {}

    for name, info in plugins.items():
        page_handler = getattr(info.instance, "page", None)
        if page_handler is not None:
            pages[name] = page_handler

    return pages


def get_all_plugins():
    """获取所有已发现的插件信息"""
    return discover_plugins()


def get_plugin(name):
    """按名称获取单个插件信息"""
    return discover_plugins().get(name)


def _load_plugins_config():
    """读取插件配置文件"""
    import json5
    if not os.path.exists(PLUGIN_CONFIG_DIR):
        return {"disabled": []}
    try:
        with open(PLUGIN_CONFIG_DIR, "r", encoding="utf-8") as f:
            return json5.load(f) or {"disabled": []}
    except Exception:
        return {"disabled": []}


def _save_plugins_config(config):
    """保存插件配置文件"""
    import json5
    with open(PLUGIN_CONFIG_DIR, "w", encoding="utf-8") as f:
        json5.dump(config, f, ensure_ascii=False, indent=4, quote_keys=True)


def get_disabled_plugins():
    """获取已禁用的插件列表"""
    return _load_plugins_config().get("disabled", [])


def set_plugin_disabled(name, disabled):
    """设置插件禁用状态"""
    config = _load_plugins_config()
    disabled_list = config.get("disabled", [])
    if disabled and name not in disabled_list:
        disabled_list.append(name)
    elif not disabled and name in disabled_list:
        disabled_list.remove(name)
    config["disabled"] = disabled_list
    _save_plugins_config(config)


def reload_plugins(mct=None):
    """强制重新加载所有插件"""
    global _plugin_cache
    _plugin_cache = None
    initialization.plugins.clear()
    plugins = discover_plugins()
    run_plugins(mct)
    return plugins


def import_plugin(zip_path):
    """从 zip 文件导入插件，返回 (success, message)"""
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
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            os.makedirs(target_dir, exist_ok=True)

            for member in zf.namelist():
                parts = member.split('/')
                if len(parts) <= 1:
                    continue
                relative = '/'.join(parts[1:])
                if not relative:
                    continue
                target_path = os.path.join(target_dir, relative)
                if member.endswith('/'):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zf.open(member) as src, open(target_path, 'wb') as dst:
                        dst.write(src.read())

        logger.info("插件 %s 导入成功", plugin_name)
        return True, plugin_name
    except Exception as e:
        logger.error("插件导入失败: %s", traceback.format_exc())
        return False, str(e)


def export_plugin(name):
    """导出插件为 zip 文件，返回 zip 文件路径或 None"""
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

        logger.info("插件 %s 导出成功: %s", name, zip_path)
        return zip_path
    except Exception as e:
        logger.error("插件导出失败: %s", traceback.format_exc())
        return None


def delete_plugin(name):
    """删除插件目录，返回 (success, message)"""
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

        logger.info("插件 %s 已删除", name)
        return True, name
    except Exception as e:
        logger.error("插件删除失败: %s", traceback.format_exc())
        return False, str(e)
