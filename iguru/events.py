"""Event data shared by iGuru's interfaces and monitors."""

from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from typing import TypeAlias


@dataclass(frozen=True)
class FileChange:
    path: Path
    content: str


Event: TypeAlias = tuple[str, object]
EventQueue: TypeAlias = Queue[Event]
