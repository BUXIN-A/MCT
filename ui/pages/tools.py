from core import I18N
from core import logger

from ui import theme
from nicegui import ui

from ui.pages.tool import resource

class ToolsPage:
    """工具页面"""
    def __init__(self):
        self.ID = "tools"
        self.tool_list = [
            {
                "id": "tool.resource",
                "page": "/tools/resource",
                "title": I18N('tool.resource.title'),
                "icon": "assets/images/resource.png",
                "description": I18N('tool.resource.description'),
            }
        ]
        @ui.page('/tools/resource')
        def tool_resource_page():
            resource.ToolResourcePage().show()

    def open_tool(self, page):
        ui.navigate.to(page)
        logger.info(f'进入界面 "{page}"')

    def show(self):
        with theme.frame(I18N('tools.title')):
            ui.label(I18N('tools.title')).classes('text-h4')
            for tool in self.tool_list:
                with ui.card().classes('w-full max-w-lg'):
                    with ui.row():
                        ui.image(tool['icon']).classes('w-16 h-16')
                        ui.label(tool['title']).classes('text-h6')
                        ui.label(tool['description']).classes('text-body-1')
                        ui.button(I18N('tools.open'), on_click=lambda page=tool['page']: self.open_tool(page)).classes('ml-auto')