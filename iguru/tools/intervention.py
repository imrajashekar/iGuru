"""A deterministic guardrail for deciding how strongly iGuru should intervene."""

from strands import tool


@tool
def evaluate_intervention(
    reason: str,
    repeated_failure_count: int = 0,
    idle_seconds: int = 0,
    learner_requested_help: bool = False,
) -> dict:
    """Recommend silence, permission, or a small hint from observable intervention signals."""
    if learner_requested_help:
        action = "give_small_hint"
    elif repeated_failure_count >= 3:
        action = "ask_permission"
    elif idle_seconds >= 300:
        action = "check_in"
    else:
        action = "remain_silent"
    return {
        "action": action,
        "reason": reason,
        "signals": {
            "repeated_failure_count": max(0, repeated_failure_count),
            "idle_seconds": max(0, idle_seconds),
            "learner_requested_help": learner_requested_help,
        },
    }
