from pathlib import Path
from typing import Optional

from file_explorer.exceptions import FileExplorerError, PathNotFoundError
from file_explorer.filesystem import FilesystemAbstraction
from file_explorer.path_utils import resolve_path

_MAX_HISTORY = 100


class DirectoryNavigator:

    def __init__(self, fs: FilesystemAbstraction, start_dir: Path | str) -> None:
        self._fs = fs
        self._current = resolve_path(start_dir)
        self._history: list[Path] = []
        self._future: list[Path] = []

        if not self._fs.exists(self._current):
            raise PathNotFoundError(
                f"Start directory does not exist: {self._current}",
                path=self._current,
            )

    @property
    def current(self) -> Path:
        return self._current

    def list_contents(self, show_hidden: bool = False) -> list[Path]:
        entries = self._fs.read_dir(self._current)
        if not show_hidden:
            entries = [e for e in entries if not e.name.startswith(".")]
        return entries

    def enter(self, name: str | Path) -> Path:
        target = (self._current / name).resolve()
        if not self._fs.exists(target):
            raise PathNotFoundError(
                f"Path does not exist: {target}", path=target
            )
        if not self._fs.is_dir(target):
            raise FileExplorerError(
                f"Not a directory: {target}", path=target
            )
        self._history.append(self._current)
        if len(self._history) > _MAX_HISTORY:
            self._history.pop(0)
        self._future.clear()
        self._current = target
        return self._current

    def go_up(self) -> Path:
        parent = self._current.parent
        if self._current == parent:
            return self._current
        self._history.append(self._current)
        if len(self._history) > _MAX_HISTORY:
            self._history.pop(0)
        self._future.clear()
        self._current = parent
        return self._current

    def go_to(self, path: Path | str) -> Path:
        target = resolve_path(path)
        if not self._fs.exists(target):
            raise PathNotFoundError(
                f"Path does not exist: {target}", path=target
            )
        if self._current != target:
            self._history.append(self._current)
            if len(self._history) > _MAX_HISTORY:
                self._history.pop(0)
            self._future.clear()
        self._current = target
        return self._current

    def refresh(self) -> list[Path]:
        return self.list_contents()

    def get_history(self) -> list[Path]:
        return list(self._history)

    def go_back(self) -> Optional[Path]:
        if not self._history:
            return None
        self._future.append(self._current)
        self._current = self._history.pop()
        return self._current

    def go_forward(self) -> Optional[Path]:
        if not self._future:
            return None
        self._history.append(self._current)
        self._current = self._future.pop()
        return self._current

    @property
    def root(self) -> Path:
        return Path(self._current.anchor)
