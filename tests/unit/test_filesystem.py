from pathlib import Path

import pytest

from file_explorer.exceptions import (
    FileAlreadyExistsError,
    FileExplorerError,
    PathNotFoundError,
)
from file_explorer.filesystem import NativeFilesystem


@pytest.fixture
def fs():
    return NativeFilesystem()


class TestReadDir:
    def test_read_dir_returns_paths(self, tmp_path: Path, fs: NativeFilesystem):
        (tmp_path / "a.txt").touch()
        (tmp_path / "b.txt").touch()
        entries = fs.read_dir(tmp_path)
        assert len(entries) == 2
        assert all(isinstance(e, Path) for e in entries)

    def test_read_dir_nonexistent_raises(self, fs: NativeFilesystem):
        with pytest.raises(PathNotFoundError):
            fs.read_dir(Path("/nonexistent_path_xyz"))

    def test_read_dir_sorted(self, tmp_path: Path, fs: NativeFilesystem):
        (tmp_path / "z.txt").touch()
        (tmp_path / "a.txt").touch()
        entries = fs.read_dir(tmp_path)
        assert entries[0].name == "a.txt"
        assert entries[1].name == "z.txt"


class TestCreateFile:
    def test_create_file_creates_file(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "new.txt"
        result = fs.create_file(target)
        assert result == target
        assert target.exists()
        assert target.is_file()

    def test_create_file_existing_raises(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "existing.txt"
        target.touch()
        with pytest.raises(FileAlreadyExistsError):
            fs.create_file(target)


class TestCreateDir:
    def test_create_dir_creates_directory(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "subdir"
        result = fs.create_dir(target)
        assert result == target
        assert target.exists()
        assert target.is_dir()

    def test_create_dir_existing_raises(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "subdir"
        target.mkdir()
        with pytest.raises(FileAlreadyExistsError):
            fs.create_dir(target)

    def test_create_dir_creates_parents(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "a" / "b" / "c"
        result = fs.create_dir(target)
        assert result == target
        assert target.exists()


class TestDeleteFile:
    def test_delete_file_removes_file(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "to_delete.txt"
        target.touch()
        fs.delete_file(target)
        assert not target.exists()

    def test_delete_file_nonexistent_raises(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "ghost.txt"
        with pytest.raises(PathNotFoundError):
            fs.delete_file(target)


class TestDeleteDir:
    def test_delete_dir_empty(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "empty_dir"
        target.mkdir()
        fs.delete_dir(target)
        assert not target.exists()

    def test_delete_dir_recursive(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "parent"
        (target / "child").mkdir(parents=True)
        (target / "child" / "file.txt").touch()
        fs.delete_dir(target, recursive=True)
        assert not target.exists()

    def test_delete_dir_nonempty_no_recursive_raises(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "parent"
        (target / "child").mkdir(parents=True)
        with pytest.raises(FileExplorerError):
            fs.delete_dir(target)


class TestRename:
    def test_rename_updates_path(self, tmp_path: Path, fs: NativeFilesystem):
        src = tmp_path / "old.txt"
        dst = tmp_path / "new.txt"
        src.touch()
        result = fs.rename(src, dst)
        assert result == dst
        assert dst.exists()
        assert not src.exists()

    def test_rename_nonexistent_raises(self, tmp_path: Path, fs: NativeFilesystem):
        src = tmp_path / "ghost.txt"
        dst = tmp_path / "also_ghost.txt"
        with pytest.raises(PathNotFoundError):
            fs.rename(src, dst)


class TestCopyFile:
    def test_copy_file(self, tmp_path: Path, fs: NativeFilesystem):
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("hello")
        result = fs.copy_file(src, dst)
        assert result == dst
        assert dst.exists()
        assert dst.read_text() == "hello"

    def test_copy_file_nonexistent_src_raises(self, tmp_path: Path, fs: NativeFilesystem):
        src = tmp_path / "ghost.txt"
        dst = tmp_path / "dest.txt"
        with pytest.raises(PathNotFoundError):
            fs.copy_file(src, dst)


class TestCopyDir:
    def test_copy_dir(self, tmp_path: Path, fs: NativeFilesystem):
        src = tmp_path / "src_dir"
        dst = tmp_path / "dst_dir"
        src.mkdir()
        (src / "file.txt").touch()
        result = fs.copy_dir(src, dst)
        assert result == dst
        assert dst.exists()
        assert (dst / "file.txt").exists()


class TestMove:
    def test_move_file(self, tmp_path: Path, fs: NativeFilesystem):
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("hello")
        result = fs.move(src, dst)
        assert result == dst
        assert dst.exists()
        assert dst.read_text() == "hello"
        assert not src.exists()


class TestGetMetadata:
    def test_get_metadata_returns_dict(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "data.txt"
        target.write_text("content")
        meta = fs.get_metadata(target)
        assert isinstance(meta, dict)
        assert meta["size"] == 7
        assert meta["is_file"] is True
        assert meta["is_dir"] is False

    def test_get_metadata_nonexistent_raises(self, tmp_path: Path, fs: NativeFilesystem):
        with pytest.raises(PathNotFoundError):
            fs.get_metadata(tmp_path / "ghost.txt")


class TestExists:
    def test_exists_true(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "exists.txt"
        target.touch()
        assert fs.exists(target) is True

    def test_exists_false(self, tmp_path: Path, fs: NativeFilesystem):
        assert fs.exists(tmp_path / "ghost.txt") is False


class TestIsFileIsDir:
    def test_is_file(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "file.txt"
        target.touch()
        assert fs.is_file(target) is True
        assert fs.is_dir(target) is False

    def test_is_dir(self, tmp_path: Path, fs: NativeFilesystem):
        assert fs.is_dir(tmp_path) is True
        assert fs.is_file(tmp_path) is False

    def test_is_file_nonexistent(self, tmp_path: Path, fs: NativeFilesystem):
        assert fs.is_file(tmp_path / "ghost.txt") is False


class TestGetPermissions:
    def test_get_permissions_returns_octal(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "perm.txt"
        target.touch()
        perms = fs.get_permissions(target)
        assert perms.startswith("0o")
