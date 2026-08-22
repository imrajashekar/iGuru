"""On-demand screen capture and the global help shortcut."""

import mss
import mss.tools
from pynput import keyboard

from .config import HELP_HOTKEY
from .events import EventQueue


def listen_for_help_hotkey(events: EventQueue) -> None:
    try:
        hotkeys = {HELP_HOTKEY: lambda: events.put(("screen", "help hotkey"))}
        with keyboard.GlobalHotKeys(hotkeys) as listener:
            listener.join()
    except Exception as exc:
        events.put(("notice", f"Global hotkey unavailable: {exc}. Use /screen instead."))


def capture_screen(monitor_number: int) -> bytes:
    with mss.mss() as screens:
        if monitor_number < 1 or monitor_number >= len(screens.monitors):
            available = max(0, len(screens.monitors) - 1)
            raise ValueError(f"monitor {monitor_number} does not exist ({available} available)")
        shot = screens.grab(screens.monitors[monitor_number])
        return mss.tools.to_png(shot.rgb, shot.size)
