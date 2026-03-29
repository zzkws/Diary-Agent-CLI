from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DB_PATH = Path("data/diary_agent.db")


@dataclass(frozen=True)
class Settings:
    database_url: str
    database_path: Path


def get_settings() -> Settings:
    raw_path = os.getenv("DIARY_AGENT_DB_PATH", str(DEFAULT_DB_PATH))
    db_path = Path(raw_path)
    return Settings(
        database_url=f"sqlite:///{db_path.as_posix()}",
        database_path=db_path,
    )
