from __future__ import annotations

from datetime import datetime

from diary_agent.db.base import utc_now
from diary_agent.db.models import Topic
from diary_agent.db.repositories.topics import TopicRepository
from diary_agent.domain.enums import PriorityMode, TopicState
from diary_agent.domain.schemas import TopicCreate, TopicLifecycleAdjustment, TopicUpdate


class TopicRegistry:
    """Owns topic lifecycle logic and keeps lifecycle decisions explicit."""

    def __init__(self, topics: TopicRepository) -> None:
        self.topics = topics

    def create_topic(self, data: TopicCreate) -> Topic:
        topic = self.topics.create(data)
        topic.last_touched_at = utc_now()
        return topic

    def create_candidate_topic(self, data: TopicCreate) -> Topic:
        payload = TopicCreate(
            title=data.title,
            description=data.description,
            category=data.category,
            status_summary=data.status_summary,
            state=TopicState.CANDIDATE,
            priority_mode=PriorityMode.SPORADIC,
            cadence_days=data.cadence_days,
            importance_score=min(max(data.importance_score, 0.3), 0.8),
            confidence_score=min(max(data.confidence_score, 0.3), 0.8),
            source=data.source or "session_extraction",
        )
        return self.create_topic(payload)

    def update_topic_summary(self, topic: Topic, summary: str) -> Topic:
        topic.status_summary = summary.strip()
        topic.last_updated_at = utc_now()
        topic.last_touched_at = topic.last_updated_at
        self.topics.session.add(topic)
        self.topics.session.flush()
        return topic

    def update_topic_metadata(self, topic: Topic, *, category: str | None = None, description: str | None = None) -> Topic:
        topic.category = category if category is not None else topic.category
        topic.description = description if description is not None else topic.description
        topic.last_touched_at = utc_now()
        self.topics.session.add(topic)
        self.topics.session.flush()
        return topic

    def archive_topic(self, topic: Topic, archived_at: datetime | None = None) -> Topic:
        timestamp = archived_at or utc_now()
        return self.topics.update(
            topic,
            TopicUpdate(
                state=TopicState.ARCHIVED,
                priority_mode=PriorityMode.CLOSED,
                archived_at=timestamp,
            ),
        )

    def reactivate_topic(self, topic: Topic) -> Topic:
        return self.topics.update(
            topic,
            TopicUpdate(
                state=TopicState.ACTIVE,
                priority_mode=PriorityMode.CADENCED if topic.cadence_days else PriorityMode.SPORADIC,
                archived_at=None,
            ),
        )

    def adjust_topic_lifecycle(self, topic: Topic, adjustment: TopicLifecycleAdjustment) -> Topic:
        return self.topics.update(
            topic,
            TopicUpdate(
                state=adjustment.state,
                priority_mode=adjustment.priority_mode,
                cadence_days=adjustment.cadence_days,
                importance_score=adjustment.importance_score,
                confidence_score=adjustment.confidence_score,
                status_summary=adjustment.status_summary,
            ),
        )
