from re import L

from core import logger
from core import I18N
from core import config

from ui import theme
from nicegui import ui
from typing import Dict

LANGUAGE_MAP: Dict[str, str] = {
    'zh_cn': '中文',
    'en_us': 'English'
}
LANGUAGE_MAP_REVERSE: Dict[str, str] = {v: k for k, v in LANGUAGE_MAP.items()}

# 语言设置函数
def get_language() -> str:
    language = config.Function().get_config_value('locale')
    return LANGUAGE_MAP.get(language, '中文')
def set_language(language: str) -> None:
    try:
        language = language.value
        config_value = LANGUAGE_MAP_REVERSE.get(language)
        config.Function().set_config_value('locale', config_value)
        logger.info(f'语言已切换为: {language} ({config_value})')
        ui.navigate.reload()
        
    except Exception as e:
        logger.error(f"设置语言失败: {str(e)}")
        raise

class SettingPage:
    """设置页面"""
    def __init__(self):
        self.ID = "settings"
    def show(self):
        with theme.frame(I18N('settings.title')):
            ui.label(I18N('settings.system.title')).classes('text-h4')
            Language_Select = ui.select(label=I18N('settings.language'),  options=['中文', 'English'], value=get_language(), on_change=set_language).style('width: calc(100% - 40px); margin-left: 20px; margin-right: 20px;')

            ui.label(I18N('settings.theme.title')).classes('text-h4')
            ...