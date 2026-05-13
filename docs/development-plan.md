# Development Plan — File Explorer Core Backend

> **Based on:** `docs/core-architecture.md`
> **Target:** Python 3.10+ backend implementation (no GUI)
> **Status:** Development roadmap

---

## 1. Project Initialization

### 1.1 Recommended Project Structure

```
file_explorer/
├── .venv/
├── .gitignore
├── .gitattributes
├── requirements.txt
├── pyproject.toml              # optional metadata (PEP 621)
├── README.md
├── logs/
│   └── file_explorer.log
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_path_utils.py
│   │   ├── test_filesystem_ops.py
│   │   ├── test_metadata.py
│   │   ├── test_search.py
│   │   ├── test_copy_move.py
│   │   ├── test_errors.py
│   │   ├── test_command_abstraction.py
│   │   └── test_config.py
│   └── integration/
│       ├── __init__.py
│       └── test_real_filesystem_ops.py
└── src/
    └── file_explorer/
        ├── __init__.py
        ├── _logging.py
        ├── exceptions.py
        ├── path_utils.py
        ├── filesystem.py          # abstraction layer
        ├── directory.py           # navigation
        ├── crud.py                # file/folder CRUD
        ├── metadata.py            # file metadata
        ├── copy_move.py           # copy + move operations
        ├── search.py              # search system
        ├── commands.py            # command / operation abstraction
        └── config.py              # configuration and preferences
```

### 1.2 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Package name | `snake_case` single word | `file_explorer` |
| Modules | `snake_case` | `path_utils.py`, `copy_move.py` |
| Classes | `PascalCase` | `FilesystemAbstraction`, `CopyCommand` |
| Functions/methods | `snake_case` | `resolve_path()`, `copy_item()` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT` |
| Private helpers | Prefixed `_` | `_normalize_separators()` |
| Test files | `test_<module>.py` | `test_path_utils.py` |
| Test classes | `Test<PascalCase>` | `TestPathUtils` |
| Test functions | `test_<scenario>` | `test_resolve_relative_path` |

### 1.3 Virtual Environment & Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate
```

**Dependency management rules:**
- Every external library must be declared in `requirements.txt`.
- Never `pip install` without updating `requirements.txt`.
- After adding a new dependency, run:
  ```bash
  pip freeze > requirements.txt
  ```
- Keep dependencies minimal — the entire core should only need:
  - `pathlib` (stdlib) for path handling
  - `shutil` (stdlib) for copy/move
  - `os` / `stat` (stdlib) for filesystem calls
  - `fnmatch` (stdlib) for search pattern matching
  - `json` (stdlib) for configuration
  - `logging` (stdlib) for structured logging
  - *(zero external dependencies for the core backend)*

**`requirements.txt` (initial):**

```
# Core backend has zero external dependencies.
# All dependencies are Python standard library modules.
# If a third-party library is added later, pin the version:
# e.g., pyyaml>=6.0
```

### 1.4 `.gitignore`

```
# Virtual environment
.venv/

# Python cache
__pycache__/
*.py[cod]
*.pyo

# Logs
logs/*.log

# OS files
Thumbs.db
.DS_Store

# IDE
.vscode/
.idea/

# Config overrides (if user-specific)
config_local.json
```

### 1.5 Logging Setup (`src/file_explorer/_logging.py`)

- Use Python's `logging` module with a format string:
  ```
  [%(asctime)s] %(levelname)-8s %(name)s:%(lineno)d — %(message)s
  ```
- Configure both a file handler (`logs/file_explorer.log`) and a console handler.
- Set default log level to `INFO`; switchable to `DEBUG` via configuration.
- Create a helper `get_logger(name)` that returns a child logger from the root `file_explorer` namespace.

### 1.6 Environment Setup Recommendations

- Python 3.10+ (use `pathlib` exclusively, avoid `os.path`).
- Use `pyproject.toml` with `[project.scripts]` if a CLI entry point is desired later.
- Set `PYTHONPATH=.` or install the package in editable mode:
  ```bash
  pip install -e .
  ```

---

## 2. Core Architecture Planning

### 2.1 Module Separation & Responsibilities

| Module | Responsibility |
|--------|---------------|
| `_logging.py` | Centralized logger configuration |
| `exceptions.py` | All custom exception classes |
| `path_utils.py` | Path parsing, normalization, resolution, platform adaptation |
| `filesystem.py` | Abstract interface + concrete implementation for raw FS calls |
| `directory.py` | Directory reading, tree walking, current-directory context |
| `crud.py` | Create/read/update/delete files and folders |
| `metadata.py` | Extract size, dates, attributes, type info |
| `copy_move.py` | Copy and move single/batch items with conflict handling |
| `search.py` | Name-based recursive search with pattern matching |
| `commands.py` | Command-pattern wrappers for all operations |
| `config.py` | Persistent JSON-based configuration storage |

### 2.2 Dependency Flow Between Modules

```
                     config.py
                        |
                        v
    path_utils.py --> filesystem.py (abstract interface)
                        |
            +-----------+-----------+-----------+-----------+
            |           |           |           |           |
            v           v           v           v           v
       directory.py  crud.py  metadata.py  copy_move.py  search.py
            |           |           |           |           |
            +-----------+-----------+-----------+-----------+
                        |
                        v
                  commands.py
                        |
                        v
                 (GUI / future layers)
```

