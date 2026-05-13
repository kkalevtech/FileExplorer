import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from file_explorer.exceptions import PermissionDeniedError
from file_explorer.filesystem import FilesystemAbstraction


@dataclass
class SearchResult:
    path: Path
    name: str
    score: float = 0.0


@dataclass
class SearchOptions:
    pattern: str
    root_path: Path | str
    recursive: bool = True
    case_sensitive: bool = False
    max_results: int = 1000
    include_hidden: bool = False
    file_filter: Optional[bool] = None


def _match_pattern(name: str, pattern: str, case_sensitive: bool) -> bool:
    if not case_sensitive:
        name = name.lower()
        pattern = pattern.lower()
    return fnmatch.fnmatch(name, pattern)


def _walk(
    fs: FilesystemAbstraction,
    path: Path,
    recursive: bool,
    include_hidden: bool,
    max_results: int,
) -> list[Path]:
    results: list[Path] = []

    try:
        entries = fs.read_dir(path)
    except (PermissionDeniedError, OSError):
        return results

    for entry in entries:
        if len(results) >= max_results:
            break
        if not include_hidden and entry.name.startswith("."):
            continue
        results.append(entry)
        if recursive and fs.is_dir(entry):
            results.extend(
                _walk(fs, entry, recursive, include_hidden, max_results - len(results))
            )
            if len(results) >= max_results:
                break

    return results


def search_by_name(
    fs: FilesystemAbstraction,
    options: SearchOptions,
) -> list[SearchResult]:
    root = Path(options.root_path).resolve()
    pattern = options.pattern if options.pattern else "*"

    entries = _walk(
        fs,
        root,
        recursive=options.recursive,
        include_hidden=options.include_hidden,
        max_results=options.max_results,
    )

    results: list[SearchResult] = []
    for entry in entries:
        if len(results) >= options.max_results:
            break

        if not _match_pattern(entry.name, pattern, options.case_sensitive):
            continue

        if options.file_filter is not None:
            if options.file_filter and not fs.is_file(entry):
                continue
            if not options.file_filter and not fs.is_dir(entry):
                continue

        results.append(SearchResult(path=entry, name=entry.name))

    return results
