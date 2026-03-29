from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from diary_agent.db.base import utc_now
from diary_agent.db.models import DailySession, SessionTopicQueue, SessionTurn
from diary_agent.domain.enums import MessageKind, MessageRole, QueueStatus, SessionStatus
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

    def mark_status(self, daily_session: DailySession, status: SessionStatus) -> DailySession:
        daily_session.status = status.value
        if status == SessionStatus.IN_PROGRESS and daily_session.started_at is None:
            daily_session.started_at = utc_now()
        if status == SessionStatus.COMPLETED:
            daily_session.finished_at = utc_now()
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

    def get_for_session_topic(self, session_id: str, topic_id: str) -> SessionTopicQueue | None:
        stmt = select(SessionTopicQueue).where(
            SessionTopicQueue.session_id == session_id,
            SessionTopicQueue.topic_id == topic_id,
        )
        return self.session.scalar(stmt)

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

    def mark_status(self, queue_item: SessionTopicQueue, status: QueueStatus) -> SessionTopicQueue:
        queue_item.status = status.value
        self.session.add(queue_item)
        self.session.flush()
        return queue_item


class SessionTurnRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_session(self, session_id: str) -> list[SessionTurn]:
        stmt = select(SessionTurn).where(SessionTurn.session_id == session_id).order_by(SessionTurn.turn_index.asc())
        return list(self.session.scalars(stmt))

    def next_turn_index(self, session_id: str) -> int:
        current = self.session.scalar(select(func.max(SessionTurn.turn_index)).where(SessionTurn.session_id == session_id))
        return (current or 0) + 1

    def create_turn(
        self,
        session_id: str,
        topic_id: str | None,
        role: MessageRole,
        message_kind: MessageKind,
        message_text: str,
    ) -> SessionTurn:
        turn = SessionTurn(
            session_id=session_id,
            topic_id=topic_id,
            turn_index=self.next_turn_index(session_id),
            role=role.value,
            message_kind=message_kind.value,
            message_text=message_text,
        )
        self.session.add(turn)
        self.session.flush()
        return turn