- `path_utils.py` and `exceptions.py` are **dependency-free** (leaf modules).
- `filesystem.py` depends on `path_utils` and `exceptions`.
- All operation modules (`directory.py`, `crud.py`, `metadata.py`, `copy_move.py`, `search.py`) depend on `filesystem.py`, `path_utils.py`, and `exceptions.py`.
- `commands.py` depends on all operation modules.
- `config.py` is independent but consumed by any module needing settings.

### 2.3 Interface-Based Design

The `filesystem.py` module should define an abstract base class (ABC):

```python
class FilesystemAbstraction(ABC):
    @abstractmethod
    def read_dir(self, path: Path) -> list[Path]: ...
    @abstractmethod
    def create_file(self, path: Path) -> Path: ...
    @abstractmethod
    def create_dir(self, path: Path) -> Path: ...
    @abstractmethod
    def delete(self, path: Path) -> None: ...
    @abstractmethod
    def rename(self, src: Path, dst: Path) -> Path: ...
    @abstractmethod
    def copy(self, src: Path, dst: Path) -> Path: ...
    @abstractmethod
    def move(self, src: Path, dst: Path) -> Path: ...
    @abstractmethod
    def get_metadata(self, path: Path) -> dict: ...
    @abstractmethod
    def exists(self, path: Path) -> bool: ...
```

A concrete `NativeFilesystem` class implements this using `pathlib`/`shutil`.
A `MockFilesystem` class (in tests) implements the same interface in memory.

### 2.4 Separation of Business Logic from Filesystem Operations

- **Business logic** (e.g., "when copying, resolve conflict by appending `_copy`") lives in `copy_move.py`, **not** in `filesystem.py`.
- `filesystem.py` is a thin wrapper around OS calls — it does **not** contain policy decisions.
- All policy, validation, and orchestration lives in the operation modules (`crud.py`, `copy_move.py`, etc.).
- This separation makes the system testable: mock `filesystem.py` and test the business logic in isolation.

---

## 3. Step-by-Step Implementation Phases

---

### Phase 1: Project Skeleton & Exceptions

**Goal:** Establish the project scaffold, logging, and custom exception hierarchy.

**Files to create:**
- `src/file_explorer/__init__.py` — package init, expose public API
- `src/file_explorer/_logging.py` — `setup_logging()`, `get_logger()`
- `src/file_explorer/exceptions.py`
- `.gitignore`
- `requirements.txt`
- `tests/conftest.py`

**Exception classes (`exceptions.py`):**

| Exception | Parent | When raised |
|-----------|--------|------------|
| `FileExplorerError` | `Exception` | Base for all custom exceptions |
| `PathNotFoundError` | `FileExplorerError` | Path does not exist |
| `PermissionDeniedError` | `FileExplorerError` | Insufficient permissions |
| `FileAlreadyExistsError` | `FileExplorerError` | Destination already exists |
| `DiskFullError` | `FileExplorerError` | Not enough disk space |
| `FileInUseError` | `FileExplorerError` | File locked by another process |
| `InvalidPathError` | `FileExplorerError` | Malformed or illegal path |
| `OperationCancelledError` | `FileExplorerError` | Operation cancelled by caller |

**Validation strategy:**
- Each exception carries an optional `path: Path` attribute and `os_error: OSError | None`.
- Verify that `isinstance(e, FileExplorerError)` catches all custom exceptions.

**Refactoring checkpoint:**
- Ensure `from file_explorer.exceptions import *` is clean.
- Verify `setup_logging()` creates the `logs/` directory if missing.

---

### Phase 2: Path Utilities (`path_utils.py`)

**Goal:** Build all path manipulation logic in a single focused module with no external dependencies beyond `pathlib`.

**Classes / Functions:**

| Name | Signature | Purpose |
|------|-----------|---------|
| `resolve_path` | `(path: str \| Path, base: Path \| None = None) -> Path` | Resolve relative/absolute paths, expand `~`, normalize |
| `is_subpath` | `(child: Path, parent: Path) -> bool` | Check if child is inside parent (prevent traversal attacks) |
| `sanitize_filename` | `(name: str) -> str` | Strip illegal filename characters per platform |
| `unique_path` | `(base: Path, name: str) -> Path` | Append suffix if collision exists (e.g., `file (2).txt`) |
| `split_path_components` | `(path: Path) -> list[str]` | Return all path parts as strings |
| `common_ancestor` | `(paths: list[Path]) -> Path` | Find deepest common parent directory |

