from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from diary_agent.db.base import Base
from diary_agent.db.repositories.sessions import DailySessionRepository, SessionTopicQueueRepository
from diary_agent.db.repositories.topics import TopicRepository
from diary_agent.domain.enums import QueueStatus, SessionStatus, TopicState
from diary_agent.domain.schemas import DailySessionCreate, SessionTopicQueueCreate, TopicCreate, TopicSignalExtraction
from diary_agent.services.memory_writer import MemoryWriter
from diary_agent.services.topic_registry import TopicRegistry


def _db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True, expire_on_commit=False)()


def test_memory_writer_persists_history_and_updates_topic_and_queue() -> None:
    session = _db_session()
    topic_repo = TopicRepository(session)
    queue_repo = SessionTopicQueueRepository(session)
    daily_repo = DailySessionRepository(session)

    topic = topic_repo.create(TopicCreate(title="Health"))
    day = daily_repo.create(DailySessionCreate(session_date=date(2026, 3, 29), status=SessionStatus.IN_PROGRESS))
    queue_item = queue_repo.create(SessionTopicQueueCreate(session_id=day.id, topic_id=topic.id, queue_order=0))

    writer = MemoryWriter(topic_repo, queue_repo, TopicRegistry(topic_repo))
    extraction = TopicSignalExtraction(
        topic_status_summary="Health: better sleep this week",
        salience_score=0.84,
        mood="positive",
        followup_needed=False,
        formal_memory_record="Record|topic=Health; salience=0.84; mood=positive; update=better sleep this week",
    )

    writer.apply_topic_reply(
        session=day,
        queue_item=queue_item,
        topic=topic,
        question_text="How did Health go today?",
        user_reply="better sleep this week",
        turn_id="turn-1",
        extraction=extraction,
    )

    history = topic_repo.list_history(topic.id)
    assert len(history) == 1
    assert history[0].agent_record.startswith("Record|topic=Health")
    assert topic.status_summary == "Health: better sleep this week"
    assert topic.update_count == 1
    assert topic.ask_count == 1
    assert topic.priority_mode in {"sporadic", "cadenced"}
    assert queue_item.status == QueueStatus.DONE.value


def test_memory_writer_creates_candidate_topic_from_extraction() -> None:
    session = _db_session()
    topic_repo = TopicRepository(session)
    queue_repo = SessionTopicQueueRepository(session)
    daily_repo = DailySessionRepository(session)

    topic = topic_repo.create(TopicCreate(title="Career"))
    day = daily_repo.create(DailySessionCreate(session_date=date(2026, 3, 29), status=SessionStatus.IN_PROGRESS))
    queue_item = queue_repo.create(SessionTopicQueueCreate(session_id=day.id, topic_id=topic.id, queue_order=0))

    writer = MemoryWriter(topic_repo, queue_repo, TopicRegistry(topic_repo))
    extraction = TopicSignalExtraction(
        topic_status_summary="Career: ongoing",
        salience_score=0.5,
        formal_memory_record="Record|topic=Career; salience=0.50; mood=undetected; update=ongoing",
        new_topic_candidates=[TopicCreate(title="Travel Plans", source="session_extractor")],
    )

    writer.apply_topic_reply(day, queue_item, topic, "Q", "A", "turn-1", extraction)

    topics = topic_repo.list_all()
    candidate = next(t for t in topics if t.title == "Travel Plans")
    assert candidate.state == TopicState.CANDIDATE.value
    queued = queue_repo.get_for_session_topic(day.id, candidate.id)
    assert queued is not None
    assert queued.was_new_topic is True
