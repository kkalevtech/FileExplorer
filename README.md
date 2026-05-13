# File Explorer — Core Backend

Zero-dependency Python 3.10+ backend for file explorer applications. Provides a complete filesystem operations layer with command abstraction, undo/redo, search, and configuration — all with no third-party packages.

---

## What's Implemented

All 12 phases from the development plan are complete (265 tests passing).

| Module | Exports | Purpose |
|--------|---------|---------|
| `path_utils` | `resolve_path`, `is_subpath`, `sanitize_filename`, `unique_path`, `split_path_components`, `common_ancestor` | Path resolution, security checks, platform-safe naming |
| `filesystem` | `FilesystemAbstraction` (ABC), `NativeFilesystem` | Abstract filesystem interface + real OS implementation |
| `directory` | `DirectoryNavigator` | Directory listing, navigation, history (capped at 100) |
| `crud` | `create_file`, `create_directory`, `read_file_content`, `write_file_content`, `rename_item`, `delete_item`, `duplicate_item` | High-level file/folder operations with validation |
| `metadata` | `FileMetadata`, `get_metadata`, `get_size_formatted` | File size, dates, attributes, extension, hidden/readonly detection |
| `copy_move` | `copy_item`, `move_item`, `batch_copy`, `batch_move`, `ConflictStrategy`, `OperationResult` | Single/batch copy+move with conflict resolution, progress callbacks, cancellation |
| `search` | `search_by_name`, `SearchOptions`, `SearchResult` | Recursive name-based search with glob patterns, filters, max results |
| `permissions` | `PermissionManager`, `is_retryable`, `user_friendly_message` | Permission checks, error categorization, user-facing messages |
| `commands` | `CreateFileCommand`, `CreateDirectoryCommand`, `DeleteFileCommand`, `DeleteDirectoryCommand`, `RenameCommand`, `CopyCommand`, `MoveCommand`, `BatchCommand`, `OperationHistory` | Command pattern with undo/redo, configurable history limit |
| `config` | `AppConfig`, `ConfigManager`, `default_config_path`, `load_config`, `save_config` | Persistent JSON config with atomic saves, corruption handling |
| `exceptions` | `FileExplorerError`, `PathNotFoundError`, `PermissionDeniedError`, `FileAlreadyExistsError`, `DiskFullError`, `FileInUseError`, `InvalidPathError`, `OperationCancelledError`, `OperationCannotUndoError` | Typed exception hierarchy, all carry `path` and `os_error` |
| `_logging` | `setup_logging`, `get_logger` | Structured logging to console + file |

---

## Quick Start

```bash
# Install (editable mode for development)
pip install -e .

# Or install dev dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from pathlib import Path
from file_explorer import (
    NativeFilesystem,
    DirectoryNavigator,
    create_file, write_file_content, read_file_content, delete_item,
    copy_item, move_item,
    search_by_name, SearchOptions,
    get_metadata,
    AppConfig, ConfigManager,
    CreateFileCommand, OperationHistory,
)

fs = NativeFilesystem()

# Navigate
nav = DirectoryNavigator(fs, Path.cwd())
print(nav.list_contents())
nav.enter("subdir")

# CRUD
create_file(fs, Path("new.txt"))
write_file_content(fs, Path("new.txt"), "hello world")
content = read_file_content(fs, Path("new.txt"))
delete_item(fs, Path("new.txt"), recursive=True)

# Copy / Move
result = copy_item(fs, Path("src.txt"), Path("dst.txt"))
result = move_item(fs, Path("src.txt"), Path("dst.txt"))

# Search
results = search_by_name(fs, SearchOptions(pattern="*.py", root_path=Path.cwd()))

# Metadata
meta = get_metadata(fs, Path("file.txt"))
print(meta.size, meta.modified, meta.is_hidden)

# Configuration
config = ConfigManager()
config.set("show_hidden_files", True)
config.set("max_history", 100)

# Commands with undo
history = OperationHistory(limit=50)
cmd = CreateFileCommand(fs, Path("test.txt"))
cmd.execute()
history.push(cmd)
history.undo()  # deletes test.txt
history.redo()  # creates it again
```

---

## Commands

