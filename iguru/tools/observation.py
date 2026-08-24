"""Safe tools for inspecting limited local learning context."""

import ctypes

from strands import tool


@tool
def get_active_window() -> dict[str, str]:
    """Return the title of the foreground Windows application without capturing its screen."""
    user32 = ctypes.windll.user32
    handle = user32.GetForegroundWindow()
    if not handle:
        return {"status": "unavailable", "title": ""}
    length = user32.GetWindowTextLengthW(handle)
    title = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(handle, title, length + 1)
    return {"status": "ok", "title": title.value}
