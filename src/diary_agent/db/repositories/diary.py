from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from diary_agent.db.models import DiaryEntry


class DiaryEntryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_entry_date(self, entry_date: date) -> DiaryEntry | None:
        return self.session.scalar(select(DiaryEntry).where(DiaryEntry.entry_date == entry_date))

    def get_by_session_id(self, session_id: str) -> DiaryEntry | None:
        return self.session.scalar(select(DiaryEntry).where(DiaryEntry.session_id == session_id))
