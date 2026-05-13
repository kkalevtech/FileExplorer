from pathlib import Path

import pytest

from file_explorer.exceptions import InvalidPathError
from file_explorer.path_utils import (
    common_ancestor,
    is_subpath,
    resolve_path,
    sanitize_filename,
    split_path_components,
    unique_path,
)


class TestResolvePath:
    def test_resolve_absolute(self):
        result = resolve_path("/absolute/path")
        assert result.is_absolute()

    def test_resolve_relative(self, tmp_path: Path):
        base = tmp_path / "parent" / "child"
        result = resolve_path("sub/file.txt", base=base)
        assert result == (base / "sub/file.txt").resolve()

    def test_resolve_home(self):
        result = resolve_path("~")
        assert result == Path.home()

    def test_resolve_empty_raises(self):
        with pytest.raises(InvalidPathError):
            resolve_path("")

    def test_resolve_whitespace_raises(self):
        with pytest.raises(InvalidPathError):
            resolve_path("   ")


class TestIsSubpath:
    def test_is_subpath_true(self, tmp_path: Path):
        parent = tmp_path / "parent"
        child = parent / "child"
        parent.mkdir()
        child.mkdir()
        assert is_subpath(child, parent) is True

    def test_is_subpath_false(self, tmp_path: Path):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        assert is_subpath(a, b) is False

    def test_is_subpath_equal(self, tmp_path: Path):
        p = tmp_path / "dir"
        p.mkdir()
        assert is_subpath(p, p) is False


class TestSanitizeFilename:
    def test_removes_illegal_chars(self):
        result = sanitize_filename('file<>:"/\\|?*.txt')
        assert result == "file.txt"

    def test_keeps_valid_name(self):
        result = sanitize_filename("hello_world.py")
        assert result == "hello_world.py"

    def test_strips_trailing_dots_and_spaces(self):
        result = sanitize_filename("  name...  ")
        assert result == "name"


class TestUniquePath:
    def test_no_collision(self, tmp_path: Path):
        result = unique_path(tmp_path, "new_file.txt")
        assert result == tmp_path / "new_file.txt"

    def test_with_collision(self, tmp_path: Path):
        (tmp_path / "file.txt").touch()
        result = unique_path(tmp_path, "file.txt")
        assert result == tmp_path / "file (1).txt"

    def test_multiple_collisions(self, tmp_path: Path):
        (tmp_path / "file.txt").touch()
        (tmp_path / "file (1).txt").touch()
        result = unique_path(tmp_path, "file.txt")
        assert result == tmp_path / "file (2).txt"

    def test_no_extension(self, tmp_path: Path):
        (tmp_path / "readme").touch()
        result = unique_path(tmp_path, "readme")
        assert result == tmp_path / "readme (1)"


class TestSplitPathComponents:
    def test_returns_components(self):
        p = Path("/home/user/docs/file.txt")
        parts = split_path_components(p)
        assert isinstance(parts, list)
        assert all(isinstance(c, str) for c in parts)

    def test_relative_path(self):
        p = Path("relative/path/to/file")
        parts = split_path_components(p)
        assert len(parts) >= 3


class TestCommonAncestor:
    def test_common_ancestor(self, tmp_path: Path):
        a = tmp_path / "a" / "b" / "c"
        b = tmp_path / "a" / "b" / "d"
        a.mkdir(parents=True)
        b.mkdir(parents=True)
        ancestor = common_ancestor([a, b])
        assert ancestor == (tmp_path / "a" / "b").resolve()

    def test_single_path(self, tmp_path: Path):
        p = tmp_path / "x" / "y" / "z"
        p.mkdir(parents=True)
        assert common_ancestor([p]) == p.resolve()

    def test_no_common_ancestor(self):
        result = common_ancestor([Path("/a/b"), Path("/c/d")])
        assert result == Path(result.anchor)

    def test_empty_list(self):
        assert common_ancestor([]) == Path()
