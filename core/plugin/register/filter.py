from core.logging import logger


class filter:
    pages = {}

    @classmethod
    def page(cls, page_id, title=None, icon=None):
        def decorator(func):
            cls.pages[page_id] = {
                "handler": func,
                "title": title or page_id,
                "icon": icon,
            }
            logger.debug("插件页面注册: %s", page_id)
            return func
        return decorator

    @classmethod
    def get(cls, page_id):
        return cls.pages.get(page_id)

    @classmethod
    def all(cls):
        return dict(cls.pages)
