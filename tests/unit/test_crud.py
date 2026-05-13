from pathlib import Path

import pytest

from file_explorer.crud import (
    create_directory,
    create_file,
    delete_item,
    duplicate_item,
    read_file_content,
    rename_item,
    write_file_content,
)
from file_explorer.exceptions import (
    FileAlreadyExistsError,
    FileExplorerError,
    PathNotFoundError,
)
from file_explorer.filesystem import NativeFilesystem


@pytest.fixture
def fs():
    return NativeFilesystem()


class TestCreateFile:
    def test_create_file_new(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "new.txt"
        result = create_file(fs, target)
        assert result == target.resolve()
        assert target.exists()

    def test_create_file_existing_no_overwrite(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "existing.txt"
        target.touch()
        with pytest.raises(FileAlreadyExistsError):
            create_file(fs, target)

    def test_create_file_existing_overwrite(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "existing.txt"
        target.write_text("old")
        result = create_file(fs, target, overwrite=True)
        assert result == target.resolve()
        assert target.exists()

    def test_create_file_parent_missing_raises(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "ghost" / "file.txt"
        with pytest.raises(PathNotFoundError):
            create_file(fs, target)


class TestCreateDirectory:
    def test_create_directory_new(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "newdir"
        result = create_directory(fs, target)
        assert result == target.resolve()
        assert target.is_dir()

    def test_create_directory_existing_ok(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "existing"
        target.mkdir()
        result = create_directory(fs, target, exist_ok=True)
        assert result == target.resolve()

    def test_create_directory_existing_no_exist_ok_raises(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "existing"
        target.mkdir()
        with pytest.raises(FileAlreadyExistsError):
            create_directory(fs, target)


class TestReadFileContent:
    def test_read_file_content_text(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "hello.txt"
        target.write_text("Hello, World!")
        content = read_file_content(fs, target)
        assert content == "Hello, World!"

    def test_read_file_nonexistent_raises(self, tmp_path: Path, fs: NativeFilesystem):
        with pytest.raises(PathNotFoundError):
            read_file_content(fs, tmp_path / "ghost.txt")


class TestWriteFileContent:
    def test_write_file_content(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "output.txt"
        result = write_file_content(fs, target, "new content")
        assert result == target.resolve()
        assert target.read_text() == "new content"


class TestDeleteItem:
    def test_delete_file(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "delete_me.txt"
        target.touch()
        delete_item(fs, target)
        assert not target.exists()

    def test_delete_dir_empty(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "empty_dir"
        target.mkdir()
        delete_item(fs, target)
        assert not target.exists()

    def test_delete_dir_nonempty_no_recursive_raises(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "parent"
        (target / "child").mkdir(parents=True)
        with pytest.raises(FileExplorerError):
            delete_item(fs, target)

    def test_delete_dir_nonempty_recursive(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "parent"
        (target / "child" / "file.txt").mkdir(parents=True)
        delete_item(fs, target, recursive=True)
        assert not target.exists()


class TestRenameItem:
    def test_rename_item(self, tmp_path: Path, fs: NativeFilesystem):
        src = tmp_path / "old.txt"
        dst = tmp_path / "new.txt"
        src.touch()
        result = rename_item(fs, src, dst)
        assert result == dst.resolve()
        assert dst.exists()
        assert not src.exists()

    def test_rename_with_overwrite(self, tmp_path: Path, fs: NativeFilesystem):
        src = tmp_path / "src.txt"
        dst = tmp_path / "dst.txt"
        src.write_text("source")
        dst.write_text("destination")
        result = rename_item(fs, src, dst, overwrite=True)
        assert result == dst.resolve()
        assert dst.read_text() == "source"


class TestDuplicateItem:
    def test_duplicate_file(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "file.txt"
        target.write_text("content")
        result = duplicate_item(fs, target)
        assert result.exists()
        assert result.name == "file \u2014 Copy.txt"

    def test_duplicate_twice(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "file.txt"
        target.write_text("content")
        first = duplicate_item(fs, target)
        second = duplicate_item(fs, target)
        assert first.exists()
        assert second.exists()
        assert first != second
