from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from file_explorer.exceptions import (
    FileAlreadyExistsError,
    FileExplorerError,
    PathNotFoundError,
)
from file_explorer.filesystem import FilesystemAbstraction
from file_explorer.path_utils import resolve_path


class ConflictStrategy(Enum):
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"
    ASK = "ask"


@dataclass
class OperationResult:
    source: Path
    destination: Path
    success: bool
    error: Optional[str] = None


def _resolve_conflict(
    fs: FilesystemAbstraction,
    dst: Path,
    strategy: ConflictStrategy,
) -> Optional[Path]:
    if not fs.exists(dst):
        return dst

    if strategy == ConflictStrategy.SKIP:
        return None

    if strategy == ConflictStrategy.OVERWRITE:
        if fs.is_file(dst):
            fs.delete_file(dst)
        elif fs.is_dir(dst):
            fs.delete_dir(dst, recursive=True)
        return dst

    if strategy == ConflictStrategy.RENAME:
        counter = 1
        stem = dst.stem
        suffix = dst.suffix
        candidate = dst
        while fs.exists(candidate):
            candidate = dst.parent / f"{stem} ({counter}){suffix}"
            counter += 1
        return candidate

    if strategy == ConflictStrategy.ASK:
        raise FileAlreadyExistsError(
            f"Destination already exists: {dst}", path=dst
        )

    return dst


def _check_same_path(src: Path, dst: Path) -> bool:
    try:
        return src.resolve() == dst.resolve()
    except OSError:
        return src == dst


def copy_item(
    fs: FilesystemAbstraction,
    src: Path | str,
    dst: Path | str,
    strategy: ConflictStrategy = ConflictStrategy.OVERWRITE,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancellation_token: Optional[Callable[[], bool]] = None,
) -> OperationResult:
    src = resolve_path(src)
    dst = resolve_path(dst)

    if not fs.exists(src):
        return OperationResult(
            source=src, destination=dst, success=False,
            error=f"Source not found: {src}",
        )

    if _check_same_path(src, dst):
        return OperationResult(
            source=src, destination=dst, success=False,
            error=f"Source and destination are the same: {src}",
        )

    if fs.is_dir(dst) and fs.exists(dst):
        dst = dst / src.name

    if fs.is_dir(src) and fs.exists(dst) and fs.is_file(dst):
        return OperationResult(
            source=src, destination=dst, success=False,
            error=f"Cannot copy directory onto existing file: {dst}",
        )

    effective_dst = _resolve_conflict(fs, dst, strategy)
    if effective_dst is None:
        return OperationResult(
            source=src, destination=dst, success=True,
        )

    if cancellation_token and cancellation_token():
        return OperationResult(
            source=src, destination=effective_dst, success=False,
            error="Operation cancelled",
        )

    try:
        if progress_callback:
            progress_callback(0, 1)

        if fs.is_file(src):
            fs.copy_file(src, effective_dst)
        else:
            fs.copy_dir(src, effective_dst)

        if progress_callback:
            progress_callback(1, 1)

        return OperationResult(
            source=src, destination=effective_dst, success=True,
        )
    except FileExplorerError as e:
        return OperationResult(
            source=src, destination=effective_dst, success=False,
            error=str(e),
        )


def move_item(
    fs: FilesystemAbstraction,
    src: Path | str,
    dst: Path | str,
    strategy: ConflictStrategy = ConflictStrategy.OVERWRITE,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancellation_token: Optional[Callable[[], bool]] = None,
) -> OperationResult:
    src = resolve_path(src)
    dst = resolve_path(dst)

    if not fs.exists(src):
        return OperationResult(
            source=src, destination=dst, success=False,
            error=f"Source not found: {src}",
        )

    if _check_same_path(src, dst):
        return OperationResult(
            source=src, destination=dst, success=False,
            error=f"Source and destination are the same: {src}",
        )

    if fs.is_dir(dst) and fs.exists(dst):
        dst = dst / src.name

    if fs.is_dir(src) and fs.exists(dst) and fs.is_file(dst):
        return OperationResult(
            source=src, destination=dst, success=False,
            error=f"Cannot move directory onto existing file: {dst}",
        )

    effective_dst = _resolve_conflict(fs, dst, strategy)
    if effective_dst is None:
        return OperationResult(
            source=src, destination=dst, success=True,
        )

    if cancellation_token and cancellation_token():
        return OperationResult(
            source=src, destination=effective_dst, success=False,
            error="Operation cancelled",
        )

    try:
        if progress_callback:
            progress_callback(0, 1)

        fs.move(src, effective_dst)

        if progress_callback:
            progress_callback(1, 1)

        return OperationResult(
            source=src, destination=effective_dst, success=True,
        )
    except FileExplorerError as e:
        return OperationResult(
            source=src, destination=effective_dst, success=False,
            error=str(e),
        )


def batch_copy(
    fs: FilesystemAbstraction,
    items: list[tuple[Path | str, Path | str]],
    strategy: ConflictStrategy = ConflictStrategy.OVERWRITE,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancellation_token: Optional[Callable[[], bool]] = None,
) -> list[OperationResult]:
    results: list[OperationResult] = []
    total = len(items)

    for i, (src, dst) in enumerate(items):
        if cancellation_token and cancellation_token():
            break

        if progress_callback:
            progress_callback(i, total)

        result = copy_item(fs, src, dst, strategy=strategy)
        results.append(result)

    if progress_callback:
        progress_callback(len(results), total)

    return results


def batch_move(
    fs: FilesystemAbstraction,
    items: list[tuple[Path | str, Path | str]],
    strategy: ConflictStrategy = ConflictStrategy.OVERWRITE,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancellation_token: Optional[Callable[[], bool]] = None,
) -> list[OperationResult]:
    results: list[OperationResult] = []
    total = len(items)

    for i, (src, dst) in enumerate(items):
        if cancellation_token and cancellation_token():
            break

        if progress_callback:
            progress_callback(i, total)

        result = move_item(fs, src, dst, strategy=strategy)
        results.append(result)

    if progress_callback:
        progress_callback(len(results), total)

    return results
