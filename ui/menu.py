from core import I18N

from nicegui import ui

menu_list = [
    {'name': 'home.title', 'url': '/'},
    {'name': 'resource.title', 'url': '/resources'},
    {'name': 'setting.title', 'url': '/settings'},
    {'name': 'about.title', 'url': '/about'},
]

@ui.refreshable
def menu() -> None:
    for item in menu_list:
        ui.link(I18N(item['name']), item['url']).classes(replace='text-black')
