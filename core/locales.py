import i18n
from pathlib import Path
from core.config import Function, Config

_is_initialized = False

def init_locales():
    global _is_initialized
    if not _is_initialized:
        i18n.set('enable_memoization', True)
        i18n.set('filename_format', '{locale}.{format}')
        i18n.set('file_format', 'json')
        i18n.load_path.append(Path(Config.LOCALES_DIR))
        _is_initialized = True

def I18N(key: str) -> str:
    i18n.set('locale', Function().get_config_value("locale"))
    return i18n.t(key)