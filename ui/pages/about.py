from core import I18N
from core.config import Config
from ui import theme
from nicegui import ui

class AboutPage:
    """首页"""
    def __init__(self):
        self.ID = "about"
        self.columns = [
            {'name': 'name', 'label': '名称', 'field': 'name', 'align': 'left'},
            {'name': 'version', 'label': '版本', 'field': 'version', 'align': 'center'},
            {'name': 'link', 'label': '链接', 'field': 'link', 'align': 'left'},
        ]
        self.rows = [
            {'name': 'NiceGUI', 'version': '3.15.0', 'link': 'https://nicegui.io'},
            {'name': 'json5', 'version': '0.15.0', 'link': 'https://json5.org'},
            {'name': 'python-i18n', 'version': '0.3.9', 'link': 'https://github.com/danhper/python-i18n'},
            {'name': 'PyYAML', 'version': '6.0.1', 'link': 'https://pyyaml.org'},
        ]
    def show(self):
        with theme.frame(I18N('about.title')):
            global columns, rows
            ui.label(I18N('about.title')).classes('text-h4')
            ui.label(f"VERSION: {Config.APP_VERSION}").classes('text-h6')
            ui.markdown('''
            # MCT
            ## 介绍
            MCT（Minecraft Toolbox）是一个开源的 Minecraft 工具箱，旨在为 Minecraft 玩家提供一站式的工具和资源管理平台。通过 MCT，玩家可以轻松地管理游戏资源、配置文件以及其他相关工具，从而提升游戏体验。

            ## 开发成员

            ### 总监督 

            - @部鑫(BUXIN)
            ### 开发

            - @部鑫
            - @小皮鸭
            ### 美术

            - @部鑫
            ### 测试

            - @部鑫
            - @小皮鸭

            ## 致谢
            |作者|描述|链接|
            |---|---|---|
            |无|无|无|
            ''')
            ui.table(
                columns=self.columns,
                rows=self.rows,
                row_key='name',
                title='第三方库',
                pagination={'rowsPerPage': 10}
            ).classes('w-full')        