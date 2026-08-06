from core.logging import logger


class initialization:
    """插件注册装饰器 — 用于声明式注册插件元信息"""

    plugins = {}

    @classmethod
    def register(cls, category, name, description="", version="0.0.0"):
        def decorator(plugin_cls):
            cls.plugins[name] = {
                "category": category,
                "name": name,
                "description": description,
                "version": version,
                "class": plugin_cls,
            }
            logger.debug("插件注册: %s (%s)", name, category)
            return plugin_cls
        return decorator

    @classmethod
    def get(cls, name):
        return cls.plugins.get(name)

    @classmethod
    def get_by_category(cls, category):
        return {
            k: v for k, v in cls.plugins.items()
            if v["category"] == category
        }

    @classmethod
    def all(cls):
        return dict(cls.plugins)
