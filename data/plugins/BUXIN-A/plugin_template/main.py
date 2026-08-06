from core import logger
from core import I18N
from core.plugin.register import initialization, filter

from nicegui import ui
import json5
import os

class Plugin:
    def __init__(self, mct=None):
        self.mct = mct

    async def initialize(self):
        """
        可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。
        """
        global plugin_guide
        print("plugin_template 插件初始化")
        with open(os.path.join(os.path.dirname(__file__), "PluginGuide.md"), "r", encoding="utf-8") as f:
            plugin_guide = f.read()

    @filter.page('plugin_template', title='插件模板')
    async def page(self):
        ui.label('插件模板').classes('text-h2')
        ui.markdown(f'''
# 如何开发插件？
{plugin_guide}
''')