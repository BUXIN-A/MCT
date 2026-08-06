import os
import importlib.util
import asyncio
import inspect
import traceback

import yaml

from core.logging import logger
from core.plugin.register.handler import initialization
from ui import theme

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "plugins")
PLUGIN_DIR = os.path.abspath(PLUGIN_DIR)


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

    for name, info in plugins.items():
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

    for page_id, page_handler in pages.items():
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


def reload_plugins(mct=None):
    """强制重新加载所有插件"""
    global _plugin_cache
    _plugin_cache = None
    # 清空 initialization 注册表中的旧条目
    initialization.plugins.clear()
    plugins = discover_plugins()
    run_plugins(mct)
    return plugins
