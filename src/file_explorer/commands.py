from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from file_explorer.copy_move import (
    ConflictStrategy,
    OperationResult,
    copy_item,
    move_item,
)
from file_explorer.crud import (
    create_directory,
    create_file,
    delete_item,
    rename_item,
)
from file_explorer.exceptions import OperationCannotUndoError
from file_explorer.filesystem import FilesystemAbstraction


class Command(ABC):

    def __init__(self) -> None:
        self.description: str = ""
        self.timestamp: datetime = datetime.now()
        self._executed: bool = False

    @abstractmethod
    def execute(self) -> OperationResult:
        ...

    @abstractmethod
    def undo(self) -> OperationResult:
        ...


class _FileCommand(Command):

    def __init__(self, fs: FilesystemAbstraction, path: Path | str) -> None:
        super().__init__()
        self._fs = fs
        self._path = Path(path)


class CreateFileCommand(_FileCommand):

    def __init__(self, fs: FilesystemAbstraction, path: Path | str, overwrite: bool = False) -> None:
        super().__init__(fs, path)
        self._overwrite = overwrite
        self.description = f"Create file: {path}"

    def execute(self) -> OperationResult:
        try:
            create_file(self._fs, self._path, overwrite=self._overwrite)
            self._executed = True
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        except Exception as e:
            return OperationResult(
                source=self._path, destination=self._path, success=False,
                error=str(e),
            )

    def undo(self) -> OperationResult:
        if not self._executed:
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        if not self._fs.exists(self._path):
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        try:
            self._fs.delete_file(self._path)
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        except Exception as e:
            return OperationResult(
                source=self._path, destination=self._path, success=False,
                error=str(e),
            )


class CreateDirectoryCommand(_FileCommand):

    def __init__(self, fs: FilesystemAbstraction, path: Path | str, exist_ok: bool = False) -> None:
        super().__init__(fs, path)
        self._exist_ok = exist_ok
        self.description = f"Create directory: {path}"

    def execute(self) -> OperationResult:
        try:
            create_directory(self._fs, self._path, exist_ok=self._exist_ok)
            self._executed = True
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        except Exception as e:
            return OperationResult(
                source=self._path, destination=self._path, success=False,
                error=str(e),
            )

    def undo(self) -> OperationResult:
        if not self._executed:
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        if not self._fs.exists(self._path):
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        try:
            self._fs.delete_dir(self._path, recursive=True)
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        except Exception as e:
            return OperationResult(
                source=self._path, destination=self._path, success=False,
                error=str(e),
            )


class _DeleteCommand(_FileCommand):

    def execute(self) -> OperationResult:
        raise NotImplementedError

    def undo(self) -> OperationResult:
        raise OperationCannotUndoError(
            "Cannot undo a delete operation",
            path=self._path,
        )


class DeleteFileCommand(_DeleteCommand):

    def __init__(self, fs: FilesystemAbstraction, path: Path | str) -> None:
        super().__init__(fs, path)
        self.description = f"Delete file: {path}"

    def execute(self) -> OperationResult:
        try:
            delete_item(self._fs, self._path)
            self._executed = True
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        except Exception as e:
            return OperationResult(
                source=self._path, destination=self._path, success=False,
                error=str(e),
            )


class DeleteDirectoryCommand(_DeleteCommand):

    def __init__(self, fs: FilesystemAbstraction, path: Path | str, recursive: bool = False) -> None:
        super().__init__(fs, path)
        self._recursive = recursive
        self.description = f"Delete directory: {path}"

    def execute(self) -> OperationResult:
        try:
            delete_item(self._fs, self._path, recursive=self._recursive)
            self._executed = True
            return OperationResult(
                source=self._path, destination=self._path, success=True,
            )
        except Exception as e:
            return OperationResult(
                source=self._path, destination=self._path, success=False,
                error=str(e),
            )


class RenameCommand(_FileCommand):

    def __init__(self, fs: FilesystemAbstraction, src: Path | str, dst: Path | str, overwrite: bool = False) -> None:
        super().__init__(fs, src)
        self._dst = Path(dst)
        self._overwrite = overwrite
        self.description = f"Rename: {src} -> {dst}"

    def execute(self) -> OperationResult:
        try:
            rename_item(self._fs, self._path, self._dst, overwrite=self._overwrite)
            self._executed = True
            return OperationResult(
                source=self._path, destination=self._dst, success=True,
            )
        except Exception as e:
            return OperationResult(
                source=self._path, destination=self._dst, success=False,
                error=str(e),
            )

    def undo(self) -> OperationResult:
        if not self._executed:
            return OperationResult(
                source=self._dst, destination=self._path, success=True,
            )
        if not self._fs.exists(self._dst):
            return OperationResult(
                source=self._dst, destination=self._path, success=True,
                error="Source no longer exists for undo",
            )
        try:
            rename_item(self._fs, self._dst, self._path, overwrite=True)
            return OperationResult(
                source=self._dst, destination=self._path, success=True,
            )
        except Exception as e:
            return OperationResult(
                source=self._dst, destination=self._path, success=False,
                error=str(e),
            )


