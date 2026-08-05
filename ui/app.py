from nicegui import ui

from ui.pages import home
from ui.pages import resources
from ui.pages import settings
from ui.pages import about

class App:
    def __init__(self) -> None:
        @ui.refreshable
        @ui.page('/')
        def home_page():
            home.HomePage().show()
        @ui.page('/resources')
        def resources_page():
            resources.ResourcesPage().show()
        @ui.page('/settings')
        def setting_page():
            settings.SettingPage().show()
        @ui.page('/about')
        def about_page():
            about.HomePage().show()
        
    def run(self) -> None:
        ui.run()