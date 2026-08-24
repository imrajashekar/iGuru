"""Tools used by the coach to maintain compact learning context."""

from strands import tool

from .state import learning_state


@tool
def get_learner_state() -> dict:
    """Get the current task, approach, obstacle, understanding, and recent observations."""
    return learning_state.profile()


@tool
def update_learner_state(
    task: str = "", approach: str = "", current_obstacle: str = "", understanding: str = "",
) -> dict:
    """Update only learning facts supported by the current conversation or observation."""
    return learning_state.update_profile(
        task=task,
        approach=approach,
        current_obstacle=current_obstacle,
        understanding=understanding,
    )


@tool
def record_attempt(summary: str, outcome: str = "") -> dict:
    """Record a meaningful learner attempt and its visible outcome to avoid repetitive advice."""
    if not summary.strip():
        raise ValueError("summary cannot be empty")
    return learning_state.add_attempt(summary, outcome)


@tool
def get_recent_attempts(limit: int = 5) -> list[dict]:
    """Return recent learner attempts, newest last."""
    return learning_state.attempts(max(1, min(limit, 10)))


@tool
def record_hint(level: int, concept: str) -> dict:
    """Record a delivered hint so later guidance can progress without repeating it."""
    if level < 1 or level > 4:
        raise ValueError("level must be between 1 and 4")
    if not concept.strip():
        raise ValueError("concept cannot be empty")
    return learning_state.add_hint(level, concept)


@tool
def get_recent_hints(limit: int = 5) -> list[dict]:
    """Return recently delivered hint levels and concepts, newest last."""
    return learning_state.hints(max(1, min(limit, 10)))
