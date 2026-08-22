"""Read-only monitoring of the learner's local practice files."""

import time
from pathlib import Path

from .config import IGNORED_PARTS, MAX_FILE_BYTES, SUPPORTED_SUFFIXES
from .events import EventQueue, FileChange


def is_coachable_file(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_SUFFIXES and not any(
        part in IGNORED_PARTS for part in path.parts
    )


def snapshot(root: Path) -> dict[Path, int]:
    result: dict[Path, int] = {}
    for path in root.rglob("*"):
        try:
            if path.is_file() and is_coachable_file(path) and path.stat().st_size <= MAX_FILE_BYTES:
                result[path] = path.stat().st_mtime_ns
        except (OSError, PermissionError):
            continue
    return result


def read_change(path: Path) -> FileChange | None:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return FileChange(path=path, content=content)


def watch_files(root: Path, events: EventQueue, interval: float) -> None:
    known = snapshot(root)
    while True:
        time.sleep(interval)
        current = snapshot(root)
        for path, modified in current.items():
            if known.get(path) != modified:
                change = read_change(path)
                if change:
                    events.put(("change", change))
        known = current
