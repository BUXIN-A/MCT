from core import I18N
from core import i18n_key_exists
from core.plugin import plugin

from ui import theme
from nicegui import ui
import os
import shutil
import tempfile
import threading


def _schedule_temp_cleanup(directory, delay: float = 60.0) -> None:
    threading.Timer(
        delay,
        lambda: shutil.rmtree(directory, ignore_errors=True),
    ).start()


class PluginsPage:
    """插件管理页面"""

    def __init__(self):
        self.ID = "plugins"

    def show(self):
        with theme.frame(I18N('plugins.title')):
            ui.label(I18N('plugins.title')).classes('text-h4')
            ui.separator()

            with ui.row().classes('w-full items-center justify-between mt-4'):
                ui.label(I18N('plugins.title')).classes('text-h6')
                with ui.row().classes('gap-2'):
                    ui.upload(
                        label=I18N('plugins.import'),
                        auto_upload=True,
                        on_upload=self._handle_import,
                    ).props('accept=.zip flat color=primary')

            all_plugins = plugin.get_all_plugins()
            disabled_list = plugin.get_disabled_plugins()

            if not all_plugins:
                ui.label(I18N('plugins.empty')).classes('text-subtitle1 text-grey mt-4')
                return

            with ui.column().classes('w-full gap-4 mt-4'):
                for name, info in all_plugins.items():
                    self._render_plugin_card(name, info, name in disabled_list)

            plugin_pages = plugin.get_plugin_pages()
            enabled_pages = {k: v for k, v in plugin_pages.items() if k not in disabled_list}
            if enabled_pages:
                ui.separator().classes('mt-6')
                ui.label(I18N('plugins.page_nav')).classes('text-h5 mt-4')
                with ui.row().classes('w-full gap-2 mt-2'):
                    for page_name, page_handler in enabled_pages.items():
                        meta = all_plugins[page_name].meta if page_name in all_plugins else None
                        display = meta.display_name if meta else page_name
                        ui.button(
                            display,
                            on_click=lambda _, p=page_name: ui.navigate.to(f'/plugin/{p}'),
                        ).props('color=primary outline')

    def _render_plugin_card(self, name, info, is_disabled):
        meta = info.meta
        if is_disabled:
            status_color = 'grey'
            status_text = I18N('plugins.status.disabled')
        elif info.loaded:
            status_color = 'green'
            status_text = I18N('plugins.status.loaded')
        elif info.error:
            status_color = 'red'
            status_text = I18N('plugins.status.error')
        else:
            status_color = 'grey'
            status_text = I18N('plugins.status.uninit')

        with ui.card().classes('w-full'):
            with ui.row().classes('w-full items-center justify-between'):
                with ui.column().classes('gap-0'):
                    with ui.row().classes('items-center gap-2'):
                        ui.label(meta.display_name).classes('text-h6')
                        ui.badge(meta.version).props('color=secondary')
                        ui.badge(status_text).props(f'color={status_color}')
                    ui.label(f'{I18N("plugins.detail.author")}: {meta.author}').classes('text-caption')
                    if meta.desc:
                        ui.label(meta.desc).classes('text-caption text-grey')

                with ui.row().classes('items-center gap-1'):
                    ui.switch(
                        value=not is_disabled,
                        on_change=lambda e, n=name: self._toggle_plugin(n, e.value),
                    ).props('color=green')

                    ui.button(icon='info', on_click=lambda n=name, i=name, inf=info, dis=is_disabled: self._show_detail(n, inf, dis)).props('flat color=blue')

                    if info.error:
                        ui.button(icon='error', on_click=lambda e=info.error: ui.notify(
                            e, type='negative', multi_line=True, timeout=0
                        )).props('flat color=red')

                    ui.button(icon='download', on_click=lambda n=name: self._export_plugin(n)).props('flat color=orange')

                    ui.button(icon='delete', on_click=lambda n=name, d=meta.display_name: self._confirm_delete(n, d)).props('flat color=red')

    def _toggle_plugin(self, name, enabled):
        """切换插件启用状态"""
        plugin.set_plugin_disabled(name, not enabled)
        plugin.reload_plugins()
        ui.notify(
            I18N('plugins.enable') if enabled else I18N('plugins.disable'),
            type='positive'
        )
        ui.navigate.to('/plugins')

    def _show_detail(self, name, info, is_disabled):
        """显示插件详情弹窗"""
        meta = info.meta
        if is_disabled:
            status = I18N('plugins.status.disabled')
        elif info.loaded:
            status = I18N('plugins.status.loaded')
        elif info.error:
            status = I18N('plugins.status.error')
        else:
            status = I18N('plugins.status.uninit')

        with ui.dialog() as dialog, ui.card().classes('w-full max-w-lg'):
            ui.label(I18N('plugins.detail')).classes('text-h5')
            ui.separator()

            with ui.column().classes('w-full gap-2 mt-2'):
                with ui.row().classes('w-full'):
                    ui.label(I18N('plugins.detail.display_name') + ':').classes('text-bold w-32')
                    ui.label(meta.display_name)
                with ui.row().classes('w-full'):
                    ui.label(I18N('plugins.detail.name') + ':').classes('text-bold w-32')
                    ui.label(meta.name)
                with ui.row().classes('w-full'):
                    ui.label(I18N('plugins.detail.version') + ':').classes('text-bold w-32')
                    ui.label(meta.version)
                with ui.row().classes('w-full'):
                    ui.label(I18N('plugins.detail.author') + ':').classes('text-bold w-32')
                    ui.label(meta.author)
                with ui.row().classes('w-full'):
                    ui.label(I18N('plugins.detail.status') + ':').classes('text-bold w-32')
                    ui.label(status)
                if meta.desc:
                    with ui.row().classes('w-full'):
                        ui.label(I18N('plugins.detail.desc') + ':').classes('text-bold w-32')
                        ui.label(meta.desc)
                if meta.repo:
                    with ui.row().classes('w-full'):
                        ui.label(I18N('plugins.detail.repo') + ':').classes('text-bold w-32')
                        ui.label(meta.repo)
                with ui.row().classes('w-full'):
                    ui.label(I18N('plugins.detail.path') + ':').classes('text-bold w-32')
                    ui.label(info.dir).classes('text-caption')
                if info.error:
                    ui.separator()
                    ui.label(I18N('plugins.detail.error_info') + ':').classes('text-bold')
                    ui.label(info.error).classes('text-caption text-red')

            with ui.row().classes('w-full justify-end mt-4'):
                ui.button(I18N('plugins.cancel'), on_click=dialog.close).props('flat')
                ui.button(I18N('plugins.confirm'), on_click=dialog.close).props('color=primary')

        dialog.open()

    def _export_plugin(self, name):
        """导出插件"""
        zip_path = plugin.export_plugin(name)
        if zip_path:
            ui.download(zip_path, filename=f"{name}.zip")
            ui.notify(I18N('plugins.export.success'), type='positive')
            _schedule_temp_cleanup(os.path.dirname(zip_path))
        else:
            ui.notify(I18N('plugins.export.fail'), type='negative')

    def _confirm_delete(self, name, display_name):
        """确认删除弹窗"""
        with ui.dialog() as dialog, ui.card():
            ui.label(I18N('plugins.delete.confirm').format(display_name))
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button(I18N('plugins.cancel'), on_click=dialog.close).props('flat')
                ui.button(
                    I18N('plugins.confirm'),
                    on_click=lambda: self._do_delete(name, dialog),
                ).props('color=red')
        dialog.open()

    def _do_delete(self, name, dialog):
        """执行删除"""
        dialog.close()
        success, msg = plugin.delete_plugin(name)
        if success:
            ui.notify(I18N('plugins.delete.success'), type='positive')
            plugin.reload_plugins()
            ui.navigate.to('/plugins')
        else:
            ui.notify(I18N('plugins.delete.fail'), type='negative')

    async def _handle_import(self, e):
        """处理插件导入"""
        tmp_path = os.path.join(tempfile.gettempdir(), e.file.name)
        await e.file.save(tmp_path)
        success, msg = plugin.import_plugin(tmp_path)
        if success:
            ui.notify(I18N('plugins.import.success'), type='positive')
            plugin.reload_plugins()
            ui.navigate.to('/plugins')
        else:
            ui.notify(f"{I18N('plugins.import.fail')}: {msg}", type='negative')
