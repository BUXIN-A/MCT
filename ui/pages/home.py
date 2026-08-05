from core import I18N

from ui import theme
from nicegui import ui

class HomePage:
    """首页"""
    def __init__(self):
        self.ID = "home"
    def show(self):
        with theme.frame(I18N('home.title')):
            ui.label(I18N('home.title')).classes('text-h4')
            ui.markdown(I18N('home.content'))