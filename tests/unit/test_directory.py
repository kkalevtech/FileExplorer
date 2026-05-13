from pathlib import Path

import pytest

from file_explorer.directory import DirectoryNavigator
from file_explorer.exceptions import FileExplorerError, PathNotFoundError
from file_explorer.filesystem import NativeFilesystem


@pytest.fixture
def fs():
    return NativeFilesystem()


@pytest.fixture
def nav(tmp_path: Path, fs: NativeFilesystem):
    return DirectoryNavigator(fs, tmp_path)


class TestInit:
    def test_current_starts_at_correct_dir(self, tmp_path: Path, fs: NativeFilesystem):
        nav = DirectoryNavigator(fs, tmp_path)
        assert nav.current == tmp_path.resolve()

    def test_nonexistent_start_dir_raises(self, fs: NativeFilesystem):
        with pytest.raises(PathNotFoundError):
            DirectoryNavigator(fs, Path("/nonexistent_path_xyz"))


class TestListContents:
    def test_returns_sorted(self, nav: DirectoryNavigator, tmp_path: Path):
        (tmp_path / "z.txt").touch()
        (tmp_path / "a.txt").touch()
        contents = nav.list_contents()
        assert contents[0].name == "a.txt"
        assert contents[1].name == "z.txt"

    def test_hidden_excluded_by_default(self, nav: DirectoryNavigator, tmp_path: Path):
        (tmp_path / "visible.txt").touch()
        (tmp_path / ".hidden").touch()
        contents = nav.list_contents()
        assert all(not c.name.startswith(".") for c in contents)

    def test_hidden_included_when_requested(self, nav: DirectoryNavigator, tmp_path: Path):
        (tmp_path / "visible.txt").touch()
        (tmp_path / ".hidden").touch()
        contents = nav.list_contents(show_hidden=True)
        names = {c.name for c in contents}
        assert "visible.txt" in names
        assert ".hidden" in names


class TestEnter:
    def test_enter_subdirectory(self, nav: DirectoryNavigator, tmp_path: Path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        result = nav.enter("subdir")
        assert result == sub.resolve()
        assert nav.current == sub.resolve()

    def test_enter_file_raises(self, nav: DirectoryNavigator, tmp_path: Path):
        f = tmp_path / "file.txt"
        f.touch()
        with pytest.raises(FileExplorerError):
            nav.enter("file.txt")

    def test_enter_nonexistent_raises(self, nav: DirectoryNavigator):
        with pytest.raises(PathNotFoundError):
            nav.enter("ghost")


class TestGoUp:
    def test_go_up(self, nav: DirectoryNavigator, tmp_path: Path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        nav.enter("subdir")
        result = nav.go_up()
        assert result == tmp_path.resolve()

    def test_go_up_at_root(self, nav: DirectoryNavigator, tmp_path: Path):
        root_result = nav.go_up()
        assert root_result == nav.current

    def test_go_up_multiple_times(self, nav: DirectoryNavigator, tmp_path: Path):
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        nav.go_to(deep)
        nav.go_up()
        assert nav.current == (deep.parent).resolve()
        nav.go_up()
        assert nav.current == (deep.parent.parent).resolve()


class TestGoTo:
    def test_go_to_absolute(self, nav: DirectoryNavigator, tmp_path: Path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        result = nav.go_to(sub)
        assert result == sub.resolve()

    def test_go_to_nonexistent_raises(self, nav: DirectoryNavigator):
        with pytest.raises(PathNotFoundError):
            nav.go_to(Path("/nonexistent_xyz_123"))


class TestHistory:
    def test_history_tracks_navigation(self, nav: DirectoryNavigator, tmp_path: Path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        nav.enter("subdir")
        assert len(nav.get_history()) == 1
        assert nav.get_history()[0] == tmp_path.resolve()
        nav.go_up()
        assert len(nav.get_history()) == 2

    def test_go_back_restores_previous(self, nav: DirectoryNavigator, tmp_path: Path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        nav.enter("subdir")
        result = nav.go_back()
        assert result == tmp_path.resolve()
        assert nav.current == tmp_path.resolve()

    def test_go_back_empty_history(self, nav: DirectoryNavigator):
        assert nav.go_back() is None

    def test_history_does_not_grow_unbounded(self, nav: DirectoryNavigator, tmp_path: Path):
        for i in range(150):
            d = tmp_path / f"sub{i}"
            d.mkdir()
            nav.go_to(d)
        assert len(nav.get_history()) <= 100


class TestGoForward:
    def test_go_forward_after_go_back(self, nav: DirectoryNavigator, tmp_path: Path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        nav.enter("subdir")
        nav.go_back()
        result = nav.go_forward()
        assert result == sub.resolve()

    def test_go_forward_empty(self, nav: DirectoryNavigator):
        assert nav.go_forward() is None

    def test_forward_cleared_on_new_navigation(self, nav: DirectoryNavigator, tmp_path: Path):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        nav.enter("a")
        nav.go_back()
        nav.enter("b")
        assert nav.go_forward() is None


class TestRefresh:
    def test_refresh_returns_current_contents(self, nav: DirectoryNavigator, tmp_path: Path):
        (tmp_path / "new_file.txt").touch()
        contents = nav.refresh()
        assert any(c.name == "new_file.txt" for c in contents)


class TestRoot:
    def test_root_property(self, nav: DirectoryNavigator):
        root = nav.root
        assert root == Path(nav.current.anchor)
