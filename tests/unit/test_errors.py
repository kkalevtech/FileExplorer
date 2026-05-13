import os
import sys
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
from file_explorer.permissions import (
    PermissionManager,
    is_retryable,
    user_friendly_message,
)


class TestCheckReadable:
    def test_readable_file(self, tmp_path: Path):
        target = tmp_path / "readable.txt"
        target.touch()
        assert PermissionManager.check_readable(target) is True

    def test_nonexistent_file(self, tmp_path: Path):
        assert PermissionManager.check_readable(tmp_path / "ghost.txt") is False


class TestCheckWritable:
    def test_writable_file(self, tmp_path: Path):
        target = tmp_path / "writable.txt"
        target.touch()
        assert PermissionManager.check_writable(target) is True

    def test_writable_directory(self, tmp_path: Path):
        assert PermissionManager.check_writable(tmp_path) is True


class TestCheckExecutable:
    def test_executable_directory(self, tmp_path: Path):
        assert PermissionManager.check_executable(tmp_path) is True


class TestIsSystemProtected:
    def test_not_protected(self, tmp_path: Path):
        assert PermissionManager.is_system_protected(tmp_path) is False

    def test_windows_protected_paths(self):
        if sys.platform == "win32":
            assert PermissionManager.is_system_protected("C:\\Windows") is True
            assert PermissionManager.is_system_protected("C:\\Windows\\System32") is True

    def test_linux_protected_paths(self):
        if sys.platform == "linux":
            assert PermissionManager.is_system_protected("/proc") is True
            assert PermissionManager.is_system_protected("/sys") is True


class TestGetAccessibleDescendants:
    def test_accessible_descendants(self, tmp_path: Path):
        (tmp_path / "a.txt").touch()
        (tmp_path / "sub" / "b.txt").mkdir(parents=True)
        result = PermissionManager.get_accessible_descendants(tmp_path)
        assert len(result) > 0


class TestIsRetryable:
    def test_file_in_use_is_retryable(self):
        assert is_retryable(FileInUseError()) is True

    def test_disk_full_is_retryable(self):
        assert is_retryable(DiskFullError()) is True

    def test_path_not_found_not_retryable(self):
        assert is_retryable(PathNotFoundError()) is False

    def test_permission_denied_not_retryable(self):
        assert is_retryable(PermissionDeniedError()) is False

    def test_base_error_not_retryable(self):
        assert is_retryable(FileExplorerError()) is False


class TestUserFriendlyMessage:
    def test_path_not_found_message(self):
        e = PathNotFoundError(path=Path("/test/file.txt"))
        msg = user_friendly_message(e)
        assert "could not be found" in msg

    def test_permission_denied_message(self):
        e = PermissionDeniedError(path=Path("/test/file.txt"))
        msg = user_friendly_message(e)
        assert "don't have permission" in msg

    def test_file_in_use_message(self):
        e = FileInUseError(path=Path("/test/file.txt"))
        msg = user_friendly_message(e)
        assert "in use" in msg

    def test_disk_full_message(self):
        e = DiskFullError()
        msg = user_friendly_message(e)
        assert "disk space" in msg

    def test_file_already_exists_message(self):
        e = FileAlreadyExistsError(path=Path("/test/file.txt"))
        msg = user_friendly_message(e)
        assert "already exists" in msg

    def test_generic_message(self):
        e = FileExplorerError("Something went wrong")
        msg = user_friendly_message(e)
        assert "Something went wrong" in msg
