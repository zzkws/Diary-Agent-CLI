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

    def upsert_for_session(
        self,
        session_id: str,
        entry_date: date,
        title: str,
        summary: str,
        body_markdown: str,
        mood: str | None,
    ) -> DiaryEntry:
        entry = self.get_by_session_id(session_id)
        if entry is None:
            entry = DiaryEntry(
                session_id=session_id,
                entry_date=entry_date,
                title=title,
                summary=summary,
                body_markdown=body_markdown,
                mood=mood,
            )
        else:
            entry.title = title
            entry.summary = summary
            entry.body_markdown = body_markdown
            entry.mood = mood
        self.session.add(entry)
        self.session.flush()
        return entry
