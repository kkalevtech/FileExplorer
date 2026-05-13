import platform
import stat as stat_module
from dataclasses import dataclass
from pathlib import Path

from file_explorer.exceptions import FileExplorerError, PermissionDeniedError
from file_explorer.filesystem import FilesystemAbstraction


@dataclass
class FileMetadata:
    size: int
    created: float
    modified: float
    accessed: float
    extension: str
    is_dir: bool
    is_file: bool
    is_symlink: bool
    is_hidden: bool
    is_readonly: bool
    permissions: str


def get_metadata(fs: FilesystemAbstraction, path: Path | str) -> FileMetadata:
    path = Path(path).resolve()
    if not fs.exists(path):
        raise FileExplorerError(f"Path not found: {path}", path=path)

    try:
        raw = fs.get_metadata(path)
    except PermissionDeniedError:
        raise
    except FileExplorerError as e:
        raise FileExplorerError(f"Failed to get metadata for {path}", path=path) from e

    return FileMetadata(
        size=raw.get("size", 0),
        created=raw.get("created", 0.0),
        modified=raw.get("modified", 0.0),
        accessed=raw.get("accessed", 0.0),
        extension=_get_extension(path),
        is_dir=raw.get("is_dir", False),
        is_file=raw.get("is_file", False),
        is_symlink=raw.get("is_symlink", False),
        is_hidden=_is_hidden(path),
        is_readonly=_is_readonly(path),
        permissions=raw.get("permissions", ""),
    )


def get_size_formatted(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    elif size < 1024 ** 2:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 ** 3:
        return f"{size / 1024 ** 2:.1f} MB"
    else:
        return f"{size / 1024 ** 3:.1f} GB"


def _get_extension(path: Path) -> str:
    ext = path.suffix
    if ext:
        return ext[1:].lower()
    return ""


def _is_hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    if platform.system() == "Windows":
        try:
            attrs = path.stat().st_file_attributes
            return bool(attrs & 0x2)
        except OSError:
            return False
    return False


def _is_readonly(path: Path) -> bool:
    try:
        if platform.system() == "Windows":
            attrs = path.stat().st_file_attributes
            return bool(attrs & 0x1)
        mode = path.stat().st_mode
        return not bool(mode & stat_module.S_IWUSR)
    except OSError:
        return False
