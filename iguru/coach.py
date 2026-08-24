"""Construction of the persistent Strands coaching agent."""

import os
from pathlib import Path

from strands import Agent
from strands.models.gemini import GeminiModel
from strands.session.file_session_manager import FileSessionManager

from .config import DEFAULT_MODEL
from .prompts import build_system_prompt
from .tools import IGURU_TOOLS


def make_agent(
    session_name: str,
    session_dir: Path,
    coaching_style: str = "standard",
) -> Agent:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to helper-agent/.env")

    model = GeminiModel(
        model_id=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
        client_args={"api_key": api_key},
        params={"temperature": 0.35},
    )
    manager = FileSessionManager(session_id=session_name, storage_dir=str(session_dir))
    return Agent(
        name="iGuru",
        model=model,
        system_prompt=build_system_prompt(coaching_style),
        tools=IGURU_TOOLS,
        session_manager=manager,
        callback_handler=None,
    )
