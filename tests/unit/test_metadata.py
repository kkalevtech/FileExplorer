import platform
from pathlib import Path

import pytest

from file_explorer.exceptions import FileExplorerError
from file_explorer.filesystem import NativeFilesystem
from file_explorer.metadata import FileMetadata, _get_extension, _is_hidden, _is_readonly, get_metadata, get_size_formatted


@pytest.fixture
def fs():
    return NativeFilesystem()


class TestGetMetadata:
    def test_get_metadata_file(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "test.txt"
        target.write_text("hello")
        meta = get_metadata(fs, target)
        assert isinstance(meta, FileMetadata)
        assert meta.size == 5
        assert meta.is_file is True
        assert meta.is_dir is False
        assert meta.extension == "txt"

    def test_get_metadata_directory(self, tmp_path: Path, fs: NativeFilesystem):
        meta = get_metadata(fs, tmp_path)
        assert isinstance(meta, FileMetadata)
        assert meta.is_dir is True
        assert meta.is_file is False

    def test_get_metadata_nonexistent_raises(self, tmp_path: Path, fs: NativeFilesystem):
        with pytest.raises(FileExplorerError):
            get_metadata(fs, tmp_path / "ghost.txt")

    def test_get_metadata_hidden_file(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / ".hidden"
        target.touch()
        meta = get_metadata(fs, target)
        assert meta.is_hidden is True

    def test_get_metadata_symlink(self, tmp_path: Path, fs: NativeFilesystem):
        target = tmp_path / "real.txt"
        link = tmp_path / "link.txt"
        target.write_text("content")
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            pytest.skip("Symlink not supported on this platform")
        meta = get_metadata(fs, link)
        assert meta.is_symlink is True


class TestGetSizeFormatted:
    def test_bytes(self):
        assert get_size_formatted(0) == "0 B"
        assert get_size_formatted(512) == "512 B"
        assert get_size_formatted(1023) == "1023 B"

    def test_kb(self):
        assert get_size_formatted(1024) == "1.0 KB"
        assert get_size_formatted(2048) == "2.0 KB"
        assert get_size_formatted(1536) == "1.5 KB"

    def test_mb(self):
        size = 1024 * 1024 * 2
        assert get_size_formatted(size) == "2.0 MB"
        size_mb_half = 1024 * 1024 * 1 + 512 * 1024
        assert get_size_formatted(size_mb_half) == "1.5 MB"

    def test_gb(self):
        size = 1024 ** 3 * 3
        assert get_size_formatted(size) == "3.0 GB"


class TestGetExtension:
    def test_normal_extension(self):
        assert _get_extension(Path("file.txt")) == "txt"
        assert _get_extension(Path("archive.tar.gz")) == "gz"

    def test_no_extension(self):
        assert _get_extension(Path("README")) == ""

    def test_dotfile_no_extension(self):
        assert _get_extension(Path(".bashrc")) == ""


class TestIsHidden:
    def test_dotfile(self, tmp_path: Path):
        target = tmp_path / ".hidden"
        target.touch()
        assert _is_hidden(target) is True

    def test_visible_file(self, tmp_path: Path):
        target = tmp_path / "visible.txt"
        target.touch()
        assert _is_hidden(target) is False


class TestIsReadonly:
    def test_writable_file(self, tmp_path: Path):
        target = tmp_path / "writable.txt"
        target.touch()
        assert _is_readonly(target) is False

    def test_readonly_file(self, tmp_path: Path):
        target = tmp_path / "readonly.txt"
        target.touch()
        if platform.system() == "Windows":
            import os
            os.system(f'attrib +R "{target}"')
        else:
            target.chmod(0o444)
        assert _is_readonly(target) is True
