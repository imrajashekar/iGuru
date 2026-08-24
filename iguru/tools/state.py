"""Thread-safe in-memory learning state shared by iGuru tools."""

from collections import deque
from copy import deepcopy
from threading import RLock
from typing import Any


class LearningStateStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._profile: dict[str, Any] = {
            "task": "", "approach": "", "current_obstacle": "", "understanding": "",
        }
        self._attempts: deque[dict[str, Any]] = deque(maxlen=20)
        self._hints: deque[dict[str, Any]] = deque(maxlen=20)
        self._observations: deque[str] = deque(maxlen=20)

    def profile(self) -> dict[str, Any]:
        with self._lock:
            return {
                **deepcopy(self._profile),
                "attempt_count": len(self._attempts),
                "hint_count": len(self._hints),
                "recent_observations": list(self._observations)[-5:],
            }

    def update_profile(self, **values: str) -> dict[str, Any]:
        with self._lock:
            for key, value in values.items():
                if value.strip():
                    self._profile[key] = value.strip()
            return self.profile()

    def add_attempt(self, summary: str, outcome: str) -> dict[str, Any]:
        with self._lock:
            attempt = {"summary": summary.strip(), "outcome": outcome.strip()}
            self._attempts.append(attempt)
            return deepcopy(attempt)

    def attempts(self, limit: int) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(list(self._attempts)[-limit:])

    def add_hint(self, level: int, concept: str) -> dict[str, Any]:
        with self._lock:
            hint = {"level": level, "concept": concept.strip()}
            self._hints.append(hint)
            return deepcopy(hint)

    def hints(self, limit: int) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(list(self._hints)[-limit:])


learning_state = LearningStateStore()
