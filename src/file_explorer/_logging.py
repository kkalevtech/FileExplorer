import logging
import sys
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "file_explorer.log"
_LOG_FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s:%(lineno)d \u2014 %(message)s"
_ROOT_LOGGER_NAME = "file_explorer"


def setup_logging(level: int = logging.INFO) -> None:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger(_ROOT_LOGGER_NAME)
    root.setLevel(level)

    if root.handlers:
        return

    formatter = logging.Formatter(_LOG_FORMAT)

    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
