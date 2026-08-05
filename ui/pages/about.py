from core import I18N

from ui import theme
from nicegui import ui

class HomePage:
    """首页"""
    def __init__(self):
        self.ID = "about"
    def show(self):
        with theme.frame(I18N('about.title')):
            ui.label(I18N('about.title')).classes('text-h4')
            # 如果是开发者名单，不必要多语言
            ui.markdown('''
            # MCT
            ## 介绍
            MCT（Minecraft Toolbox）是一个开源的 Minecraft 工具箱，旨在为 Minecraft 玩家提供一站式的工具和资源管理平台。通过 MCT，玩家可以轻松地管理游戏资源、配置文件以及其他相关工具，从而提升游戏体验。

            ## 开发成员

            ### 总监督 

            - @部鑫(BUXIN)
            ### 开发

            - @部鑫(BUXIN)
            - @小皮鸭
            ### 美术

            - @部鑫(BUXIN)
            ### 测试

            - @zys
            - @Fallen Leaves
            ''')