class CopyCommand(_FileCommand):

    def __init__(
        self,
        fs: FilesystemAbstraction,
        src: Path | str,
        dst: Path | str,
        strategy: ConflictStrategy = ConflictStrategy.OVERWRITE,
    ) -> None:
        super().__init__(fs, src)
        self._dst = Path(dst)
        self._strategy = strategy
        self._effective_dst: Optional[Path] = None
        self.description = f"Copy: {src} -> {dst}"

    def execute(self) -> OperationResult:
        result = copy_item(self._fs, self._path, self._dst, strategy=self._strategy)
        if result.success:
            self._executed = True
            self._effective_dst = result.destination
        return result

    def undo(self) -> OperationResult:
        if not self._executed or self._effective_dst is None:
            return OperationResult(
                source=self._dst, destination=self._path, success=True,
            )
        if not self._fs.exists(self._effective_dst):
            return OperationResult(
                source=self._effective_dst, destination=self._path, success=True,
            )
        try:
            if self._fs.is_file(self._effective_dst):
                self._fs.delete_file(self._effective_dst)
            else:
                self._fs.delete_dir(self._effective_dst, recursive=True)
            return OperationResult(
                source=self._effective_dst, destination=self._path, success=True,
            )
        except Exception as e:
            return OperationResult(
                source=self._effective_dst, destination=self._path, success=False,
                error=str(e),
            )


class MoveCommand(_FileCommand):

    def __init__(
        self,
        fs: FilesystemAbstraction,
        src: Path | str,
        dst: Path | str,
        strategy: ConflictStrategy = ConflictStrategy.OVERWRITE,
    ) -> None:
        super().__init__(fs, src)
        self._dst = Path(dst)
        self._strategy = strategy
        self._effective_dst: Optional[Path] = None
        self.description = f"Move: {src} -> {dst}"

    def execute(self) -> OperationResult:
        result = move_item(self._fs, self._path, self._dst, strategy=self._strategy)
        if result.success:
            self._executed = True
            self._effective_dst = result.destination
        return result

    def undo(self) -> OperationResult:
        if not self._executed or self._effective_dst is None:
            return OperationResult(
                source=self._dst, destination=self._path, success=True,
            )
        if not self._fs.exists(self._effective_dst):
            return OperationResult(
                source=self._effective_dst, destination=self._path, success=True,
            )
        try:
            result = move_item(
                self._fs,
                self._effective_dst,
                self._path,
                strategy=ConflictStrategy.OVERWRITE,
            )
            return result
        except Exception as e:
            return OperationResult(
                source=self._effective_dst, destination=self._path, success=False,
                error=str(e),
            )


class BatchCommand(Command):

    def __init__(self, commands: list[Command]) -> None:
        super().__init__()
        self._commands = commands
        self.description = f"Batch of {len(commands)} commands"
        self._results: list[OperationResult] = []

    def execute(self) -> OperationResult:
        self._results = []
        successes = 0
        for cmd in self._commands:
            result = cmd.execute()
            self._results.append(result)
            if result.success:
                successes += 1

        self._executed = True
        return OperationResult(
            source=Path(""), destination=Path(""), success=True,
            error=f"{successes}/{len(self._commands)} succeeded",
        )

    def undo(self) -> OperationResult:
        if not self._executed:
            return OperationResult(
                source=Path(""), destination=Path(""), success=True,
            )
        successes = 0
        for cmd in reversed(self._commands):
            try:
                result = cmd.undo()
                if result.success:
                    successes += 1
            except OperationCannotUndoError:
                continue
            except Exception:
                continue

        return OperationResult(
            source=Path(""), destination=Path(""), success=True,
            error=f"{successes}/{len(self._commands)} undid",
        )


class OperationHistory:

    def __init__(self, limit: int = 50) -> None:
        self._limit = limit
        self._history: list[Command] = []
        self._redo_stack: list[Command] = []

    @property
    def can_undo(self) -> bool:
        return len(self._history) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def limit(self) -> int:
        return self._limit

    @limit.setter
    def limit(self, value: int) -> None:
        self._limit = value
        while len(self._history) > self._limit:
            self._history.pop(0)

    def push(self, command: Command) -> None:
        self._history.append(command)
        self._redo_stack.clear()
        while len(self._history) > self._limit:
            self._history.pop(0)

    def undo(self) -> Optional[OperationResult]:
        if not self._history:
            return None
        cmd = self._history.pop()
        self._redo_stack.append(cmd)
        return cmd.undo()

    def redo(self) -> Optional[OperationResult]:
        if not self._redo_stack:
            return None
        cmd = self._redo_stack.pop()
        result = cmd.execute()
        self._history.append(cmd)
        return result

    def clear(self) -> None:
        self._history.clear()
        self._redo_stack.clear()
