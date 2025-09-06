import logging
import datetime
from typing import Any

class AnsiColors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """カスタムフォーマッター：ログレベルに応じて色を変更"""
    
    COLORS = {
        logging.DEBUG: AnsiColors.CYAN,
        logging.INFO: AnsiColors.GREEN,
        logging.WARNING: AnsiColors.YELLOW,
        logging.ERROR: AnsiColors.RED,
        logging.CRITICAL: AnsiColors.BOLD + AnsiColors.RED
    }
    
    def format(self, record):
        # 時刻フォーマット
        timestamp = datetime.datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        
        # レベル名の色付け
        level_color = self.COLORS.get(record.levelno, AnsiColors.RESET)
        level_name = record.levelname
        
        # メッセージの構築
        message = f"{AnsiColors.GRAY}[{timestamp}] {level_color}{level_name}{AnsiColors.RESET} {record.getMessage()}"
        
        # 例外情報があれば追加
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        
        return message

logger = None
def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """カラーフォーマットを適用したロガーを作成"""
    global logger
    logger = logging.getLogger(name)
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # コンソールハンドラーを作成
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter())
    
    logger.addHandler(console_handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger

# utils.pyスタイルの関数を提供
def now() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")

def println(*args: Any, **kw: Any) -> None:
    logger.info(' '.join(map(str, args)))

def error(*args: Any, **kw: Any) -> None:
    logger.error(' '.join(map(str, args)))

def warn(*args: Any, **kw: Any) -> None:
    logger.warning(' '.join(map(str, args)))

def critical(*args: Any, **kw: Any) -> None:
    logger.critical(' '.join(map(str, args)))

def debug(*args: Any, **kw: Any) -> None:
    logger.debug(' '.join(map(str, args)))

# 追加のログ関数
def info(*args: Any, **kw: Any) -> None:
    logger.info(' '.join(map(str, args)))

def exception(*args: Any, exc_info: bool = True, **kw: Any) -> None:
    """例外情報付きでエラーログを出力"""
    logger.error(' '.join(map(str, args)), exc_info=exc_info)

