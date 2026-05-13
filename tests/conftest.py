from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pytest

from file_explorer.exceptions import (
    DiskFullError,
    FileAlreadyExistsError,
    FileExplorerError,
    FileInUseError,
    PathNotFoundError,
    PermissionDeniedError,
)
from file_explorer.filesystem import FilesystemAbstraction


@dataclass
class MockEntry:
    name: str
    is_dir: bool = False
    content: str = ""
    metadata: Optional[dict] = None


class MockFilesystem(FilesystemAbstraction):

    def __init__(self) -> None:
        self._entries: dict[Path, MockEntry] = {}
        self._restricted: set[Path] = set()
        self._locked: set[Path] = set()
        self._capacity: Optional[int] = None

    def _norm(self, path: Path) -> Path:
        return path.absolute()

    def _resolve(self, path: Path) -> MockEntry:
        p = self._norm(path)
        if p not in self._entries:
            raise PathNotFoundError(f"Path not found: {p}", path=p)
        return self._entries[p]

    def _enforce_permissions(self, path: Path) -> None:
        p = self._norm(path)
        if p in self._restricted:
            raise PermissionDeniedError(f"Permission denied: {p}", path=p)
        if p in self._locked:
            raise FileInUseError(f"File in use: {p}", path=p)

    def _ensure_parents(self, path: Path) -> None:
        parent = path.parent
        if parent != path and self._norm(parent) not in self._entries:
            self._entries[self._norm(parent)] = MockEntry(
                name=parent.name, is_dir=True
            )
            self._ensure_parents(parent)

    def set_restricted(self, *paths: Path) -> None:
        for p in paths:
            self._restricted.add(self._norm(p))

    def set_locked(self, *paths: Path) -> None:
        for p in paths:
            self._locked.add(self._norm(p))

    def set_capacity(self, capacity: int) -> None:
        self._capacity = capacity

    def read_dir(self, path: Path) -> list[Path]:
        self._enforce_permissions(path)
        p = self._norm(path)
        if p not in self._entries:
            raise PathNotFoundError(f"Path not found: {p}", path=p)
        entry = self._entries[p]
        if not entry.is_dir:
            raise FileExplorerError(f"Not a directory: {p}", path=p)
        return sorted(
            child for child in self._entries
            if child.parent == p and child != p
        )

    def read_dir_recursive(self, path: Path) -> list[Path]:
        self._enforce_permissions(path)
        p = self._norm(path)
        if p not in self._entries:
            raise PathNotFoundError(f"Path not found: {p}", path=p)
        return sorted(
            child for child in self._entries
            if child != p and (p == child.parent or p in child.parents)
        )

    def create_file(self, path: Path) -> Path:
        p = self._norm(path)
        self._enforce_permissions(p)
        if p in self._entries:
            raise FileAlreadyExistsError(
                f"File already exists: {p}", path=p
            )
        if self._capacity is not None:
            total = sum(
                len(e.content) for e in self._entries.values() if not e.is_dir
            )
            if total >= self._capacity:
                raise DiskFullError("Disk full", path=p)
        self._ensure_parents(p)
        self._entries[p] = MockEntry(name=p.name, is_dir=False)
        return p

    def create_dir(self, path: Path) -> Path:
        p = self._norm(path)
        self._enforce_permissions(p)
        if p in self._entries:
            raise FileAlreadyExistsError(
                f"Directory already exists: {p}", path=p
            )
        self._ensure_parents(p)
        self._entries[p] = MockEntry(name=p.name, is_dir=True)
        return p

    def delete_file(self, path: Path) -> None:
        p = self._norm(path)
        self._enforce_permissions(p)
        entry = self._resolve(p)
        if entry.is_dir:
            raise FileExplorerError(f"Is a directory: {p}", path=p)
        del self._entries[p]

    def delete_dir(self, path: Path, recursive: bool = False) -> None:
        p = self._norm(path)
        self._enforce_permissions(p)
        self._resolve(p)
        children = [
            child for child in self._entries
            if child != p and (p == child.parent or p in child.parents)
        ]
        if children and not recursive:
            raise FileExplorerError(
                f"Directory not empty: {p}", path=p
            )
        for child in children:
            del self._entries[child]
        del self._entries[p]

    def rename(self, src: Path, dst: Path) -> Path:
        s = self._norm(src)
        d = self._norm(dst)
        self._enforce_permissions(s)
        self._enforce_permissions(d)
        entry = self._resolve(s)
        if d in self._entries:
            raise FileAlreadyExistsError(
                f"Destination already exists: {d}", path=d
            )
        del self._entries[s]
        self._ensure_parents(d)
        entry.name = d.name
        self._entries[d] = entry
        return d

    def copy_file(self, src: Path, dst: Path) -> Path:
        s = self._norm(src)
        d = self._norm(dst)
        self._enforce_permissions(s)
        entry = self._resolve(s)
        if entry.is_dir:
            raise FileExplorerError(f"Is a directory: {s}", path=s)
        self._ensure_parents(d)
        self._entries[d] = MockEntry(
            name=d.name, is_dir=False, content=entry.content
        )
        return d

    def copy_dir(self, src: Path, dst: Path, ignore_patterns: Optional[set[str]] = None) -> Path:
        s = self._norm(src)
        d = self._norm(dst)
        self._enforce_permissions(s)
        self._resolve(s)
        self._ensure_parents(d)
        self._entries[d] = MockEntry(name=d.name, is_dir=True)
        for child in sorted(self._entries):
            if child != s and (s == child.parent or s in child.parents):
                rel = child.relative_to(s)
                new_child = d / rel
                ce = self._entries[child]
                self._entries[self._norm(new_child)] = MockEntry(
                    name=new_child.name,
                    is_dir=ce.is_dir,
                    content=ce.content,
                )
                self._ensure_parents(self._norm(new_child))
        return d

    def move(self, src: Path, dst: Path) -> Path:
        s = self._norm(src)
        d = self._norm(dst)
        self._enforce_permissions(s)
        entry = self._resolve(s)
        if d in self._entries:
            raise FileAlreadyExistsError(
                f"Destination already exists: {d}", path=d
            )
        del self._entries[s]
        self._ensure_parents(d)
        entry.name = d.name
        self._entries[d] = entry
        if entry.is_dir:
            for child in sorted(self._entries):
                if child != s and (s == child.parent or s in child.parents):
                    rel = child.relative_to(s)
                    new_child = d / rel
                    ce = self._entries.pop(child)
                    ce.name = new_child.name
                    self._entries[self._norm(new_child)] = ce
        return d

    def get_metadata(self, path: Path) -> dict:
        p = self._norm(path)
        self._enforce_permissions(p)
        entry = self._resolve(p)
        if entry.metadata:
            return entry.metadata
        return {
            "size": len(entry.content),
            "created": 0.0,
            "modified": 0.0,
            "accessed": 0.0,
            "is_dir": entry.is_dir,
            "is_file": not entry.is_dir,
            "is_symlink": False,
            "permissions": "0o644",
        }

    def exists(self, path: Path) -> bool:
        return self._norm(path) in self._entries

    def is_file(self, path: Path) -> bool:
        p = self._norm(path)
        entry = self._entries.get(p)
        return entry is not None and not entry.is_dir

    def is_dir(self, path: Path) -> bool:
        p = self._norm(path)
        entry = self._entries.get(p)
        return entry is not None and entry.is_dir

    def read_file(self, path: Path, mode: str = "text") -> str | bytes:
        p = self._norm(path)
        self._enforce_permissions(p)
        entry = self._resolve(p)
        if entry.is_dir:
            raise FileExplorerError(f"Is a directory: {p}", path=p)
        if mode == "text":
            return entry.content
        return entry.content.encode("utf-8")

    def write_file(self, path: Path, content: str | bytes) -> Path:
        p = self._norm(path)
        self._enforce_permissions(p)
        entry = self._resolve(p)
        if entry.is_dir:
            raise FileExplorerError(f"Is a directory: {p}", path=p)
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        entry.content = content
        return p

    def get_permissions(self, path: Path) -> str:
        p = self._norm(path)
        self._enforce_permissions(p)
        self._resolve(p)
        return "0o644"


@pytest.fixture
def mock_fs() -> MockFilesystem:
    fs = MockFilesystem()
    root = Path("/").absolute()
    fs.create_dir(root / "dir1")
    fs.create_file(root / "dir1" / "file1.txt")
    fs.create_dir(root / "dir2")
    fs.create_dir(root / "dir2" / "subdir")
    fs.create_file(root / "dir2" / "subdir" / "file2.txt")
    fs.create_file(root / "file_a.txt")
    fs.create_file(root / "file_b.txt")
    fs.create_file(root / ".hidden_file")
    return fs
