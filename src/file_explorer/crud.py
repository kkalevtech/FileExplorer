from pathlib import Path
from typing import Union

from file_explorer.exceptions import (
    FileAlreadyExistsError,
    FileExplorerError,
    PathNotFoundError,
)
from file_explorer.filesystem import FilesystemAbstraction
from file_explorer.path_utils import resolve_path, unique_path


def create_file(fs: FilesystemAbstraction, path: Path | str, overwrite: bool = False) -> Path:
    path = resolve_path(path)
    if not fs.exists(path.parent):
        raise PathNotFoundError(
            f"Parent directory does not exist: {path.parent}", path=path
        )
    if fs.exists(path):
        if not overwrite:
            raise FileAlreadyExistsError(
                f"File already exists: {path}", path=path
            )
        fs.delete_file(path)
    return fs.create_file(path)


def create_directory(fs: FilesystemAbstraction, path: Path | str, exist_ok: bool = False) -> Path:
    path = resolve_path(path)
    if fs.exists(path):
        if not exist_ok:
            raise FileAlreadyExistsError(
                f"Path already exists: {path}", path=path
            )
        if not fs.is_dir(path):
            raise FileExplorerError(
                f"Path exists and is not a directory: {path}", path=path
            )
        return path
    fs.create_dir(path)
    return path


def read_file_content(fs: FilesystemAbstraction, path: Path | str, mode: str = "text") -> Union[str, bytes]:
    path = resolve_path(path)
    if not fs.exists(path):
        raise PathNotFoundError(f"File not found: {path}", path=path)
    if not fs.is_file(path):
        raise FileExplorerError(f"Not a file: {path}", path=path)
    return fs.read_file(path, mode=mode)


def write_file_content(fs: FilesystemAbstraction, path: Path | str, content: Union[str, bytes]) -> Path:
    path = resolve_path(path)
    if not fs.exists(path.parent):
        raise PathNotFoundError(
            f"Parent directory does not exist: {path.parent}", path=path
        )
    if fs.exists(path) and fs.is_dir(path):
        raise FileExplorerError(f"Path is a directory: {path}", path=path)
    if fs.exists(path):
        fs.delete_file(path)
    return fs.write_file(path, content)


def rename_item(fs: FilesystemAbstraction, src: Path | str, dst: Path | str, overwrite: bool = False) -> Path:
    src = resolve_path(src)
    dst = resolve_path(dst)
    if not fs.exists(src):
        raise PathNotFoundError(f"Source not found: {src}", path=src)
    if fs.exists(dst):
        if not overwrite:
            raise FileAlreadyExistsError(
                f"Destination already exists: {dst}", path=dst
            )
        if fs.is_file(dst):
            fs.delete_file(dst)
        else:
            fs.delete_dir(dst, recursive=True)
    return fs.rename(src, dst)


def delete_item(fs: FilesystemAbstraction, path: Path | str, recursive: bool = False) -> None:
    path = resolve_path(path)
    if not fs.exists(path):
        raise PathNotFoundError(f"Path not found: {path}", path=path)
    if fs.is_file(path):
        fs.delete_file(path)
    elif fs.is_dir(path):
        if not recursive and fs.read_dir(path):
            raise FileExplorerError(
                f"Directory is not empty: {path}. Use recursive=True to delete.",
                path=path,
            )
        fs.delete_dir(path, recursive=recursive)


def duplicate_item(fs: FilesystemAbstraction, path: Path | str) -> Path:
    path = resolve_path(path)
    if not fs.exists(path):
        raise PathNotFoundError(f"Path not found: {path}", path=path)

    stem = path.stem
    suffix = path.suffix
    new_name = f"{stem} \u2014 Copy{suffix}"
    new_path = unique_path(path.parent, new_name)

    if fs.is_file(path):
        fs.copy_file(path, new_path)
    else:
        fs.copy_dir(path, new_path)
    return new_path
