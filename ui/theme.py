from core import I18N
from core import config

from contextlib import contextmanager
from nicegui import ui
from ui import menu

@contextmanager
def frame(navtitle: str):
    # 设置全局主题
    ui.colors(primary=config.Function().get_config_value('theme.primary'), secondary=config.Function().get_config_value('theme.secondary'), accent=config.Function().get_config_value('theme.accent'))
    
    # 左侧抽屉菜单
    with ui.left_drawer().classes('bg-blue-100') as left_drawer:
        ui.label(I18N('menu')).classes('text-lg font-bold p-4 text-center w-full')
        menu.menu()

    # 顶部导航栏
    with ui.header().classes(replace='row items-center') as header:
        ui.button(on_click=left_drawer.toggle, icon='menu').props('flat color=white')
        ui.label(navtitle).classes('font-bold')

    # 页面主体内容
    with ui.column().classes('items-start justify-start h-screen no-wrap p-9 w-full overflow-y-auto'):
        yield