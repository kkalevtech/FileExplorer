import platform
import re
from pathlib import Path
from typing import Optional

from file_explorer.exceptions import InvalidPathError


def resolve_path(path: str | Path, base: Optional[Path] = None) -> Path:
    if not path or (isinstance(path, str) and not path.strip()):
        raise InvalidPathError("Path must not be empty", path=Path(path) if isinstance(path, str) else None)

    base = base or Path.cwd()
    resolved = Path(path).expanduser()

    if not resolved.is_absolute():
        resolved = (base / resolved).resolve()
    else:
        resolved = resolved.resolve()

    return resolved


def is_subpath(child: Path, parent: Path) -> bool:
    child_resolved = child.resolve()
    parent_resolved = parent.resolve()

    if child_resolved == parent_resolved:
        return False

    return parent_resolved in child_resolved.parents


def sanitize_filename(name: str) -> str:
    if platform.system() == "Windows":
        illegal = r'[<>:"/\\|?*\x00-\x1f]'
    else:
        illegal = r"[/\x00]"

    cleaned = re.sub(illegal, "", name)
    cleaned = cleaned.strip(". ")
    return cleaned


def unique_path(base: Path, name: str) -> Path:
    candidate = base / name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1

    while True:
        new_name = f"{stem} ({counter}){suffix}"
        candidate = base / new_name
        if not candidate.exists():
            return candidate
        counter += 1


def split_path_components(path: Path) -> list[str]:
    return list(path.parts)


def common_ancestor(paths: list[Path]) -> Path:
    if not paths:
        return Path()

    parts_list = [p.resolve().parts for p in paths]
    common = []
    for components in zip(*parts_list):
        if len(set(components)) == 1:
            common.append(components[0])
        else:
            break

    if not common:
        return Path()

    result = Path(common[0])
    for part in common[1:]:
        result = result / part

    return result
