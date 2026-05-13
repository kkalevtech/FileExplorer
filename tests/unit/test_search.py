from pathlib import Path

from file_explorer.search import SearchOptions, SearchResult, search_by_name
from tests.conftest import MockFilesystem


def _tree(fs: MockFilesystem) -> None:
    fs.create_file(Path("/root/document.txt"))
    fs.create_file(Path("/root/photo.jpg"))
    fs.create_file(Path("/root/notes.txt"))
    fs.create_dir(Path("/root/sub"))
    fs.create_file(Path("/root/sub/deep.txt"))
    fs.create_file(Path("/root/sub/readme.md"))
    fs.create_file(Path("/root/.hidden.txt"))
    fs.create_dir(Path("/root/empty_dir"))


class TestSearchExactMatch:
    def test_exact_match(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="document.txt", root_path=Path("/root"))
        results = search_by_name(fs, opts)
        assert len(results) == 1
        assert results[0].name == "document.txt"

    def test_no_matches(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="nonexistent.py", root_path=Path("/root"))
        results = search_by_name(fs, opts)
        assert len(results) == 0


class TestSearchWildcard:
    def test_wildcard(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="*.txt", root_path=Path("/root"))
        results = search_by_name(fs, opts)
        names = {r.name for r in results}
        assert "document.txt" in names
        assert "notes.txt" in names
        assert "deep.txt" in names
        assert "photo.jpg" not in names

    def test_question_mark(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="document.???", root_path=Path("/root"))
        results = search_by_name(fs, opts)
        assert len(results) == 1
        assert results[0].name == "document.txt"


class TestSearchCaseInsensitive:
    def test_case_insensitive_default(self):
        fs = MockFilesystem()
        fs.create_file(Path("/root/File.txt"))
        opts = SearchOptions(pattern="file.txt", root_path=Path("/root"))
        results = search_by_name(fs, opts)
        assert len(results) == 1


class TestSearchRecursive:
    def test_recursive_finds_nested(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="deep.txt", root_path=Path("/root"), recursive=True)
        results = search_by_name(fs, opts)
        assert len(results) == 1

    def test_non_recursive_does_not_find_nested(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="deep.txt", root_path=Path("/root"), recursive=False)
        results = search_by_name(fs, opts)
        assert len(results) == 0


class TestSearchHidden:
    def test_hidden_excluded_by_default(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="*.txt", root_path=Path("/root"))
        results = search_by_name(fs, opts)
        names = {r.name for r in results}
        assert ".hidden.txt" not in names

    def test_hidden_included_when_requested(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="*.txt", root_path=Path("/root"), include_hidden=True)
        results = search_by_name(fs, opts)
        names = {r.name for r in results}
        assert ".hidden.txt" in names


class TestSearchFileFilter:
    def test_files_only(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="*", root_path=Path("/root"), file_filter=True)
        results = search_by_name(fs, opts)
        assert all(r.path for r in results)
        for r in results:
            assert fs.is_file(r.path) is True

    def test_dirs_only(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="*", root_path=Path("/root"), file_filter=False)
        results = search_by_name(fs, opts)
        assert all(r.path for r in results)
        for r in results:
            assert fs.is_dir(r.path) is True


class TestSearchMaxResults:
    def test_max_results_capped(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="*", root_path=Path("/root"), max_results=2)
        results = search_by_name(fs, opts)
        assert len(results) <= 2


class TestSearchEmptyPattern:
    def test_empty_pattern_returns_all(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="", root_path=Path("/root"), max_results=100)
        results = search_by_name(fs, opts)
        assert len(results) > 0


class TestSearchPermissionDenied:
    def test_skip_permission_denied(self):
        fs = MockFilesystem()
        _tree(fs)
        fs.set_restricted(Path("/root/sub"))
        opts = SearchOptions(pattern="*", root_path=Path("/root"), recursive=True)
        results = search_by_name(fs, opts)
        assert len(results) > 0
        found_names = {r.name for r in results}
        assert "deep.txt" not in found_names
        assert "readme.md" not in found_names


class TestSearchResultDataclass:
    def test_search_result_fields(self):
        r = SearchResult(path=Path("/a.txt"), name="a.txt", score=1.0)
        assert r.path == Path("/a.txt")
        assert r.name == "a.txt"
        assert r.score == 1.0

    def test_search_result_default_score(self):
        r = SearchResult(path=Path("/a.txt"), name="a.txt")
        assert r.score == 0.0


class TestSearchRootPath:
    def test_search_from_root(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="*.txt", root_path=Path("/"))
        results = search_by_name(fs, opts)
        assert len(results) >= 3


class TestSearchSorted:
    def test_results_sorted_by_path(self):
        fs = MockFilesystem()
        _tree(fs)
        opts = SearchOptions(pattern="*", root_path=Path("/root"), max_results=100)
        results = search_by_name(fs, opts)
        paths = [r.path for r in results]
        assert paths == sorted(paths)
