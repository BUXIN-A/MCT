"""全局配置"""
import json5
from typing import Final

@staticmethod
class Function:
    def get_config_value(self, key: str):
        with open(Config.CONFIG_DIR, "r", encoding="utf-8") as f:
            config = json5.load(f)
        for part in key.split('.'):
            if not isinstance(config, dict) or part not in config:
                raise KeyError(key)
            config = config[part]
        return config
    def set_config_value(self, key: str, value) -> None:
        with open(Config.CONFIG_DIR, "r", encoding="utf-8") as f:
            config = json5.load(f)
        parts = key.split('.')
        node = config
        for part in parts[:-1]:
            if not isinstance(node, dict):
                raise KeyError(key)
            if part not in node:
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value
        with open(Config.CONFIG_DIR, "w", encoding="utf-8") as f:
            json5.dump(config, f, ensure_ascii=False, indent=4, quote_keys=True)

class Config:
    """全局配置"""
    # ── 应用信息 ──
    APP_VERSION: Final = "0.0.3"

    # ── 窗口 ── #正式版启用
    WINDOW_SIZE: Final = (1200, 760)
    WINDOW_MIN_SIZE: Final = (960, 600)

    # ── 资源配置 ──
    LOCALES_DIR: Final = "assets/locales"
    CONFIG_DIR: Final = "data/config.json"
    WINDOW_ICON: Final = "assets/icons/mct.ico"
