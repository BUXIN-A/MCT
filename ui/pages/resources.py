from core import I18N

from ui import theme
from nicegui import ui

class ResourcesPage:
    """资源页面"""
    def __init__(self):
        self.ID = "resources"
    def show(self):
        with theme.frame(I18N('resource.title')):
            ui.label(I18N('resource.title')).classes('text-h4')
