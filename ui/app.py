import asyncio

from nicegui import ui

from ui.pages import home
from ui.pages import tools
from ui.pages import plugins
from ui.pages import settings
from ui.pages import about

from core.plugin import plugin

class App:
    def __init__(self) -> None:
        @ui.page('/')
        def home_page():
            home.HomePage().show()
        @ui.page('/tools')
        def tools_page():
            tools.ToolsPage().show()
        @ui.page('/plugins')
        def plugins_page():
            plugins.PluginsPage().show()
        @ui.page('/settings')
        def setting_page():
            settings.SettingPage().show()
        @ui.page('/about')
        def about_page():
            about.AboutPage().show()
        
    def run(self) -> None:
        plugin.run_plugins()
        plugin.register_plugin_pages()
        
        ui.run()
