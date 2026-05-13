import os
import platform
import stat
import sys
from pathlib import Path

import pytest

from file_explorer.exceptions import (
    FileAlreadyExistsError,
    FileExplorerError,
    FileInUseError,
    PathNotFoundError,
    PermissionDeniedError,
)
from file_explorer.filesystem import NativeFilesystem


@pytest.fixture
def fs():
    return NativeFilesystem()


@pytest.fixture
def dirs(tmp_path: Path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    dst.mkdir()
    return src, dst


class TestNativeFilesystemBasicOps:

    def test_create_file(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "new.txt"
        result = fs.create_file(target)
        assert result == target
        assert target.exists()
        assert target.is_file()

    def test_create_file_existing_raises(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "exists.txt"
        target.touch()
        with pytest.raises(FileAlreadyExistsError):
            fs.create_file(target)

    def test_create_dir(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "newdir"
        result = fs.create_dir(target)
        assert result == target
        assert target.exists()
        assert target.is_dir()

    def test_create_dir_existing_raises(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "exists"
        target.mkdir()
        with pytest.raises(FileAlreadyExistsError):
            fs.create_dir(target)

    def test_delete_file(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "delete_me.txt"
        target.touch()
        fs.delete_file(target)
        assert not target.exists()

    def test_delete_file_nonexistent_raises(self, fs: NativeFilesystem, tmp_path: Path):
        with pytest.raises(PathNotFoundError):
            fs.delete_file(tmp_path / "nope.txt")

    def test_delete_dir_empty(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "empty_dir"
        target.mkdir()
        fs.delete_dir(target)
        assert not target.exists()

    def test_delete_dir_recursive(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "parent"
        sub = target / "child" / "grandchild"
        sub.mkdir(parents=True)
        fs.delete_dir(target, recursive=True)
        assert not target.exists()

    def test_rename_file(self, fs: NativeFilesystem, tmp_path: Path):
        src = tmp_path / "old.txt"
        dst = tmp_path / "new.txt"
        src.touch()
        result = fs.rename(src, dst)
        assert result == dst
        assert not src.exists()
        assert dst.exists()

    def test_rename_dir(self, fs: NativeFilesystem, tmp_path: Path):
        src = tmp_path / "olddir"
        dst = tmp_path / "newdir"
        src.mkdir()
        fs.rename(src, dst)
        assert not src.exists()
        assert dst.is_dir()

    def test_copy_file(self, fs: NativeFilesystem, tmp_path: Path):
        src = tmp_path / "src.txt"
        dst = tmp_path / "dst.txt"
        src.write_text("hello", encoding="utf-8")
        result = fs.copy_file(src, dst)
        assert result == dst
        assert src.exists()
        assert dst.read_text(encoding="utf-8") == "hello"

    def test_copy_dir(self, fs: NativeFilesystem, tmp_path: Path):
        src = tmp_path / "srcdir"
        dst = tmp_path / "dstdir"
        src.mkdir()
        (src / "file.txt").touch()
        result = fs.copy_dir(src, dst)
        assert result == dst
        assert dst.is_dir()
        assert (dst / "file.txt").exists()

    def test_copy_dir_with_ignore(self, fs: NativeFilesystem, tmp_path: Path):
        src = tmp_path / "srcdir"
        dst = tmp_path / "dstdir"
        src.mkdir()
        (src / "keep.txt").touch()
        (src / "ignore.me").touch()
        result = fs.copy_dir(src, dst, ignore_patterns={"*.me"})
        assert (dst / "keep.txt").exists()
        assert not (dst / "ignore.me").exists()

    def test_move_file(self, fs: NativeFilesystem, tmp_path: Path):
        src = tmp_path / "src.txt"
        dst = tmp_path / "dst.txt"
        src.write_text("move me", encoding="utf-8")
        result = fs.move(src, dst)
        assert result == dst
        assert not src.exists()
        assert dst.read_text(encoding="utf-8") == "move me"

    def test_move_dir(self, fs: NativeFilesystem, tmp_path: Path):
        src = tmp_path / "srcdir"
        dst = tmp_path / "dstdir"
        src.mkdir()
        (src / "a.txt").touch()
        fs.move(src, dst)
        assert not src.exists()
        assert (dst / "a.txt").exists()

    def test_read_dir(self, fs: NativeFilesystem, tmp_path: Path):
        (tmp_path / "a.txt").touch()
        (tmp_path / "b.txt").touch()
        entries = fs.read_dir(tmp_path)
        names = [p.name for p in entries]
        assert "a.txt" in names
        assert "b.txt" in names

    def test_read_dir_nonexistent_raises(self, fs: NativeFilesystem, tmp_path: Path):
        with pytest.raises(PathNotFoundError):
            fs.read_dir(tmp_path / "nope")

    def test_read_dir_recursive(self, fs: NativeFilesystem, tmp_path: Path):
        sub = tmp_path / "sub" / "nested"
        sub.mkdir(parents=True)
        (sub / "deep.txt").touch()
        entries = fs.read_dir_recursive(tmp_path)
        assert any("deep.txt" in str(e) for e in entries)

    def test_read_file_text(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "test.txt"
        target.write_text("hello world", encoding="utf-8")
        assert fs.read_file(target) == "hello world"

    def test_read_file_binary(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "test.bin"
        target.write_bytes(b"\x00\x01\x02")
        assert fs.read_file(target, mode="binary") == b"\x00\x01\x02"

    def test_write_file_text(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "out.txt"
        target.touch()
        fs.write_file(target, "new content")
        assert target.read_text(encoding="utf-8") == "new content"

    def test_write_file_binary(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "out.bin"
        target.touch()
        fs.write_file(target, b"\xde\xad\xbe\xef")
        assert target.read_bytes() == b"\xde\xad\xbe\xef"

    def test_exists(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "exists.txt"
        assert fs.exists(tmp_path) is True
        assert fs.exists(target) is False
        target.touch()
        assert fs.exists(target) is True

    def test_is_file_is_dir(self, fs: NativeFilesystem, tmp_path: Path):
        f = tmp_path / "afile.txt"
        d = tmp_path / "adir"
        f.touch()
        d.mkdir()
        assert fs.is_file(f) is True
        assert fs.is_dir(f) is False
        assert fs.is_dir(d) is True
        assert fs.is_file(d) is False

    def test_get_metadata(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "meta.txt"
        target.write_text("data", encoding="utf-8")
        meta = fs.get_metadata(target)
        assert meta["size"] == 4
        assert meta["is_file"] is True
        assert meta["is_dir"] is False
        assert meta["is_symlink"] is False
        assert "permissions" in meta

    def test_get_permissions(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "perm.txt"
        target.touch()
        perms = fs.get_permissions(target)
        assert perms.startswith("0o")


class TestCrossOperationWorkflows:

    def test_create_write_read_delete_cycle(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "cycle.txt"
        fs.create_file(target)
        assert target.exists()
        fs.write_file(target, "workflow test")
        assert fs.read_file(target) == "workflow test"
        fs.delete_file(target)
        assert not target.exists()

    def test_create_dir_populate_copy_verify(self, fs: NativeFilesystem, tmp_path: Path):
        src_dir = tmp_path / "source"
        dst_dir = tmp_path / "copy"
        fs.create_dir(src_dir)
        nested = src_dir / "sub" / "nested"
        nested.mkdir(parents=True)
        (nested / "file.txt").write_text("deep", encoding="utf-8")
        fs.copy_dir(src_dir, dst_dir)
        assert (dst_dir / "sub" / "nested" / "file.txt").exists()
        assert (dst_dir / "sub" / "nested" / "file.txt").read_text(encoding="utf-8") == "deep"

    def test_create_rename_read(self, fs: NativeFilesystem, tmp_path: Path):
        src = tmp_path / "before.txt"
        dst = tmp_path / "after.txt"
        fs.create_file(src)
        fs.write_file(src, "renamed content")
        fs.rename(src, dst)
        assert not src.exists()
        assert fs.read_file(dst) == "renamed content"

    def test_create_move_back(self, fs: NativeFilesystem, tmp_path: Path):
        a = tmp_path / "a.txt"
        b = tmp_path / "sub" / "b.txt"
        fs.create_file(a)
        fs.write_file(a, "move test")
        b.parent.mkdir()
        fs.move(a, b)
        assert not a.exists()
        assert fs.read_file(b) == "move test"
        fs.move(b, a)
        assert not b.exists()
        assert fs.read_file(a) == "move test"


class TestErrorTranslation:

    def test_read_nonexistent_raises_path_not_found(self, fs: NativeFilesystem):
        with pytest.raises(PathNotFoundError):
            fs.read_file(Path("/nonexistent/path.txt"))

    def test_delete_nonexistent_raises_path_not_found(self, fs: NativeFilesystem, tmp_path: Path):
        with pytest.raises(PathNotFoundError):
            fs.delete_file(tmp_path / "nope.txt")

    def test_create_file_in_nonexistent_dir_raises(self, fs: NativeFilesystem, tmp_path: Path):
        with pytest.raises((PathNotFoundError, FileExplorerError)):
            fs.create_file(tmp_path / "nope" / "file.txt")

    def test_copy_nonexistent_source_raises(self, fs: NativeFilesystem, tmp_path: Path):
        with pytest.raises((PathNotFoundError, FileExplorerError)):
            fs.copy_file(tmp_path / "nope.txt", tmp_path / "out.txt")


class TestPermissionScenarios:

    def test_delete_readonly_file_on_windows(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "readonly.txt"
        target.touch()
        os.chmod(str(target), stat.S_IREAD)
        try:
            with pytest.raises(PermissionDeniedError):
                fs.delete_file(target)
        finally:
            os.chmod(str(target), stat.S_IWRITE)
            target.unlink()

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific: file locking test")
    def test_file_in_use_on_windows(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "locked.txt"
        target.touch()
        import io
        with io.open(str(target), "w", encoding="utf-8") as f:
            f.write("locked")
            f.flush()
            os.fsync(f.fileno())
            with pytest.raises(FileInUseError):
                fs.delete_file(target)

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific: chmod permission test")
    def test_delete_unreadable_file_on_unix(self, fs: NativeFilesystem, tmp_path: Path):
        target = tmp_path / "no_perm.txt"
        target.touch()
        os.chmod(str(target), 0o000)
        try:
            with pytest.raises(PermissionDeniedError):
                fs.delete_file(target)
        finally:
            os.chmod(str(target), 0o644)
            target.unlink()
