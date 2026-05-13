import errno
import logging
import shutil
import stat as stat_module
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from file_explorer.exceptions import (
    DiskFullError,
    FileAlreadyExistsError,
    FileExplorerError,
    FileInUseError,
    InvalidPathError,
    PathNotFoundError,
    PermissionDeniedError,
)


def _translate_error(path: Path, os_error: OSError) -> FileExplorerError:
    if isinstance(os_error, FileNotFoundError):
        return PathNotFoundError(str(os_error), path=path, os_error=os_error)

    if isinstance(os_error, PermissionError):
        winerror = getattr(os_error, "winerror", None)
        if winerror == 32:
            return FileInUseError(str(os_error), path=path, os_error=os_error)
        return PermissionDeniedError(str(os_error), path=path, os_error=os_error)

    if isinstance(os_error, FileExistsError):
        return FileAlreadyExistsError(str(os_error), path=path, os_error=os_error)

    if os_error.errno == errno.ENOSPC:
        return DiskFullError(str(os_error), path=path, os_error=os_error)

    return FileExplorerError(str(os_error), path=path, os_error=os_error)


class FilesystemAbstraction(ABC):

    @abstractmethod
    def read_dir(self, path: Path) -> list[Path]:
        ...

    @abstractmethod
    def read_dir_recursive(self, path: Path) -> list[Path]:
        ...

    @abstractmethod
    def create_file(self, path: Path) -> Path:
        ...

    @abstractmethod
    def create_dir(self, path: Path) -> Path:
        ...

    @abstractmethod
    def delete_file(self, path: Path) -> None:
        ...

    @abstractmethod
    def delete_dir(self, path: Path, recursive: bool = False) -> None:
        ...

    @abstractmethod
    def rename(self, src: Path, dst: Path) -> Path:
        ...

    @abstractmethod
    def copy_file(self, src: Path, dst: Path) -> Path:
        ...

    @abstractmethod
    def copy_dir(self, src: Path, dst: Path, ignore_patterns: Optional[set[str]] = None) -> Path:
        ...

    @abstractmethod
    def move(self, src: Path, dst: Path) -> Path:
        ...

    @abstractmethod
    def get_metadata(self, path: Path) -> dict:
        ...

    @abstractmethod
    def exists(self, path: Path) -> bool:
        ...

    @abstractmethod
    def is_file(self, path: Path) -> bool:
        ...

    @abstractmethod
    def is_dir(self, path: Path) -> bool:
        ...

    @abstractmethod
    def get_permissions(self, path: Path) -> str:
        ...


class NativeFilesystem(FilesystemAbstraction):

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger("file_explorer.filesystem")

    def read_dir(self, path: Path) -> list[Path]:
        try:
            return sorted(path.iterdir())
        except OSError as e:
            raise _translate_error(path, e)

    def read_dir_recursive(self, path: Path) -> list[Path]:
        try:
            return sorted(path.rglob("*"))
        except OSError as e:
            raise _translate_error(path, e)

    def create_file(self, path: Path) -> Path:
        try:
            path.touch(exist_ok=False)
            return path
        except OSError as e:
            raise _translate_error(path, e)

    def create_dir(self, path: Path) -> Path:
        try:
            path.mkdir(parents=True, exist_ok=False)
            return path
        except OSError as e:
            raise _translate_error(path, e)

    def delete_file(self, path: Path) -> None:
        try:
            path.unlink()
        except OSError as e:
            raise _translate_error(path, e)

    def delete_dir(self, path: Path, recursive: bool = False) -> None:
        try:
            if recursive:
                shutil.rmtree(path)
            else:
                path.rmdir()
        except OSError as e:
            raise _translate_error(path, e)

    def rename(self, src: Path, dst: Path) -> Path:
        try:
            src.rename(dst)
            return dst
        except OSError as e:
            raise _translate_error(src, e)

    def copy_file(self, src: Path, dst: Path) -> Path:
        try:
            shutil.copy2(src, dst)
            return dst
        except OSError as e:
            raise _translate_error(src, e)

    def copy_dir(self, src: Path, dst: Path, ignore_patterns: Optional[set[str]] = None) -> Path:
        try:
            ignore_fn = shutil.ignore_patterns(*ignore_patterns) if ignore_patterns else None
            shutil.copytree(src, dst, ignore=ignore_fn)
            return dst
        except OSError as e:
            raise _translate_error(src, e)

    def move(self, src: Path, dst: Path) -> Path:
        try:
            shutil.move(str(src), str(dst))
            return Path(dst)
        except OSError as e:
            raise _translate_error(src, e)

    def get_metadata(self, path: Path) -> dict:
        try:
            stat_result = path.stat()
            return {
                "size": stat_result.st_size,
                "created": stat_result.st_ctime,
                "modified": stat_result.st_mtime,
                "accessed": stat_result.st_atime,
                "is_dir": stat_module.S_ISDIR(stat_result.st_mode),
                "is_file": stat_module.S_ISREG(stat_result.st_mode),
                "is_symlink": path.is_symlink(),
                "permissions": oct(stat_result.st_mode),
            }
        except OSError as e:
            raise _translate_error(path, e)

    def exists(self, path: Path) -> bool:
        try:
            return path.exists()
        except OSError:
            return False

    def is_file(self, path: Path) -> bool:
        try:
            return path.is_file()
        except OSError:
            return False

    def is_dir(self, path: Path) -> bool:
        try:
            return path.is_dir()
        except OSError:
            return False

    def get_permissions(self, path: Path) -> str:
        try:
            return oct(path.stat().st_mode)
        except OSError as e:
            raise _translate_error(path, e)
