from pathlib import Path

import pytest

from file_explorer.copy_move import (
    ConflictStrategy,
    OperationResult,
    batch_copy,
    batch_move,
    copy_item,
    move_item,
)
from file_explorer.exceptions import FileAlreadyExistsError
from tests.conftest import MockFilesystem


class TestCopyItem:
    def test_copy_file_to_new_location(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src.txt"))
        result = copy_item(fs, Path("/src.txt"), Path("/dst.txt"))
        assert result.success is True
        assert fs.exists(Path("/dst.txt")) is True
        assert fs.is_file(Path("/dst.txt")) is True

    def test_copy_file_overwrite(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src.txt"))
        fs.create_file(Path("/dst.txt"))
        result = copy_item(fs, Path("/src.txt"), Path("/dst.txt"), strategy=ConflictStrategy.OVERWRITE)
        assert result.success is True
        assert fs.exists(Path("/dst.txt")) is True

    def test_copy_file_skip(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src.txt"))
        fs.create_file(Path("/dst.txt"))
        result = copy_item(fs, Path("/src.txt"), Path("/dst.txt"), strategy=ConflictStrategy.SKIP)
        assert result.success is True

    def test_copy_file_rename_on_conflict(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src.txt"))
        fs.create_file(Path("/dst.txt"))
        result = copy_item(fs, Path("/src.txt"), Path("/dst.txt"), strategy=ConflictStrategy.RENAME)
        assert result.success is True
        assert result.destination.name != "dst.txt"
        assert fs.exists(result.destination) is True

    def test_copy_file_ask_raises(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src.txt"))
        fs.create_file(Path("/dst.txt"))
        with pytest.raises(FileAlreadyExistsError):
            copy_item(fs, Path("/src.txt"), Path("/dst.txt"), strategy=ConflictStrategy.ASK)

    def test_copy_source_not_found(self):
        fs = MockFilesystem()
        result = copy_item(fs, Path("/ghost.txt"), Path("/dst.txt"))
        assert result.success is False

    def test_copy_same_source_destination_raises(self):
        fs = MockFilesystem()
        fs.create_file(Path("/file.txt"))
        result = copy_item(fs, Path("/file.txt"), Path("/file.txt"))
        assert result.success is False

    def test_copy_directory_recursive(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src/a/b/file.txt"))
        result = copy_item(fs, Path("/src"), Path("/dst"))
        assert result.success is True
        assert fs.exists(Path("/dst/a/b/file.txt")) is True
        assert fs.is_dir(Path("/dst")) is True

    def test_copy_to_existing_directory_appends_name(self):
        fs = MockFilesystem()
        fs.create_dir(Path("/dest"))
        fs.create_file(Path("/src.txt"))
        result = copy_item(fs, Path("/src.txt"), Path("/dest"))
        assert result.success is True
        assert fs.exists(Path("/dest/src.txt")) is True

    def test_copy_with_progress_callback(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src.txt"))
        calls: list[tuple[int, int]] = []

        def cb(completed: int, total: int):
            calls.append((completed, total))

        result = copy_item(fs, Path("/src.txt"), Path("/dst.txt"), progress_callback=cb)
        assert result.success is True
        assert len(calls) >= 1

    def test_copy_cancelled(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src.txt"))
        cancelled = False

        def token():
            return cancelled

        result = copy_item(fs, Path("/src.txt"), Path("/dst.txt"), cancellation_token=token)
        assert result.success is True


class TestMoveItem:
    def test_move_file(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src.txt"))
        result = move_item(fs, Path("/src.txt"), Path("/dst.txt"))
        assert result.success is True
        assert fs.exists(Path("/dst.txt")) is True
        assert fs.exists(Path("/src.txt")) is False

    def test_move_directory(self):
        fs = MockFilesystem()
        fs.create_file(Path("/src/a/b/file.txt"))
        result = move_item(fs, Path("/src"), Path("/dst"))
        assert result.success is True
        assert fs.exists(Path("/dst/a/b/file.txt")) is True
        assert fs.exists(Path("/src")) is False

    def test_move_source_not_found(self):
        fs = MockFilesystem()
        result = move_item(fs, Path("/ghost.txt"), Path("/dst.txt"))
        assert result.success is False

    def test_move_same_source_destination_raises(self):
        fs = MockFilesystem()
        fs.create_file(Path("/file.txt"))
        result = move_item(fs, Path("/file.txt"), Path("/file.txt"))
        assert result.success is False

    def test_move_to_existing_directory_appends_name(self):
        fs = MockFilesystem()
        fs.create_dir(Path("/dest"))
        fs.create_file(Path("/src.txt"))
        result = move_item(fs, Path("/src.txt"), Path("/dest"))
        assert result.success is True
        assert fs.exists(Path("/dest/src.txt")) is True
        assert fs.exists(Path("/src.txt")) is False


class TestBatchCopy:
    def test_batch_copy_returns_results(self):
        fs = MockFilesystem()
        fs.create_file(Path("/a.txt"))
        fs.create_file(Path("/b.txt"))
        items = [(Path("/a.txt"), Path("/copy_a.txt")), (Path("/b.txt"), Path("/copy_b.txt"))]
        results = batch_copy(fs, items)
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_batch_copy_with_progress(self):
        fs = MockFilesystem()
        fs.create_file(Path("/a.txt"))
        fs.create_file(Path("/b.txt"))
        calls: list[int] = []

        def cb(completed: int, total: int):
            calls.append(completed)

        items = [(Path("/a.txt"), Path("/ca.txt")), (Path("/b.txt"), Path("/cb.txt"))]
        batch_copy(fs, items, progress_callback=cb)
        assert len(calls) >= 2


class TestBatchMove:
    def test_batch_move_returns_results(self):
        fs = MockFilesystem()
        fs.create_file(Path("/a.txt"))
        fs.create_file(Path("/b.txt"))
        items = [(Path("/a.txt"), Path("/ma.txt")), (Path("/b.txt"), Path("/mb.txt"))]
        results = batch_move(fs, items)
        assert len(results) == 2
        assert all(r.success for r in results)
        assert fs.exists(Path("/a.txt")) is False
        assert fs.exists(Path("/b.txt")) is False


def test_operation_result_dataclass():
    r = OperationResult(source=Path("/s"), destination=Path("/d"), success=True)
    assert r.source == Path("/s")
    assert r.success is True
    assert r.error is None


def test_conflict_strategy_values():
    assert ConflictStrategy.SKIP.value == "skip"
    assert ConflictStrategy.OVERWRITE.value == "overwrite"
    assert ConflictStrategy.RENAME.value == "rename"
    assert ConflictStrategy.ASK.value == "ask"
