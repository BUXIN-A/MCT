import i18n
from pathlib import Path
from core.config import Function, Config

_is_initialized = False
_cached_locale: str | None = None


def init_locales():
    global _is_initialized
    if not _is_initialized:
        i18n.set('enable_memoization', True)
        i18n.set('filename_format', '{locale}.{format}')
        i18n.set('file_format', 'json')
        i18n.load_path.append(Path(Config.LOCALES_DIR))
        _is_initialized = True


def _get_locale() -> str:
    global _cached_locale
    locale = Function().get_config_value("locale")
    if _cached_locale != locale:
        _cached_locale = locale
        i18n.set('locale', locale)
    return locale


def I18N(key: str) -> str:
    _get_locale()
    return i18n.t(key)


def i18n_key_exists(key: str) -> bool:
    """Check if an i18n translation key exists for the current locale."""
    _get_locale()
    try:
        result = i18n.t(key)
        return result != key
    except Exception:
        return False


def invalidate_locale_cache() -> None:
    global _cached_locale
    _cached_locale = None
