from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from diary_agent.db.models import DailySession, SessionTopicQueue
from diary_agent.domain.schemas import DailySessionCreate, SessionTopicQueueCreate


class DailySessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, identifier: str | None) -> DailySession | None:
        if identifier is None:
            return None
        if len(identifier) == 36 and identifier.count("-") == 4:
            return self.session.scalar(select(DailySession).where(DailySession.id == identifier))
        try:
            parsed_date = date.fromisoformat(identifier)
        except ValueError:
            return None
        return self.get_by_date(parsed_date)

    def get_by_date(self, session_date: date) -> DailySession | None:
        return self.session.scalar(select(DailySession).where(DailySession.session_date == session_date))

    def create(self, data: DailySessionCreate) -> DailySession:
        daily_session = DailySession(
            session_date=data.session_date,
            status=data.status.value,
            opening_message=data.opening_message,
            closing_message=data.closing_message,
        )
        self.session.add(daily_session)
        self.session.flush()
        return daily_session


class SessionTopicQueueRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_session(self, session_id: str) -> list[SessionTopicQueue]:
        stmt = (
            select(SessionTopicQueue)
            .where(SessionTopicQueue.session_id == session_id)
            .order_by(SessionTopicQueue.queue_order.asc())
        )
        return list(self.session.scalars(stmt))

    def create(self, data: SessionTopicQueueCreate) -> SessionTopicQueue:
        queue_item = SessionTopicQueue(
            session_id=data.session_id,
            topic_id=data.topic_id,
            queue_order=data.queue_order,
            status=data.status.value,
            selection_reason=data.selection_reason,
            asked_turn_count=data.asked_turn_count,
            was_user_initiated=data.was_user_initiated,
            was_new_topic=data.was_new_topic,
        )
        self.session.add(queue_item)
        self.session.flush()
        return queue_item
