from pathlib import Path
from typing import Optional


class FileExplorerError(Exception):
    def __init__(
        self,
        message: str = "",
        path: Optional[Path] = None,
        os_error: Optional[OSError] = None,
    ) -> None:
        self.path = path
        self.os_error = os_error
        super().__init__(message)


class PathNotFoundError(FileExplorerError):
    ...


class PermissionDeniedError(FileExplorerError):
    ...


class FileAlreadyExistsError(FileExplorerError):
    ...


class DiskFullError(FileExplorerError):
    ...


class FileInUseError(FileExplorerError):
    ...


class InvalidPathError(FileExplorerError):
    ...


class OperationCancelledError(FileExplorerError):
    ...
