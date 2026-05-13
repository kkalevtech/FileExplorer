from pathlib import Path

import pytest

from file_explorer.commands import (
    BatchCommand,
    CopyCommand,
    CreateDirectoryCommand,
    CreateFileCommand,
    DeleteFileCommand,
    MoveCommand,
    OperationHistory,
    RenameCommand,
)
from file_explorer.exceptions import OperationCannotUndoError
from tests.conftest import MockFilesystem


@pytest.fixture
def fs():
    mock = MockFilesystem()
    mock.create_dir(Path.cwd())
    return mock


class TestCreateFileCommand:
    def test_execute_creates_file(self, fs: MockFilesystem):
        target = Path.cwd() / "new.txt"
        cmd = CreateFileCommand(fs, target)
        result = cmd.execute()
        assert result.success is True
        assert fs.exists(target) is True

    def test_undo_deletes_file(self, fs: MockFilesystem):
        target = Path.cwd() / "new.txt"
        cmd = CreateFileCommand(fs, target)
        cmd.execute()
        undo_result = cmd.undo()
        assert undo_result.success is True
        assert fs.exists(target) is False


class TestCreateDirectoryCommand:
    def test_execute_creates_directory(self, fs: MockFilesystem):
        target = Path.cwd() / "newdir"
        cmd = CreateDirectoryCommand(fs, target)
        result = cmd.execute()
        assert result.success is True
        assert fs.is_dir(target) is True

    def test_undo_deletes_directory(self, fs: MockFilesystem):
        target = Path.cwd() / "newdir"
        cmd = CreateDirectoryCommand(fs, target)
        cmd.execute()
        undo_result = cmd.undo()
        assert undo_result.success is True
        assert fs.exists(target) is False


class TestDeleteFileCommand:
    def test_execute_deletes_file(self, fs: MockFilesystem):
        target = Path.cwd() / "delete_me.txt"
        fs.create_file(target)
        cmd = DeleteFileCommand(fs, target)
        result = cmd.execute()
        assert result.success is True
        assert fs.exists(target) is False

    def test_undo_raises(self, fs: MockFilesystem):
        target = Path.cwd() / "delete_me.txt"
        fs.create_file(target)
        cmd = DeleteFileCommand(fs, target)
        cmd.execute()
        with pytest.raises(OperationCannotUndoError):
            cmd.undo()


class TestRenameCommand:
    def test_execute_renames(self, fs: MockFilesystem):
        src = Path.cwd() / "old.txt"
        dst = Path.cwd() / "new.txt"
        fs.create_file(src)
        cmd = RenameCommand(fs, src, dst)
        result = cmd.execute()
        assert result.success is True
        assert fs.exists(src) is False
        assert fs.exists(dst) is True

    def test_undo_reverses_rename(self, fs: MockFilesystem):
        src = Path.cwd() / "old.txt"
        dst = Path.cwd() / "new.txt"
        fs.create_file(src)
        cmd = RenameCommand(fs, src, dst)
        cmd.execute()
        undo_result = cmd.undo()
        assert undo_result.success is True
        assert fs.exists(src) is True
        assert fs.exists(dst) is False


class TestCopyCommand:
    def test_execute_copies(self, fs: MockFilesystem):
        src = Path.cwd() / "src.txt"
        dst = Path.cwd() / "dst.txt"
        fs.create_file(src)
        cmd = CopyCommand(fs, src, dst)
        result = cmd.execute()
        assert result.success is True
        assert fs.exists(dst) is True

    def test_undo_deletes_copy(self, fs: MockFilesystem):
        src = Path.cwd() / "src.txt"
        dst = Path.cwd() / "dst.txt"
        fs.create_file(src)
        cmd = CopyCommand(fs, src, dst)
        cmd.execute()
        undo_result = cmd.undo()
        assert undo_result.success is True
        assert fs.exists(dst) is False
        assert fs.exists(src) is True


class TestMoveCommand:
    def test_execute_moves(self, fs: MockFilesystem):
        src = Path.cwd() / "src.txt"
        dst = Path.cwd() / "dst.txt"
        fs.create_file(src)
        cmd = MoveCommand(fs, src, dst)
        result = cmd.execute()
        assert result.success is True
        assert fs.exists(src) is False
        assert fs.exists(dst) is True

    def test_undo_moves_back(self, fs: MockFilesystem):
        src = Path.cwd() / "src.txt"
        dst = Path.cwd() / "dst.txt"
        fs.create_file(src)
        cmd = MoveCommand(fs, src, dst)
        cmd.execute()
        undo_result = cmd.undo()
        assert undo_result.success is True
        assert fs.exists(src) is True
        assert fs.exists(dst) is False


class TestBatchCommand:
    def test_execute_all(self, fs: MockFilesystem):
        cmds = [
            CreateFileCommand(fs, Path.cwd() / "a.txt"),
            CreateFileCommand(fs, Path.cwd() / "b.txt"),
        ]
        batch = BatchCommand(cmds)
        result = batch.execute()
        assert result.success is True
        assert fs.exists(Path.cwd() / "a.txt") is True
        assert fs.exists(Path.cwd() / "b.txt") is True


class TestOperationHistory:
    def test_push_and_undo(self, fs: MockFilesystem):
        history = OperationHistory(limit=10)
        target = Path.cwd() / "test.txt"
        cmd = CreateFileCommand(fs, target)
        cmd.execute()
        history.push(cmd)

        assert history.can_undo is True
        result = history.undo()
        assert result is not None
        assert fs.exists(target) is False

    def test_redo(self, fs: MockFilesystem):
        history = OperationHistory(limit=10)
        target = Path.cwd() / "test.txt"
        cmd = CreateFileCommand(fs, target)
        cmd.execute()
        history.push(cmd)
        history.undo()

        assert history.can_redo is True
        result = history.redo()
        assert result is not None
        assert fs.exists(target) is True

    def test_undo_empty_history(self):
        history = OperationHistory()
        assert history.undo() is None

    def test_redo_empty_history(self):
        history = OperationHistory()
        assert history.redo() is None

    def test_history_limit_enforced(self, fs: MockFilesystem):
        history = OperationHistory(limit=3)
        for i in range(5):
            target = Path.cwd() / f"f{i}.txt"
            cmd = CreateFileCommand(fs, target)
            cmd.execute()
            history.push(cmd)
        assert len(history._history) <= 3

    def test_clear(self, fs: MockFilesystem):
        history = OperationHistory()
        target = Path.cwd() / "test.txt"
        cmd = CreateFileCommand(fs, target)
        cmd.execute()
        history.push(cmd)
        history.undo()
        history.clear()
        assert history.can_undo is False
        assert history.can_redo is False

    def test_push_clears_redo(self, fs: MockFilesystem):
        history = OperationHistory()
        target1 = Path.cwd() / "a.txt"
        cmd1 = CreateFileCommand(fs, target1)
        cmd1.execute()
        history.push(cmd1)
        history.undo()

        target2 = Path.cwd() / "b.txt"
        cmd2 = CreateFileCommand(fs, target2)
        cmd2.execute()
        history.push(cmd2)
        assert history.can_redo is False


class TestCommandTimestamp:
    def test_timestamp_set_on_init(self):
        fs = MockFilesystem()
        cmd = CreateFileCommand(fs, Path.cwd() / "test.txt")
        assert cmd.timestamp is not None
