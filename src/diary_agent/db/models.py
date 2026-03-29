from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from diary_agent.db.base import Base, TimestampMixin, utc_now
from diary_agent.domain.enums import MessageKind, MessageRole, PriorityMode, QueueStatus, SessionStatus, TopicState


def new_id() -> str:
    return str(uuid.uuid4())


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(20), nullable=False, default=TopicState.ACTIVE.value)
    priority_mode: Mapped[str] = mapped_column(String(20), nullable=False, default=PriorityMode.SPORADIC.value)
    cadence_days: Mapped[Optional[int]] = mapped_column(Integer)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    energy_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="manual")
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ask_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    update_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_asked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_touched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    history_items: Mapped[list["TopicHistoryItem"]] = relationship(back_populates="topic")
    session_turns: Mapped[list["SessionTurn"]] = relationship(back_populates="topic")
    queued_sessions: Mapped[list["SessionTopicQueue"]] = relationship(back_populates="topic")


class TopicHistoryItem(Base):
    __tablename__ = "topic_history_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(ForeignKey("daily_sessions.id"), index=True)
    turn_id: Mapped[Optional[str]] = mapped_column(ForeignKey("session_turns.id"), index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    user_reply_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    agent_record: Mapped[str] = mapped_column(Text, nullable=False, default="")
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, default="topic_update")
    mood: Mapped[Optional[str]] = mapped_column(String(100))
    salience_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    topic: Mapped["Topic"] = relationship(back_populates="history_items")
    session: Mapped[Optional["DailySession"]] = relationship(back_populates="history_items")
    turn: Mapped[Optional["SessionTurn"]] = relationship(back_populates="history_items")


class DailySession(Base, TimestampMixin):
    __tablename__ = "daily_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=SessionStatus.PLANNED.value)
    opening_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    closing_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    diary_entry_id: Mapped[Optional[str]] = mapped_column(ForeignKey("diary_entries.id"))
    selected_topic_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_topic_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    turns: Mapped[list["SessionTurn"]] = relationship(back_populates="session")
    topic_queue: Mapped[list["SessionTopicQueue"]] = relationship(back_populates="session")
    history_items: Mapped[list["TopicHistoryItem"]] = relationship(back_populates="session")
    diary_entry: Mapped[Optional["DiaryEntry"]] = relationship(
        back_populates="session",
        foreign_keys="DiaryEntry.session_id",
        uselist=False,
    )


class SessionTurn(Base):
    __tablename__ = "session_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("daily_sessions.id"), nullable=False, index=True)
    topic_id: Mapped[Optional[str]] = mapped_column(ForeignKey("topics.id"), index=True)
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=MessageRole.AGENT.value)
    message_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    message_kind: Mapped[str] = mapped_column(String(30), nullable=False, default=MessageKind.NOTE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    session: Mapped["DailySession"] = relationship(back_populates="turns")
    topic: Mapped[Optional["Topic"]] = relationship(back_populates="session_turns")
    history_items: Mapped[list["TopicHistoryItem"]] = relationship(back_populates="turn")


class SessionTopicQueue(Base, TimestampMixin):
    __tablename__ = "session_topic_queue"
    __table_args__ = (
        UniqueConstraint("session_id", "topic_id", name="uq_session_topic_queue_session_id_topic_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("daily_sessions.id"), nullable=False, index=True)
    topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), nullable=False, index=True)
    queue_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=QueueStatus.QUEUED.value)
    selection_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    asked_turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    was_user_initiated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    was_new_topic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    session: Mapped["DailySession"] = relationship(back_populates="topic_queue")
    topic: Mapped["Topic"] = relationship(back_populates="queued_sessions")


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("daily_sessions.id"), nullable=False, unique=True, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mood: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    session: Mapped[Optional["DailySession"]] = relationship(
        back_populates="diary_entry",
        foreign_keys=[session_id],
    )


class AgentSetting(Base, TimestampMixin):
    __tablename__ = "agent_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    llm_provider: Mapped[str] = mapped_column(String(100), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    max_topics_per_session: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    max_followups_per_topic: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    default_question_style: Mapped[str] = mapped_column(String(100), nullable=False, default="lightweight")
    diary_style: Mapped[str] = mapped_column(String(100), nullable=False, default="reflective")
    ask_for_free_share: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TopicLink(Base):
    __tablename__ = "topic_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    from_topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), nullable=False, index=True)
    to_topic_id: Mapped[str] = mapped_column(ForeignKey("topics.id"), nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False, default="related")
    strength: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
