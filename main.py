"""Minecraft Toolbox —— 入口"""
from core.logging import logger
from ui.app import App
from core.locales import I18N, init_locales
import os, sys

logger.info(r'''
  __  __ _                            __ _     _______          _ _               
 |  \/  (_)                          / _| |   |__   __|        | | |              
 | \  / |_ _ __   ___  ___ _ __ __ _| |_| |_     | | ___   ___ | | |__   _____  __
 | |\/| | | '_ \ / _ \/ __| '__/ _` |  _| __|    | |/ _ \ / _ \| | '_ \ / _ \ \/ /
 | |  | | | | | |  __/ (__| | | (_| | | | |_     | | (_) | (_) | | |_) | (_) >  < 
 |_|  |_|_|_| |_|\___|\___|_|  \__,_|_|  \__|    |_|\___/ \___/|_|_.__/ \___/_/\_\
''')

def main():
    try:
        init_locales()
        logger.info(I18N("log.i18n"))

        app = App()
        app.run()
    except Exception as e:
        logger.exception("应用运行时发生错误: %s", e)

if __name__ in {"__main__", "__mp_main__"}:
    main()
