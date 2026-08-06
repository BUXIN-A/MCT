from core import I18N

from ui import theme
from nicegui import ui

class ToolsPage:
    """工具页面"""
    def __init__(self):
        self.ID = "tools"
    def show(self):
        with theme.frame(I18N('tools.title')):
            ui.label(I18N('tools.title')).classes('text-h4')
