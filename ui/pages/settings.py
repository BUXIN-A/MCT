from core import logger
from core import I18N
from core import config

from ui import theme
from nicegui import ui

# 语言切换函数
def get_language() -> str:
    language = config.Function().get_config_value('locale')
    if language == 'zh_cn':
        return '中文'
    elif language == 'en_us':
        return 'English'
    else:
        return '中文'
def set_language(language: str) -> None:
    if language.value == '中文':
        language = 'zh_cn'
    elif language.value == 'English':
        language = 'en_us'
    config.Function().set_config_value('locale', language)
    logger.info(f'切换到语言: {language}')
    ui.navigate.reload()

class SettingPage:
    """设置页面"""
    def __init__(self):
        self.ID = "setting"
    def show(self):
        with theme.frame(I18N('setting.title')):
            ui.label(I18N('setting.system.title')).classes('text-h4')
            Language_Select = ui.select(label=I18N('setting.language'),  options=['中文', 'English'], value=get_language(), on_change=set_language).style('width: calc(100% - 40px); margin-left: 20px; margin-right: 20px;')

            ui.label(I18N('setting.theme.title')).classes('text-h4')
            ...