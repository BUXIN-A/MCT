# 此模块由 Trea 编写
"""
日志模块 —— 按启动时间 + 序号创建日志文件

功能:
    - 自动创建日志文件夹 e:\Python\MCT\logs
    - 文件名格式：YYYYMMDD-HHMM-N.log（N 是分钟内的序号）
    - 文件日志 + 控制台日志同时输出
    - 统一接口：logger.debug/info/warning/error
"""

import glob
import logging
import os
from datetime import datetime
from typing import Literal

# ── 路径配置 ──────────────────────────────────────────────
_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
_LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "DEBUG"

# ── 格式化模板 ─────────────────────────────────────────────
_FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
# ── 临时配置 ────────────────────────────────────────────────
save_log = False

def _ensure_log_dir() -> None:
    """确保日志文件夹存在"""
    os.makedirs(_LOG_DIR, exist_ok=True)


def _resolve_log_file() -> str:
    """
    生成日志文件名，格式：YYYYMMDD-HHMM-N.log

    - 同一分钟内启动多次，序号 N 自动递增
    - 跨分钟启动自动生成新文件
    """
    _ensure_log_dir()
    now = datetime.now()
    base = now.strftime("%Y%m%d-%H%M")
    pattern = os.path.join(_LOG_DIR, f"{base}-*.log")
    existing = glob.glob(pattern)
    seq = len(existing) + 1
    return os.path.join(_LOG_DIR, f"{base}-{seq}.log")


def _build_file_handler() -> logging.FileHandler:
    """文件日志处理器：每个 session 一个文件"""
    handler = logging.FileHandler(_resolve_log_file(), encoding="utf-8")
    handler.setLevel(getattr(logging, _LOG_LEVEL))
    handler.setFormatter(logging.Formatter(_FILE_FORMAT, _DATE_FORMAT))
    return handler


def _build_console_handler() -> logging.StreamHandler:
    """控制台日志处理器"""
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, _LOG_LEVEL))
    handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT, _DATE_FORMAT))
    return handler


def get_logger(name: str = "MCT") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    if save_log:
        logger.setLevel(getattr(logging, _LOG_LEVEL))
        logger.addHandler(_build_file_handler())
    logger.addHandler(_build_console_handler())
    logger.propagate = False

    return logger


# ── 快捷常量 ───────────────────────────────────────────────
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR

# ── 模块级默认 logger ──────────────────────────────────────
logger = get_logger("MCT")
