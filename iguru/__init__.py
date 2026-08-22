"""Reusable building blocks for the iGuru learning assistant."""

from .activity import ActivityState, watch_for_stuck
from .coach import make_agent
from .events import EventQueue, FileChange
from .file_monitor import watch_files
from .prompts import file_prompt, screen_prompt
from .screen_monitor import capture_screen, listen_for_help_hotkey

__all__ = [
    "ActivityState", "EventQueue", "FileChange", "capture_screen", "file_prompt",
    "listen_for_help_hotkey", "make_agent", "screen_prompt", "watch_files",
    "watch_for_stuck",
]
