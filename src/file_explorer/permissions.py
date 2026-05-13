import os
import platform
import sys
from pathlib import Path
from typing import Optional

from file_explorer.exceptions import (
    DiskFullError,
    FileAlreadyExistsError,
    FileExplorerError,
    FileInUseError,
    PathNotFoundError,
    PermissionDeniedError,
)


_PROTECTED_PATHS: dict[str, list[str]] = {
    "Windows": [
        str(Path(os.environ.get("SystemRoot", "C:\\Windows"))),
        str(Path(os.environ.get("ProgramFiles", "C:\\Program Files"))),
        str(Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"))),
        "C:\\System Volume Information",
        "C:\\$Recycle.Bin",
        "C:\\Config.Msi",
    ],
    "Linux": [
        "/proc",
        "/sys",
        "/dev",
        "/boot",
        "/etc",
        "/lost+found",
    ],
    "Darwin": [
        "/System",
        "/Library",
        "/Applications",
        "/Volumes",
    ],
}


class PermissionManager:

    @staticmethod
    def check_readable(path: Path | str) -> bool:
        return os.access(str(path), os.R_OK)

    @staticmethod
    def check_writable(path: Path | str) -> bool:
        return os.access(str(path), os.W_OK)

    @staticmethod
    def check_executable(path: Path | str) -> bool:
        return os.access(str(path), os.X_OK)

    @staticmethod
    def is_system_protected(path: Path | str) -> bool:
        resolved = str(Path(path).resolve()).lower()
        system = platform.system()
        protected = _PROTECTED_PATHS.get(system, [])
        for protected_path in protected:
            if resolved.startswith(protected_path.lower()):
                return True
        return False

    @staticmethod
    def get_accessible_descendants(root: Path | str) -> list[Path]:
        root_path = Path(root).resolve()
        accessible: list[Path] = []

        if not root_path.is_dir():
            return accessible

        try:
            for entry in root_path.rglob("*"):
                try:
                    if entry.exists():
                        accessible.append(entry)
                except PermissionError:
                    continue
        except PermissionError:
            pass

        return sorted(accessible)


def is_retryable(error: FileExplorerError) -> bool:
    return isinstance(error, (FileInUseError, DiskFullError))


def user_friendly_message(error: FileExplorerError) -> str:
    if isinstance(error, PathNotFoundError):
        return f"The file or folder '{error.path}' could not be found. It may have been moved, renamed, or deleted."
    if isinstance(error, PermissionDeniedError):
        return f"You don't have permission to access '{error.path}'. Try running as administrator or checking folder permissions."
    if isinstance(error, FileInUseError):
        return f"The file '{error.path}' is currently in use by another program. Close the program and try again."
    if isinstance(error, DiskFullError):
        return "There is not enough free disk space to complete this operation. Free up space and try again."
    if isinstance(error, FileAlreadyExistsError):
        name = error.path.name if error.path else ""
        return f"A file or folder named '{name}' already exists in this location."
    return f"An error occurred: {error}"
