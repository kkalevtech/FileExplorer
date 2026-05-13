import json
import logging
import os
import platform
import shutil
import tempfile
from dataclasses import dataclass, asdict, fields
from pathlib import Path
from typing import Any, Optional

from file_explorer.exceptions import FileExplorerError

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    start_directory: str = "~"
    show_hidden_files: bool = False
    default_conflict_strategy: str = "rename"
    max_history: int = 50
    max_search_results: int = 1000
    log_level: str = "INFO"
    language: str = "en"
    theme: str = "system"


KNOWN_KEYS = {f.name for f in fields(AppConfig)}


def default_config_path() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    return base / "file_explorer" / "config.json"


def load_config(path: Optional[Path] = None) -> AppConfig:
    path = path or default_config_path()
    if not path.exists():
        return AppConfig()
    try:
        with open(str(path), encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        backup = path.with_suffix(".json.corrupt")
        try:
            shutil.copy2(str(path), str(backup))
            logger.warning("Corrupted config backed up to %s", backup)
        except OSError:
            logger.warning("Could not back up corrupted config")
        return AppConfig()
    if not isinstance(data, dict):
        return AppConfig()
    valid = {k: v for k, v in data.items() if k in KNOWN_KEYS}
    return AppConfig(**valid)


def save_config(config: AppConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    try:
        with open(str(tmp), "w", encoding="utf-8") as f:
            json.dump(asdict(config), f, indent=2, ensure_ascii=False)
            f.write("\n")
        tmp.replace(path)
    except OSError as e:
        raise FileExplorerError(
            f"Failed to save config: {e}",
            path=path,
            os_error=e,
        )


class ConfigManager:

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._path = config_path or default_config_path()
        self._config = load_config(self._path)
        self._dirty: bool = False

    @property
    def path(self) -> Path:
        return self._path

    def get(self, key: str) -> Any:
        if key not in KNOWN_KEYS:
            raise KeyError(f"Unknown config key: {key}")
        return getattr(self._config, key)

    def set(self, key: str, value: Any) -> None:
        if key not in KNOWN_KEYS:
            raise KeyError(f"Unknown config key: {key}")
        setattr(self._config, key, value)
        self._dirty = True
        self._flush()

    def _flush(self) -> None:
        if self._dirty:
            save_config(self._config, self._path)
            self._dirty = False

    def reset_to_defaults(self) -> None:
        self._config = AppConfig()
        self._dirty = True
        self._flush()

    def reload(self) -> None:
        self._config = load_config(self._path)
        self._dirty = False
