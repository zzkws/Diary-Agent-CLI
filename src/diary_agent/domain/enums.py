from __future__ import annotations

from enum import StrEnum


class TopicState(StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    DORMANT = "dormant"
    ARCHIVED = "archived"


class PriorityMode(StrEnum):
    DAILY = "daily"
    CADENCED = "cadenced"
    SPORADIC = "sporadic"
    MANUAL = "manual"
    ONE_OFF = "one_off"
    CLOSED = "closed"


class SessionStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    AWAITING_USER_REPLY = "awaiting_user_reply"
    CLOSING = "closing"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MessageRole(StrEnum):
    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"


class MessageKind(StrEnum):
    OPENING = "opening"
    QUESTION = "question"
    FOLLOWUP = "followup"
    REPLY = "reply"
    FREE_SHARE = "free_share"
    CLOSING = "closing"
    NOTE = "note"


class QueueStatus(StrEnum):
    QUEUED = "queued"
    ACTIVE = "active"
    DONE = "done"
    SKIPPED = "skipped"
    DEFERRED = "deferred"


class RuntimePhase(StrEnum):
    OPENING = "opening"
    TOPIC_INTRO = "topic_intro"
    TOPIC_QUESTION = "topic_question"
    TOPIC_FOLLOWUP = "topic_followup"
    TOPIC_COMMIT = "topic_commit"
    NEXT_TOPIC_DECISION = "next_topic_decision"
    FREE_SHARE = "free_share"
    DIARY_GENERATION = "diary_generation"
    CLOSING = "closing"
    COMPLETED = "completed"
