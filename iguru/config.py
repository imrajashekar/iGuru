"""Shared configuration constants for iGuru."""

SUPPORTED_SUFFIXES = {
    ".c", ".cpp", ".cs", ".css", ".go", ".html", ".java", ".js", ".jsx",
    ".json", ".kt", ".md", ".php", ".py", ".rb", ".rs", ".scala", ".sql",
    ".ts", ".tsx", ".yaml", ".yml",
}
IGNORED_PARTS = {
    ".coach_sessions", ".git", ".idea", ".iguru_window.json", ".mypy_cache",
    ".pytest_cache", ".venv",
    ".vscode", "__pycache__", "build", "dist", "node_modules", "target", "venv",
}
MAX_FILE_BYTES = 80_000
HELP_HOTKEY = "<ctrl>+<alt>+h"
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_STUCK_AFTER = 120.0
DEFAULT_SCAN_INTERVAL = 1.0
MONITOR_MODES = ("file", "screen", "combined")
