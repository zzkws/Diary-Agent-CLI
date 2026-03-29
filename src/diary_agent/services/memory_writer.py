from __future__ import annotations

from datetime import date

from diary_agent.db.base import utc_now
from diary_agent.db.models import DailySession, SessionTopicQueue, Topic
from diary_agent.db.repositories.sessions import SessionTopicQueueRepository
from diary_agent.db.repositories.topics import TopicRepository
from diary_agent.domain.enums import PriorityMode, QueueStatus, TopicState
from diary_agent.domain.schemas import TopicSignalExtraction
from diary_agent.services.topic_registry import TopicRegistry


class MemoryWriter:
    def __init__(
        self,
        topics: TopicRepository,
        queue: SessionTopicQueueRepository,
        topic_registry: TopicRegistry,
    ) -> None:
        self.topics = topics
        self.queue = queue
        self.topic_registry = topic_registry

    def apply_topic_reply(
        self,
        session: DailySession,
        queue_item: SessionTopicQueue,
        topic: Topic,
        question_text: str,
        user_reply: str,
        turn_id: str,
        extraction: TopicSignalExtraction,
    ) -> None:
        now = utc_now()
        self.topics.create_history_item(
            topic_id=topic.id,
            session_id=session.id,
            turn_id=turn_id,
            item_date=session.session_date,
            question_text=question_text,
            user_reply_text=user_reply,
            agent_record=extraction.formal_memory_record,
            mood=extraction.mood,
            salience_score=extraction.salience_score,
        )

        if extraction.topic_status_summary:
            topic.status_summary = extraction.topic_status_summary
        if extraction.topic_state is not None:
            topic.state = extraction.topic_state.value

        topic.last_updated_at = now
        topic.last_touched_at = now
        topic.update_count += 1
        topic.ask_count += 1
        topic.last_asked_at = now

        self._auto_adjust_topic(topic, extraction)

        queue_item.asked_turn_count += 1
        if not extraction.followup_needed:
            queue_item.status = QueueStatus.DONE.value

        for candidate in extraction.new_topic_candidates:
            created = self.topic_registry.create_candidate_topic(candidate)
            existing = self.queue.get_for_session_topic(session.id, created.id)
            if existing is None:
                self.queue.create(
                    data=self._new_queue_entry(session.id, created.id, selection_reason="Detected from response", is_new=True)
                )

        self.topics.session.add_all([topic, queue_item, session])
        self.topics.session.flush()

    def record_free_share(self, session: DailySession, user_reply: str, turn_id: str, extraction: TopicSignalExtraction) -> None:
        for candidate in extraction.new_topic_candidates:
            self.topic_registry.create_candidate_topic(candidate)

    def _auto_adjust_topic(self, topic: Topic, extraction: TopicSignalExtraction) -> None:
        if extraction.salience_score >= 0.8:
            topic.priority_mode = PriorityMode.CADENCED.value
            topic.cadence_days = min(topic.cadence_days or 7, 7)
        elif topic.priority_mode == PriorityMode.CADENCED.value and extraction.salience_score < 0.45:
            topic.cadence_days = max(topic.cadence_days or 14, 14)

        if extraction.topic_state == TopicState.DORMANT and topic.priority_mode == PriorityMode.DAILY.value:
            topic.priority_mode = PriorityMode.SPORADIC.value

    def _new_queue_entry(self, session_id: str, topic_id: str, selection_reason: str, is_new: bool):
        from diary_agent.domain.schemas import SessionTopicQueueCreate

        existing = self.queue.list_for_session(session_id)
        return SessionTopicQueueCreate(
            session_id=session_id,
            topic_id=topic_id,
            queue_order=len(existing),
            selection_reason=selection_reason,
            status=QueueStatus.QUEUED,
            was_new_topic=is_new,
        )
