from core import I18N
from core.plugin import plugin

from ui import theme
from nicegui import ui


class PluginsPage:
    """插件管理页面"""

    def __init__(self):
        self.ID = "plugins"

    def show(self):
        with theme.frame(I18N('plugins.title')):
            ui.label(I18N('plugins.title')).classes('text-h4')
            ui.separator()

            all_plugins = plugin.get_all_plugins()

            if not all_plugins:
                ui.label(I18N('plugins.empty')).classes('text-subtitle1 text-grey mt-4')
                return

            with ui.column().classes('w-full gap-4 mt-4'):
                for name, info in all_plugins.items():
                    self._render_plugin_card(name, info)

            # 渲染插件页面导航
            plugin_pages = plugin.get_plugin_pages()
            if plugin_pages:
                ui.separator().classes('mt-6')
                ui.label(I18N('plugins.page_nav')).classes('text-h5 mt-4')
                with ui.row().classes('w-full gap-2 mt-2'):
                    for page_name, page_handler in plugin_pages.items():
                        meta = all_plugins[page_name].meta if page_name in all_plugins else None
                        display = meta.display_name if meta else page_name
                        ui.button(
                            display,
                            on_click=lambda _, p=page_name: ui.navigate.to(f'/plugin/{p}'),
                        ).props('color=primary outline')

    def _render_plugin_card(self, name, info):
        meta = info.meta
        status_color = 'green' if info.loaded else ('red' if info.error else 'grey')
        status_text = '已加载' if info.loaded else ('加载失败' if info.error else '未初始化')

        with ui.card().classes('w-full'):
            with ui.row().classes('w-full items-center justify-between'):
                with ui.column().classes('gap-0'):
                    with ui.row().classes('items-center gap-2'):
                        ui.label(meta.display_name).classes('text-h6')
                        ui.badge(meta.version).props('color=secondary')
                        ui.badge(status_text).props(f'color={status_color}')
                    ui.label(f'作者: {meta.author}').classes('text-caption')
                    if meta.desc:
                        ui.label(meta.desc).classes('text-caption text-grey')

                if info.error:
                    ui.button(icon='error', on_click=lambda e=info.error: ui.notify(
                        e, type='negative', multi_line=True, timeout=0
                    )).props('flat color=red')
