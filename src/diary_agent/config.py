from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DB_PATH = Path("data/diary_agent.db")


@dataclass(frozen=True)
class Settings:
    database_url: str
    database_path: Path
    llm_provider: str
    llm_model: str
    gemini_api_key: str
    anthropic_api_key: str


def get_settings() -> Settings:
    raw_path = os.getenv("DIARY_AGENT_DB_PATH", str(DEFAULT_DB_PATH))
    db_path = Path(raw_path)
    llm_provider = os.getenv("DIARY_AGENT_LLM_PROVIDER", "stub")
    default_model = "gemini-1.5-flash" if llm_provider.lower() == "gemini" else "deterministic-v1"
    llm_model = os.getenv("DIARY_AGENT_LLM_MODEL", default_model)

    return Settings(
        database_url=f"sqlite:///{db_path.as_posix()}",
        database_path=db_path,
        llm_provider=llm_provider,
        llm_model=llm_model,
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    )
