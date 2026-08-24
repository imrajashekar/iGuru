"""Strands tools exposed to the iGuru coaching agent."""

from .intervention import evaluate_intervention
from .learning import (
    get_learner_state,
    get_recent_attempts,
    get_recent_hints,
    record_attempt,
    record_hint,
    update_learner_state,
)
from .observation import get_active_window


IGURU_TOOLS = [
    get_active_window,
    get_learner_state,
    update_learner_state,
    record_attempt,
    get_recent_attempts,
    record_hint,
    get_recent_hints,
    evaluate_intervention,
]

__all__ = ["IGURU_TOOLS"]