| Command | Description |
|---------|-------------|
| `pip install -e .` | Install package in editable mode |
| `pip install -r requirements.txt` | Install dev dependencies (pytest) |
| `python -m pytest tests/` | Run full test suite (265 tests) |
| `python -m pytest tests/unit/` | Run unit tests only (fast, uses MockFilesystem) |
| `python -m pytest tests/integration/` | Run integration tests (uses real temp directories) |
| `python -m pytest tests/ -v` | Verbose output |
| `python -m pytest tests/ -v --tb=short` | Short traceback |
| `python -m pytest tests/ --cov=src/file_explorer/` | Coverage report |

---

## Architecture

The core is designed around an **abstraction layer** (`FilesystemAbstraction`) that decouples business logic from OS calls.

```
path_utils.py  exceptions.py       (leaf modules, zero deps)
       |
       v
filesystem.py  (ABC + NativeFilesystem)
       |
       v
directory.py  crud.py  metadata.py  copy_move.py  search.py  permissions.py
       |           |          |             |            |           |
       +-----------+----------+-------------+------------+-----------+
                                    |
                                    v
                              commands.py
                                    |
                                    v
                             (your GUI here)
```

Key design decisions:
- **Zero global state** — all classes are instantiable; run multiple explorers (dual-pane, multi-tab) in one process
- **Interface-based** — swap `NativeFilesystem` for `MockFilesystem` in tests, or implement `ZipFilesystem`, `S3Filesystem`, etc.
- **Business logic ≠ I/O** — `filesystem.py` is a thin OS wrapper; `crud.py`, `copy_move.py` contain validation and policy
- **Command pattern** — all operations wrap as Command objects, enabling undo/redo, logging, and queuing

---

## How to Extend

### Add a custom filesystem backend

```python
from pathlib import Path
from file_explorer import FilesystemAbstraction

class ZipFilesystem(FilesystemAbstraction):
    def read_dir(self, path: Path) -> list[Path]:
        ...
    # implement all abstract methods
```

### Add a new command

```python
from file_explorer import Command, OperationResult

class CompressCommand(Command):
    def execute(self) -> OperationResult:
        ...
    def undo(self) -> OperationResult:
        ...
```

### Build a GUI

The entire public API is exported from `file_explorer`. Import and call:

```python
from file_explorer import (
    DirectoryNavigator,     # list_contents(), enter(), go_up(), history
    create_file,            # high-level CRUD
    copy_item,              # with conflict strategies
    search_by_name,         # with pattern, filters, max results
    get_metadata,           # size, dates, hidden, readonly
    OperationHistory,       # undo/redo stack
    ConfigManager,          # persistent settings
)
```

All operations return `OperationResult` (with `success`, `error`, `source`, `destination`) for UI feedback.

---

## Project Structure

```
file_explorer/
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── README.md
├── logs/                          # Runtime log output
├── docs/
│   ├── core-architecture.md
│   └── development-plan.md
├── src/
│   └── file_explorer/
│       ├── __init__.py             # Public API exports
│       ├── _logging.py             # Logger setup
│       ├── exceptions.py           # 9 exception classes
│       ├── path_utils.py           # 6 path functions
│       ├── filesystem.py           # ABC + NativeFilesystem
│       ├── directory.py            # DirectoryNavigator
│       ├── crud.py                 # 7 CRUD functions
│       ├── metadata.py             # FileMetadata + helpers
│       ├── copy_move.py            # Copy/move + batch
│       ├── search.py               # Search with pattern matching
│       ├── permissions.py          # PermissionManager + helpers
│       ├── commands.py             # 8 command classes + OperationHistory
│       └── config.py               # AppConfig + ConfigManager
└── tests/
    ├── conftest.py                 # MockFilesystem + fixtures
    ├── unit/                       # 10 test files (229 tests)
    └── integration/                # NativeFilesystem integration tests (36 tests)
```

---

## Dependencies

**Zero third-party dependencies for production.** All standard library:

`pathlib`, `shutil`, `fnmatch`, `json`, `logging`, `abc`, `enum`, `dataclasses`, `threading`, `typing`, `re`, `errno`, `os`, `stat`, `platform`, `sys`, `io`

Dev only: `pytest>=8.0`, `pytest-cov>=5.0`
