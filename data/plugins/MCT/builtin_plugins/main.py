from core import logger
from core import I18N
from nicegui import ui

from core.plugin.register import initialization, filter


class Plugin:
    def __init__(self, mct=None):
        self.mct = mct

    async def initialize(self):
        """
        可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。
        """
        print("builtin_plugins 插件初始化")

    @filter.page('builtin_plugins', title='内置插件')
    async def page(self):
        ui.label('builtin_plugins 插件页面')
