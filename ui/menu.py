from core import I18N
from core.plugin import plugin

from nicegui import ui

menu_list = [
    {'name': 'home.title', 'url': '/'},
    {'name': 'tools.title', 'url': '/tools'},
    {'name': 'plugins.title', 'url': '/plugins'},
    {'name': 'settings.title', 'url': '/settings'},
    {'name': 'about.title', 'url': '/about'}
]


@ui.refreshable
def menu() -> None:
    with ui.button_group().classes('flex-col items-stretch w-full').style('width: calc(100% - 40px); margin-left: 20px; margin-right: 20px;'):
        for item in menu_list:
            ui.button(I18N(item['name']), on_click=lambda : ui.navigate.to(item['url'])).classes('w-full text-left').style('text-decoration: none;')

    plugin_pages = plugin.get_plugin_pages()
    all_plugins = plugin.get_all_plugins()

    if plugin_pages:
        with ui.dropdown_button(I18N('plugin_pages.title'), auto_close=True).style(
            'width: calc(100% - 40px); margin-left: 20px; margin-right: 20px;'
        ):
            for page_name, page_handler in plugin_pages.items():
                meta = all_plugins[page_name].meta if page_name in all_plugins else None
                display = meta.display_name if meta else page_name
                ui.item(display, on_click=lambda _, p=page_name: ui.navigate.to(f'/plugin/{p}'))
