from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from diary_agent.domain.enums import PriorityMode, QueueStatus, SessionStatus, TopicState


@dataclass(slots=True)
class TopicCreate:
    title: str
    description: str = ""
    category: Optional[str] = None
    status_summary: str = ""
    state: TopicState = TopicState.ACTIVE
    priority_mode: PriorityMode = PriorityMode.SPORADIC
    cadence_days: Optional[int] = None
    importance_score: float = 0.5
    energy_score: float = 0.5
    confidence_score: float = 0.5
    source: str = "manual"
    is_pinned: bool = False


@dataclass(slots=True)
class TopicUpdate:
    description: Optional[str] = None
    status_summary: Optional[str] = None
    category: Optional[str] = None
    state: Optional[TopicState] = None
    priority_mode: Optional[PriorityMode] = None
    cadence_days: Optional[int] = None
    importance_score: Optional[float] = None
    energy_score: Optional[float] = None
    confidence_score: Optional[float] = None
    source: Optional[str] = None
    is_pinned: Optional[bool] = None
    archived_at: Optional[datetime] = None


@dataclass(slots=True)
class DailySessionCreate:
    session_date: date
    status: SessionStatus = SessionStatus.PLANNED
    opening_message: str = ""
    closing_message: str = ""


@dataclass(slots=True)
class SessionTopicQueueCreate:
    session_id: str
    topic_id: str
    queue_order: int
    status: QueueStatus = QueueStatus.QUEUED
    selection_reason: str = ""
    asked_turn_count: int = 0
    was_user_initiated: bool = False
    was_new_topic: bool = False


@dataclass(slots=True)
class AgentSettingCreate:
    llm_provider: str
    llm_model: str
    temperature: float
    max_topics_per_session: int
    max_followups_per_topic: int
    default_question_style: str
    diary_style: str
    ask_for_free_share: bool


@dataclass(slots=True)
class TopicSelection:
    topic_id: str
    score: float
    reason: str


@dataclass(slots=True)
class TopicSignalExtraction:
    topic_status_summary: Optional[str] = None
    topic_state: Optional[TopicState] = None
    salience_score: float = 0.5
    mood: Optional[str] = None
    followup_needed: bool = False
    followup_reason: str = ""
    formal_memory_record: str = ""
    new_topic_candidates: list[TopicCreate] = field(default_factory=list)


@dataclass(slots=True)
class PlannerTopicCandidate:
    topic_id: str
    title: str
    score: float
    layer: str
    reason: str
    cadence_due: bool = False
    days_since_asked: Optional[int] = None


@dataclass(slots=True)
class SessionPlan:
    ordered_topics: list[PlannerTopicCandidate]
    max_topics: int


@dataclass(slots=True)
class TopicLifecycleAdjustment:
    state: Optional[TopicState] = None
    priority_mode: Optional[PriorityMode] = None
    cadence_days: Optional[int] = None
    importance_score: Optional[float] = None
    confidence_score: Optional[float] = None
    status_summary: Optional[str] = None
