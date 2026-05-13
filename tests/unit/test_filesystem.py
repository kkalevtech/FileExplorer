from pathlib import Path

import pytest

from file_explorer.exceptions import (
    DiskFullError,
    FileAlreadyExistsError,
    FileExplorerError,
    FileInUseError,
    PathNotFoundError,
    PermissionDeniedError,
)
from file_explorer.filesystem import NativeFilesystem
from tests.conftest import MockFilesystem


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


class TestMockFilesystem:

    @pytest.fixture
    def mfs(self):
        return MockFilesystem()

    def test_create_file_and_exists(self, mfs: MockFilesystem):
        p = Path("/test/file.txt")
        result = mfs.create_file(p)
        assert result == p.absolute()
        assert mfs.exists(p) is True
        assert mfs.is_file(p) is True

    def test_create_dir(self, mfs: MockFilesystem):
        p = Path("/test/mydir")
        result = mfs.create_dir(p)
        assert result == p.absolute()
        assert mfs.exists(p) is True
        assert mfs.is_dir(p) is True

    def test_create_file_existing_raises(self, mfs: MockFilesystem):
        p = Path("/test/file.txt")
        mfs.create_file(p)
        with pytest.raises(FileAlreadyExistsError):
            mfs.create_file(p)

    def test_read_dir(self, mfs: MockFilesystem):
        mfs.create_file(Path("/root/a.txt"))
        mfs.create_file(Path("/root/b.txt"))
        entries = mfs.read_dir(Path("/root"))
        assert len(entries) == 2

    def test_read_dir_nonexistent_raises(self, mfs: MockFilesystem):
        with pytest.raises(PathNotFoundError):
            mfs.read_dir(Path("/ghost"))

    def test_read_dir_recursive(self, mfs: MockFilesystem):
        mfs.create_file(Path("/a/b/c/d.txt"))
        all_entries = mfs.read_dir_recursive(Path("/a"))
        assert len(all_entries) == 3

    def test_delete_file(self, mfs: MockFilesystem):
        p = Path("/test/file.txt")
        mfs.create_file(p)
        mfs.delete_file(p)
        assert mfs.exists(p) is False

    def test_delete_dir_recursive(self, mfs: MockFilesystem):
        mfs.create_file(Path("/a/b/c/file.txt"))
        mfs.delete_dir(Path("/a"), recursive=True)
        assert mfs.exists(Path("/a")) is False

    def test_delete_dir_nonempty_no_recursive_raises(self, mfs: MockFilesystem):
        mfs.create_file(Path("/a/b/file.txt"))
        with pytest.raises(FileExplorerError):
            mfs.delete_dir(Path("/a"))

    def test_rename(self, mfs: MockFilesystem):
        mfs.create_file(Path("/old.txt"))
        result = mfs.rename(Path("/old.txt"), Path("/new.txt"))
        assert result == Path("/new.txt").absolute()
        assert mfs.exists(Path("/old.txt")) is False
        assert mfs.exists(Path("/new.txt")) is True

    def test_copy_file(self, mfs: MockFilesystem):
        mfs.create_file(Path("/src.txt"))
        result = mfs.copy_file(Path("/src.txt"), Path("/dst.txt"))
        assert mfs.exists(Path("/dst.txt")) is True

    def test_copy_dir(self, mfs: MockFilesystem):
        mfs.create_file(Path("/src/a/b.txt"))
        mfs.copy_dir(Path("/src"), Path("/dst"))
        assert mfs.exists(Path("/dst/a/b.txt")) is True

    def test_move_file(self, mfs: MockFilesystem):
        mfs.create_file(Path("/src.txt"))
        mfs.move(Path("/src.txt"), Path("/dst.txt"))
        assert mfs.exists(Path("/src.txt")) is False
        assert mfs.exists(Path("/dst.txt")) is True

    def test_move_dir(self, mfs: MockFilesystem):
        mfs.create_file(Path("/src/a/b.txt"))
        mfs.move(Path("/src"), Path("/dst"))
        assert mfs.exists(Path("/src")) is False
        assert mfs.exists(Path("/dst/a/b.txt")) is True

    def test_get_metadata(self, mfs: MockFilesystem):
        mfs.create_file(Path("/f.txt"))
        meta = mfs.get_metadata(Path("/f.txt"))
        assert meta["is_file"] is True
        assert meta["is_dir"] is False

    def test_get_metadata_nonexistent_raises(self, mfs: MockFilesystem):
        with pytest.raises(PathNotFoundError):
            mfs.get_metadata(Path("/ghost.txt"))

    def test_permission_denied(self, mfs: MockFilesystem):
        p = Path("/restricted/file.txt")
        mfs.create_file(p)
        mfs.set_restricted(p)
        with pytest.raises(PermissionDeniedError):
            mfs.read_dir(p)

    def test_file_in_use(self, mfs: MockFilesystem):
        p = Path("/locked/file.txt")
        mfs.create_file(p)
        mfs.set_locked(p)
        with pytest.raises(FileInUseError):
            mfs.read_dir(p)

    def test_disk_full(self, mfs: MockFilesystem):
        mfs.set_capacity(0)
        with pytest.raises(DiskFullError):
            mfs.create_file(Path("/new.txt"))

    def test_mock_fs_fixture(self, mock_fs: MockFilesystem):
        assert mock_fs.exists(Path("/dir1")) is True
        assert mock_fs.exists(Path("/file_a.txt")) is True
        assert mock_fs.exists(Path("/.hidden_file")) is True
        assert mock_fs.is_dir(Path("/dir1")) is True
        assert mock_fs.is_file(Path("/file_a.txt")) is True