**Edge cases:**
- Paths with trailing slashes.
- Windows vs. POSIX separators (use `PurePath`/`Path` which are cross-platform).
- Empty string input → raise `InvalidPathError`.
- Paths containing `..` / `.` traversal.
- Long paths on Windows (`\\?\` prefix consideration — document but do not auto-apply).
- Unicode characters in filenames.

**Recommended functions/methods** (keep as module-level functions, not a class — `path_utils` is a utility module).

**Testing (`tests/unit/test_path_utils.py`):**
- `test_resolve_absolute` — absolute string returned as-is
- `test_resolve_relative` — relative resolved against base
- `test_resolve_home` — `~` expanded
- `test_is_subpath_true` / `test_is_subpath_false`
- `test_is_subpath_equal` — a path is NOT a subpath of itself
- `test_sanitize_removes_illegal_chars`
- `test_unique_path_no_collision`
- `test_unique_path_with_collision` — file exists, appends ` (1)`
- `test_split_path_components`
- `test_common_ancestor`
- `test_invalid_path_raises`

---

### Phase 3: Filesystem Abstraction Layer (`filesystem.py`)

**Goal:** Define `FilesystemAbstraction` (ABC) and implement `NativeFilesystem`.

**Classes:**

| Class | Type | Purpose |
|-------|------|---------|
| `FilesystemAbstraction` | ABC | Contract for all FS operations |
| `NativeFilesystem` | Concrete | Real `pathlib`/`shutil` implementation |

**`NativeFilesystem` methods:**

| Method | Delegates to | Raises |
|--------|-------------|--------|
| `read_dir(path)` | `path.iterdir()` | `PathNotFoundError`, `PermissionDeniedError` |
| `read_dir_recursive(path)` | `path.rglob('*')` | Same as above |
| `create_file(path)` | `path.touch()` | `InvalidPathError`, `PermissionDeniedError` |
| `create_dir(path)` | `path.mkdir(parents=True)` | Same as above |
| `delete_file(path)` | `path.unlink()` | `PathNotFoundError`, `PermissionDeniedError`, `FileInUseError` |
| `delete_dir(path)` | `path.rmdir()` (empty) or `shutil.rmtree` (recursive) | Same as above |
| `rename(src, dst)` | `src.rename(dst)` | `PathNotFoundError`, `FileAlreadyExistsError` |
| `copy_file(src, dst)` | `shutil.copy2(src, dst)` | Same as above |
| `copy_dir(src, dst)` | `shutil.copytree(src, dst)` | Same as above |
| `move(src, dst)` | `shutil.move(src, dst)` | Same as above |
| `get_metadata(path)` | `path.stat()`, `path.lstat()` | `PathNotFoundError` |
| `exists(path)` | `path.exists()` | Never raises |
| `is_file(path)` | `path.is_file()` | Never raises |
| `is_dir(path)` | `path.is_dir()` | Never raises |
| `get_permissions(path)` | `oct(path.stat().st_mode)` | `PathNotFoundError`, `PermissionDeniedError` |

**Implementation notes:**
- All public methods catch `OSError` / `PermissionError` / `FileNotFoundError` and re-raise as the corresponding `FileExplorerError` subclass.
- Use `pathlib.Path` exclusively — never `os.path`.
- `copy_dir` should accept an `ignore_patterns: set[str]` parameter for future use.
- `NativeFilesystem.__init__` accepts an optional `logger` parameter.

**Testing (`tests/unit/test_filesystem.py`):**
- Test through a `MockFilesystem` (Phase 5+) and also test `NativeFilesystem` against a temporary directory (via `tmp_path` fixture).
- `test_read_dir_returns_paths`
- `test_create_file_creates_file`
- `test_create_dir_creates_directory`
- `test_delete_file_removes_file`
- `test_delete_dir_removes_directory`
- `test_rename_updates_path`
- `test_read_dir_nonexistent_raises`
- `test_create_file_existing_does_not_overwrite` (touch by default does not truncate)

**Refactoring checkpoint:**
- Verify `NativeFilesystem` implements every abstract method.
- Ensure every `OSError` is translated to a `FileExplorerError`.

---

### Phase 4: Directory Navigation (`directory.py`)

**Goal:** Manage current-directory context and directory listing.

**Classes:**

| Class | Purpose |
|-------|---------|
| `DirectoryNavigator` | Tracks current directory, provides navigation methods |

**`DirectoryNavigator` methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__` | `(fs: FilesystemAbstraction, start_dir: Path \| str)` | Initialize at `start_dir` |
| `current` | `-> Path` (property) | Returns current directory |
| `list_contents` | `(show_hidden: bool = False) -> list[Path]` | Returns sorted contents of current directory |
| `enter` | `(name: str \| Path) -> Path` | Navigate into subdirectory |
| `go_up` | `-> Path` | Navigate to parent directory |
| `go_to` | `(path: Path \| str) -> Path` | Navigate to an arbitrary directory |
| `refresh` | `-> list[Path]` | Re-read current directory contents |
| `get_history` | `-> list[Path]` | Return navigation history |
| `go_back` | `-> Path \| None` | Pop last location from history |
| `root` | `-> Path` (property) | Drive root or `/` |

**Edge cases:**
- `enter` on a file → raise `NotADirectoryError` (wrapped in `FileExplorerError`).
- `go_up` at filesystem root → return root (no error).
- `go_to` a non-existent path → raise `PathNotFoundError`.
- `History` should not grow unbounded — cap at 100 entries.

**Dependencies:** `filesystem.py`, `path_utils.py`, `exceptions.py`.

**Testing (`tests/unit/test_directory.py`):**
- Use `MockFilesystem` (from Phase 5) to avoid real FS calls.
- `test_current_starts_at_correct_dir`
- `test_list_contents_returns_sorted`
- `test_list_contents_hidden_excluded`
- `test_enter_subdirectory`
- `test_enter_file_raises`
- `test_go_up`
- `test_go_up_at_root`
- `test_go_to_absolute`
- `test_history_tracks_navigation`
- `test_go_back_restores_previous`
- `test_refresh_returns_current`

---

### Phase 5: Mock Filesystem (Test Infrastructure)

**Goal:** Build `MockFilesystem` — an in-memory implementation of `FilesystemAbstraction` for unit testing.

**Class:**

| Class | Purpose |
|-------|---------|
| `MockFilesystem` | In-memory tree of `MockEntry` objects implementing `FilesystemAbstraction` |

**Internal helpers:**
- `MockEntry` — simple dataclass with `name`, `is_dir`, `content`, `children`, `metadata`.
- `_resolve(path)` — traverse internal tree from root.
- `_enforce_permissions(path)` — simulate permission errors via a set of restricted paths.

**Why this matters:**
- Tests run at RAM speed (no I/O).
- Tests are deterministic and cross-platform.
- Failure scenarios (permission denied, disk full) are trivial to simulate.

**Location:** `tests/conftest.py` (fixture `mock_fs`).

---

### Phase 6: File/Folder CRUD Operations (`crud.py`)

**Goal:** High-level create/read/update/delete operations with business logic (validation, conflict resolution, recursion control).

**Classes/Functions:**

| Name | Signature | Description |
|------|-----------|-------------|
| `create_file` | `(fs, path, overwrite=False) -> Path` | Create file, optionally overwrite |
| `create_directory` | `(fs, path, exist_ok=False) -> Path` | Create directory tree |
| `read_file_content` | `(fs, path, mode='text') -> str \| bytes` | Read file content |
| `write_file_content` | `(fs, path, content, mode='text') -> Path` | Write content to file |
| `rename_item` | `(fs, src, dst, overwrite=False) -> Path` | Rename or move item |
| `delete_item` | `(fs, path, recursive=False) -> None` | Delete file or empty dir; `recursive` for non-empty dirs |
| `duplicate_item` | `(fs, path) -> Path` | Smart duplicate (appends " — Copy") |

**Edge cases:**
- `delete_item` on non-empty dir without `recursive=True` → raise error with a clear message.
- `create_file` where parent directory does not exist → raise `PathNotFoundError` (do NOT auto-create parents — that is the caller's explicit choice).
- `rename_item` across filesystem boundaries → copy + delete fallback raises `FileExplorerError` with suggestion to use `copy_move` module.

**Dependencies:** `filesystem.py`, `path_utils.py`, `exceptions.py`.

**Testing:**
- `test_create_file_new`
- `test_create_file_existing_no_overwrite`
- `test_create_file_existing_overwrite`
- `test_create_directory_creates_parents`
- `test_create_directory_existing_ok`
- `test_read_file_content_text`
- `test_write_file_content`
- `test_delete_file`
- `test_delete_dir_empty`
- `test_delete_dir_nonempty_no_recursive_raises`
- `test_delete_dir_nonempty_recursive`
- `test_rename_item`
- `test_duplicate_item_appends_copy`

---

### Phase 7: Metadata Retrieval (`metadata.py`)

**Goal:** Extract and format file/folder metadata into a consistent dictionary.

**Classes/Functions:**

| Name | Signature | Description |
|------|-----------|-------------|
| `FileMetadata` | dataclass | `size`, `created`, `modified`, `accessed`, `extension`, `is_dir`, `is_file`, `is_symlink`, `is_hidden`, `is_readonly`, `permissions` |
| `get_metadata` | `(fs, path) -> FileMetadata` | Collect all metadata |
| `get_size_formatted` | `(size: int) -> str` | Human-readable size ("1.2 MB") |
| `get_extension` | `(path: Path) -> str` | Lowercase extension without dot |
| `is_hidden` | `(path: Path) -> bool` | Dot-prefix on Unix, `FILE_ATTRIBUTE_HIDDEN` on Windows |
| `is_readonly` | `(path: Path) -> bool` | Read-only attribute check |

**Edge cases:**
- Symlinks — distinguish link target metadata vs. link itself.
- Broken symlinks — `FileMetadata.is_symlink=True`, other fields may be unavailable; do not raise.
- Zero-byte files — valid, size = 0.
- Directories — size is 0 or platform-specific (document the choice: 0).
- Permission-denied paths — raise `PermissionDeniedError` instead of returning partial data.

**Testing:**
- `test_get_metadata_file`
- `test_get_metadata_directory`
- `test_get_metadata_hidden_file`
- `test_get_metadata_symlink`
- `test_get_metadata_broken_symlink`
- `test_get_size_formatted_bytes`
- `test_get_size_formatted_kb`
- `test_get_size_formatted_mb`
- `test_get_extension_no_extension`
- `test_is_hidden_dotfile` / `test_is_hidden_windows_attribute`

---

### Phase 8: Copy & Move Operations (`copy_move.py`)

**Goal:** Implement robust copy/move with conflict resolution, progress reporting, and batch support.

**Classes/Functions:**

| Name | Signature | Description |
|------|-----------|-------------|
| `ConflictStrategy` | Enum | `SKIP`, `OVERWRITE`, `RENAME`, `ASK` |
| `OperationResult` | dataclass | `source`, `destination`, `success`, `error: str \| None` |
| `copy_item` | `(fs, src, dst, strategy=OVERWRITE) -> OperationResult` | Copy file or directory |
| `move_item` | `(fs, src, dst, strategy=OVERWRITE) -> OperationResult` | Move file or directory |
| `batch_copy` | `(fs, items: list[tuple[Path, Path]], strategy) -> list[OperationResult]` | Batch copy |
| `batch_move` | `(fs, items: list[tuple[Path, Path]], strategy) -> list[OperationResult]` | Batch move |

**Conflict resolution logic (`_resolve_conflict`):**
- `OVERWRITE`: replace destination unconditionally.
- `SKIP`: skip silently.
- `RENAME`: call `unique_path` to generate alternative name.
- `ASK`: raise `FileAlreadyExistsError` so the caller (or future GUI) can decide.

**Progress reporting:**
- All long-running operations accept an optional `progress_callback: Callable[[int, int], None]` — called with `(completed, total)`.

**Edge cases:**
- Copying a file onto itself → raise `InvalidOperationError` (new exception or reuse `FileExplorerError`).
- Moving across drives → `shutil.move` handles it, but document that it is a copy+delete internally.
- Destination is an existing directory → append source filename.
- Source is a directory and destination is a file → raise.
- Very long path names on Windows.
- Cancellation support via an optional `cancellation_token: threading.Event`.

**Testing:**
- `test_copy_file_to_new_location`
- `test_copy_file_overwrite`
- `test_copy_file_skip`
- `test_copy_file_rename_on_conflict`
- `test_copy_directory_recursive`
- `test_move_file`
- `test_move_directory`
- `test_batch_copy_returns_results`
- `test_copy_same_source_destination_raises`
- `test_copy_with_progress_callback`
- `test_move_cross_drive` (mock shutil.move)

---

### Phase 9: Search System (`search.py`)

**Goal:** Recursive name-based search with pattern matching.

**Classes/Functions:**

| Name | Signature | Description |
|------|-----------|-------------|
| `SearchResult` | dataclass | `path`, `name`, `score: float` (for future ranking) |
| `SearchOptions` | dataclass | `pattern`, `root_path`, `recursive=True`, `case_sensitive=False`, `max_results=1000`, `include_hidden=False`, `file_filter: Optional[bool]` (None=both, True=files only, False=dirs only) |
| `search_by_name` | `(fs, options: SearchOptions) -> list[SearchResult]` | Main search entry point |
| `_match_pattern` | `(name, pattern, case_sensitive) -> bool` | Pattern matching via `fnmatch` |

**Search algorithm:**
1. Start at `root_path`.
2. Walk recursively (or non-recursively if `recursive=False`).
3. For each entry, apply `_match_pattern` to the filename.
4. Apply additional filters (`include_hidden`, `file_filter`).
5. Collect up to `max_results` results.
6. Return sorted by path.

**Edge cases:**
- Pattern is empty → return all entries (with max_results cap).
- Pattern with glob wildcards (`*`, `?`, `[seq]`) — use `fnmatch.filter`.
- Symlinks — follow or not? (Document choice: do NOT follow, match link name.)
- Permission denied on subdirectories during recursive walk → skip that subtree, log warning, continue.
- Extremely deep directory trees → set a recursion limit or document that caller should set `recursive=False`.

**Testing:**
- `test_search_exact_match`
- `test_search_wildcard`
- `test_search_case_insensitive`
- `test_search_recursive`
- `test_search_non_recursive`
- `test_search_hidden_excluded_by_default`
- `test_search_max_results`
- `test_search_empty_pattern`
- `test_search_no_matches`
- `test_search_skip_permission_denied`

---

### Phase 10: Error Handling & Permission Management

**Goal:** Ensure all modules raise consistent, typed exceptions and provide utilities for permission introspection.

**Already covered by** `exceptions.py` and the exception-translation in `filesystem.py`.

**Additional work:**

1. **`PermissionManager` class** in `exceptions.py` or a new `permissions.py`:

| Method | Signature | Description |
|--------|-----------|-------------|
| `check_readable` | `(path: Path) -> bool` | Test read access |
| `check_writable` | `(path: Path) -> bool` | Test write access |
| `check_executable` | `(path: Path) -> bool` | Test execute access (directories) |
| `is_system_protected` | `(path: Path) -> bool` | Platform-specific protected paths |
| `get_accessible_descendants` | `(root: Path) -> list[Path]` | Return only accessible items under root |

2. **Error categorization:**
   - `is_retryable(e: FileExplorerError) -> bool` — True for `FileInUseError`, `DiskFullError`; False for `PathNotFoundError`.
   - `user_friendly_message(e: FileExplorerError) -> str` — maps exceptions to human-readable strings.

3. **Protected paths (per platform):**
   - Windows: `C:\Windows`, `C:\Program Files`, `C:\System Volume Information`.
   - Linux: `/proc`, `/sys`, `/dev`, `/boot`.
   - macOS: `/System`, `/Library`.

**Testing:**
- `test_check_readable_existing_file`
- `test_check_writable_readonly_file`
- `test_check_writable_directory`
- `test_is_system_protected_windows`
- `test_is_system_protected_linux`
- `test_is_retryable_correct_categories`

---

### Phase 11: Command / Operation Abstraction (`commands.py`)

**Goal:** Wrap every operation as a command object with `execute()`, `undo()`, and metadata.

**Base class:**

```python
class Command(ABC):
    description: str
    timestamp: datetime

    @abstractmethod
    def execute(self) -> OperationResult: ...
    @abstractmethod
    def undo(self) -> OperationResult: ...
```

**Concrete commands:**

| Class | Wraps | Undo behavior |
|-------|-------|---------------|
| `CreateFileCommand` | `crud.create_file` | Delete the created file |
| `CreateDirectoryCommand` | `crud.create_directory` | Delete the created directory |
| `DeleteFileCommand` | `crud.delete_item` | **Cannot undo** (store warning) |
| `DeleteDirectoryCommand` | `crud.delete_item` | **Cannot undo** (store warning) |
| `RenameCommand` | `crud.rename_item` | Reverse rename |
| `CopyCommand` | `copy_move.copy_item` | Delete the copy |
| `MoveCommand` | `copy_move.move_item` | Move back to source |
| `BatchCommand` | list of `Command` | Executes all, then undoes in reverse |

**`OperationHistory` class:**

| Method | Description |
|--------|-------------|
| `push(command)` | Add command to history |
| `undo()` | Undo last command |
| `redo()` | Re-undo last undone command |
| `clear()` | Clear all history |
| `can_undo` / `can_redo` | Properties |
| `limit` | Configurable max history size (default 50) |

**Edge cases:**
- `undo()` when history is empty → no-op, return `None`.
- Delete commands cannot be undone → store a `cannot_undo=True` flag; `undo()` raises `OperationCannotUndoError`.
- Commands on paths that have been deleted since → catch and wrap as warning.
- `BatchCommand` partial failure → report per-item results, do not roll back automatically (caller decides).

**Testing:**
- `test_create_file_command_execute`
- `test_create_file_command_undo`
- `test_rename_command_undo`
- `test_delete_command_cannot_undo`
- `test_history_push_and_undo`
- `test_history_redo`
- `test_history_limit`
- `test_batch_command_execute_all`
- `test_batch_command_partial_failure`
- `test_undo_empty_history`

---

### Phase 12: Configuration & Preferences Storage (`config.py`)

**Goal:** Persistent, JSON-based configuration with typed access.

**Classes/Functions:**

| Name | Signature | Description |
|------|-----------|-------------|
| `AppConfig` | dataclass | All config fields with defaults |
| `ConfigManager` | class | Load/save/get/set configuration |
| `default_config_path` | `() -> Path` | Platform-specific config dir |
| `load_config` | `(path: Path \| None) -> AppConfig` | Load from JSON file |
| `save_config` | `(config: AppConfig, path: Path) -> None` | Save to JSON file |

**`AppConfig` fields (all with defaults):**

```
start_directory: str = "~"
show_hidden_files: bool = False
default_conflict_strategy: str = "rename"
max_history: int = 50
max_search_results: int = 1000
log_level: str = "INFO"
language: str = "en"
theme: str = "system"         # reserved for GUI
```

**`ConfigManager` methods:**

| Method | Description |
|--------|-------------|
| `get(key)` | Return typed value |
| `set(key, value)` | Update value, auto-save |
| `reset_to_defaults()` | Reset all to defaults |
| `get_path()` | Return config file path |

**Storage details:**
- Config file location (platform-standard):
  - Windows: `%APPDATA%/file_explorer/config.json`
  - macOS: `~/Library/Application Support/file_explorer/config.json`
  - Linux: `~/.config/file_explorer/config.json`
- File format: JSON with indentation for readability.
- Atomic writes: write to `.tmp` then rename to prevent corruption.

**Edge cases:**
- Config file does not exist → return defaults silently.
- Config file is corrupted (invalid JSON) → back up to `config.json.corrupt`, return defaults, log warning.
- Unknown keys in config file → ignore and preserve on save (future-proofing).

**Testing:**
- `test_load_config_defaults_when_missing`
- `test_load_config_custom_values`
- `test_save_config_creates_file`
- `test_set_and_get`
- `test_reset_to_defaults`
- `test_corrupted_config_falls_back_to_defaults`
- `test_platform_specific_config_path`

---

## 4. Testing Strategy

### 4.1 Unit Testing

- **Framework:** `pytest` (install via `requirements.txt` only for dev).
- **Runner:** `pytest tests/unit/` — must pass without real filesystem access.
- **Coverage target:** >90% for all core modules.
- **Fixtures:** Use `conftest.py` for shared fixtures:
  - `mock_fs` — `MockFilesystem` instance pre-populated with a standard tree.
  - `temp_dir` — `tmp_path` fixture for `NativeFilesystem` integration tests.
  - `sample_config` — `AppConfig` with test values.

**Test file mapping:**

| Test file | Module under test |
|-----------|------------------|
| `tests/unit/test_path_utils.py` | `path_utils.py` |
| `tests/unit/test_filesystem.py` | `filesystem.py` (NativeFilesystem + MockFilesystem) |
| `tests/unit/test_directory.py` | `directory.py` |
| `tests/unit/test_crud.py` | `crud.py` |
| `tests/unit/test_metadata.py` | `metadata.py` |
| `tests/unit/test_copy_move.py` | `copy_move.py` |
| `tests/unit/test_search.py` | `search.py` |
| `tests/unit/test_errors.py` | `exceptions.py`, `permissions.py` |
| `tests/unit/test_command_abstraction.py` | `commands.py` |
| `tests/unit/test_config.py` | `config.py` |

### 4.2 Integration Testing (`tests/integration/`)

- Test `NativeFilesystem` against real temporary directories (use `tmp_path`).
- Test cross-operation workflows: create → write → read → copy → delete.
- Test permission-related scenarios:
  - Create a read-only file, attempt delete → verify `PermissionDeniedError`.
  - Create a file, lock it, attempt delete → verify `FileInUseError`.
  - (Use platform-specific tools like `icacls` on Windows or `chmod` on Unix.)

### 4.3 Mocking Filesystem Operations

- `MockFilesystem` lives in `tests/conftest.py` and implements the same `FilesystemAbstraction` interface.
- All unit tests (except `test_filesystem.py` itself) should use `MockFilesystem`.
- `MockFilesystem` must support:
  - Simulating permission errors (via a configurable set of restricted paths).
  - Simulating disk-full errors (via a configurable capacity limit).
  - Simulating `FileInUseError` (via a configurable set of locked paths).
  - Fast in-memory tree operations.
- `MockFilesystem` must be reset between tests (use a fixture with `yield` and re-initialize).

### 4.4 Edge-Case Testing Checklist

| Scenario | Module | Expected behavior |
|----------|--------|------------------|
| Empty filename | `path_utils` | Raise `InvalidPathError` |
| Path with null byte | `path_utils` | Raise `InvalidPathError` |
| Extremely deep nesting | `search` | Respect recursion limit or timeout |
| Concurrent delete during iteration | `directory` | Return snapshot, not live view |
| Unicode filename (Japanese, emoji) | `filesystem` | Handle correctly on all platforms |
| 0-byte file copy | `copy_move` | Copy succeeds, result has 0 bytes |
| Copy file to itself | `copy_move` | Raise `FileExplorerError` |
| Network path | `path_utils` | Treat as valid UNC path on Windows |
| Max path length (260+ chars Windows) | `filesystem` | Document limitation, test boundary |
| Config file locked | `config` | Log warning, use in-memory defaults |
| Search with `*` only | `search` | Return all entries (capped) |

### 4.5 Cross-Platform Testing Considerations

- Run the test suite on **Windows**, **macOS**, and **Linux** via CI (GitHub Actions).
- Use `sys.platform` / `platform.system()` for platform-specific test branches.
- Platform-specific behaviors to test:
  - Windows: hidden attribute (`FILE_ATTRIBUTE_HIDDEN`), read-only, case-insensitive paths.
  - macOS: case-insensitive but preserving HFS+/APFS, `.DS_Store` handling.
  - Linux: case-sensitive, symlinks, sticky bit, `/proc` special files.
- Tests that require platform-specific features (e.g., Windows ACLs) should be marked with `@pytest.mark.skipif`.

---

## 5. Dependency Management

### 5.1 Adding Dependencies

1. Research necessity — can the feature be implemented with stdlib?
2. If a third-party library is unavoidable:
   - Add it to `requirements.txt` with a pinned major version: `library>=X.Y`.
   - Run `pip install library && pip freeze > requirements.txt` to lock all transitive deps.
   - Document why it was added as a comment: `# needed for YAML config support`.
3. Run the full test suite to verify nothing is broken.

### 5.2 Maintaining `requirements.txt`

- Keep it at the project root.
- Group by purpose with section comments:
  ```
  # === Core (production) ===
  # (none — all stdlib)

  # === Development ===
  pytest>=8.0
  pytest-cov>=5.0
  ```
- Update whenever a dependency changes.
- Do NOT commit `.venv/` or `pip freeze` detritus from unrelated packages.

### 5.3 Installing Dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate
pip install -r requirements.txt
```

### 5.4 Keeping Dependencies Minimal

- The core backend should target **zero third-party dependencies**.
- `pathlib`, `shutil`, `fnmatch`, `json`, `logging`, `abc`, `enum`, `dataclasses`, `threading`, `typing` — all stdlib.
- If `pytest` is needed, declare it in `requirements.txt` under a `# Development` section.
- Avoid pulling in large frameworks (Django, Flask, click) — the core is not a web app.

---

## 6. Git and Branch Workflow Recommendations

### 6.1 Branch Naming

```
feature/<module>-<short-description>
fix/<module>-<short-description>
refactor/<module>-<short-description>
```

Examples:
- `feature/crud-batch-operations`
- `fix/search-unicode-patterns`
- `refactor/path-utils-normalization`

### 6.2 Clean Commit Practices

- **One logical change per commit.** Do not mix formatting changes with logic changes.
- **Write descriptive commit messages:**
  ```
  crud: add overwrite flag to create_file
  
  - create_file now accepts overwrite=False by default
  - raises FileAlreadyExistsError when file exists and overwrite=False
  - updated tests to cover both paths
  ```
- Use conventional commit prefixes: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`.
- Keep commits small and focused — if a change touches 10 files across 5 modules, split it.

### 6.3 Safe Extension Workflow

1. Core modules (Phases 1–12) are developed on `main` with strict review.
2. Future developers create feature branches from `main`.
3. Each branch should only touch its own module + the `.py` files it depends on.
4. If a branch needs to modify a core module, file a discussion/proposal first.
5. `FilesystemAbstraction` is the **contract** — do not break it once established.

### 6.4 Merge Conflict Reduction

- Assign module ownership:
  - Developer A: `directory.py`, `crud.py`, `copy_move.py`
  - Developer B: `metadata.py`, `search.py`, `commands.py`
  - Developer C: `path_utils.py`, `filesystem.py`, `config.py`, `exceptions.py`
- Avoid editing the same file in parallel branches.
- Use `__init__.py` to expose a clean public API — internal renames do not affect consumers.

---

## 7. Future Expansion Notes

### 7.1 Intentionally Extensible Parts

| Component | Extension mechanism | Examples |
|-----------|--------------------|----------|
| `FilesystemAbstraction` | Subclass for new backends | `ZipFilesystem`, `S3Filesystem`, `FTPFilesystem` |
| `Command` | Subclass for new operations | `CompressCommand`, `EncryptCommand`, `BatchRenameCommand` |
| `ConfigManager` | Extend `AppConfig` dataclass | Add fields without breaking existing consumers |
| `SearchOptions` | Add fields | Add `content_search`, `date_filter`, `size_filter` |
| `ConflictStrategy` | Add enum members | Add `MERGE`, `KEEP_BOTH`, `REPLACE_OLDER` |

### 7.2 GUI Integration Points

| Backend component | GUI will consume via |
|-------------------|---------------------|
| `DirectoryNavigator` | `list_contents()`, `enter()`, `go_up()`, `current` property |
| `crud.*` | Direct function calls wrapped in `Command` objects |
| `metadata.get_metadata` | Display in list views, property dialogs, sort keys |
| `search_by_name` | Search bar, results panel |
| `batch_copy` / `batch_move` | Drag-and-drop, clipboard operations |
| `OperationHistory` | Undo/redo toolbar buttons |
| `ConfigManager` | Settings/preferences dialog |
| `Command.execute()` | All user-initiated actions pass through here |
| `OperationResult` | UI feedback (success toasts, error dialogs) |

**Integration principle:** The GUI imports from `src.file_explorer` and calls public functions / instantiates public classes. It never accesses internals (modules prefixed with `_`).

### 7.3 Architectural Decisions Supporting Scalability

1. **Interface-based filesystem abstraction** — swapping the storage backend requires zero changes to business logic.
2. **Command pattern** — enables undo/redo, operation queuing, logging, macro recording, and batch execution without modifying operation code.
3. **Separation of policy from mechanism** — `filesystem.py` does raw I/O; `crud.py` and `copy_move.py` contain business rules. Changes to policy never touch the abstraction layer.
4. **Typed configuration** — `AppConfig` dataclass allows IDE autocompletion and compile-time field validation.
5. **No global state** — `FilesystemAbstraction`, `DirectoryNavigator`, `ConfigManager`, and `OperationHistory` are all instantiable objects. Multiple instances can coexist (e.g., dual-pane file managers).
6. **Exception hierarchy** — GUI can catch `FileExplorerError` for generic error handling and specific subclasses for custom behavior.
7. **Callback-based progress reporting** — the core emits progress; the GUI decides how to render it (progress bar, spinner, silent background).

---

## Summary of Implementation Order

| Phase | Module | Depends on | Approximate effort |
|-------|--------|-----------|-------------------|
| 1 | Project skeleton, logging, exceptions | — | Small |
| 2 | `path_utils.py` | Phase 1 | Small |
| 3 | `filesystem.py` (ABC + Native) | Phases 1–2 | Medium |
| 4 | `directory.py` | Phases 1–3 | Medium |
| 5 | `MockFilesystem` (test infra) | Phase 3 | Small |
| 6 | `crud.py` | Phases 1–3, 5 | Medium |
| 7 | `metadata.py` | Phases 1–3 | Small |
| 8 | `copy_move.py` | Phases 1–3, 5 | Medium |
| 9 | `search.py` | Phases 1–3, 5 | Medium |
| 10 | Error handling, permission manager | Phases 1–3 | Small |
| 11 | `commands.py` | Phases 1–10 | Medium |
| 12 | `config.py` | Phase 1 | Small |

**Total estimated effort:** 12 phases, approximately 10–15 focused development sessions for a small team.
