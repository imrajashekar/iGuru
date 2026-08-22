"""Learner activity and possible-stuck detection."""

import time
from dataclasses import dataclass

from .events import EventQueue


@dataclass
class ActivityState:
    last_code_activity: float | None = None
    idle_prompt_sent: bool = False


def watch_for_stuck(events: EventQueue, state: ActivityState, stuck_after: float) -> None:
    while True:
        time.sleep(min(5.0, max(1.0, stuck_after / 4)))
        last_activity = state.last_code_activity
        if (
            last_activity is not None
            and not state.idle_prompt_sent
            and time.monotonic() - last_activity >= stuck_after
        ):
            state.idle_prompt_sent = True
            events.put(("screen", "automatic idle check"))
