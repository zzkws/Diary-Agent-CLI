from __future__ import annotations

from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from diary_agent.db.base import Base
from diary_agent.db.repositories.diary import DiaryEntryRepository
from diary_agent.db.repositories.sessions import DailySessionRepository, SessionTopicQueueRepository, SessionTurnRepository
from diary_agent.db.repositories.settings import AgentSettingRepository
from diary_agent.db.repositories.topics import TopicRepository
from diary_agent.domain.schemas import AgentSettingCreate, TopicCreate
from diary_agent.services.conversation_orchestrator import ConversationOrchestrator


class FakeConsole:
    def __init__(self, inputs: list[str]) -> None:
        self.inputs = inputs
        self.messages: list[str] = []

    def print(self, message: str) -> None:
        self.messages.append(str(message))

    def input(self, prompt: str) -> str:
        self.messages.append(prompt)
        if not self.inputs:
            raise AssertionError("Unexpected input call")
        return self.inputs.pop(0)


def _session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, future=True, expire_on_commit=False)()


def _seed_defaults(db):
    AgentSettingRepository(db).create_default(
        AgentSettingCreate(
            llm_provider="stub",
            llm_model="deterministic-v1",
            temperature=0.2,
            max_topics_per_session=5,
            max_followups_per_topic=1,
            default_question_style="lightweight",
            diary_style="reflective",
            ask_for_free_share=True,
        )
    )


def test_orchestrator_end_to_end_creates_diary_and_marks_completed() -> None:
    db = _session()
    _seed_defaults(db)
    topic_repo = TopicRepository(db)
    topic_repo.create(TopicCreate(title="Health", is_pinned=True))
    topic_repo.create(TopicCreate(title="Career"))

    console = FakeConsole([
        "Slept better and felt good",
        "Work is busy but manageable",
        "Nothing else",
    ])

    orchestrator = ConversationOrchestrator(
        session_repo=DailySessionRepository(db),
        queue_repo=SessionTopicQueueRepository(db),
        topic_repo=topic_repo,
        settings_repo=AgentSettingRepository(db),
        turn_repo=SessionTurnRepository(db),
        diary_repo=DiaryEntryRepository(db),
        console=console,
    )

    daily = orchestrator.run(date(2026, 3, 29))

    assert daily.status == "completed"
    assert daily.completed_topic_count == 2
    entry = DiaryEntryRepository(db).get_by_session_id(daily.id)
    assert entry is not None
    assert "## Continuity" in entry.body_markdown


def test_orchestrator_resume_does_not_repeat_done_topics() -> None:
    db = _session()
    _seed_defaults(db)
    topic_repo = TopicRepository(db)
    topic1 = topic_repo.create(TopicCreate(title="Health", is_pinned=True))
    topic_repo.create(TopicCreate(title="Learning"))

    console1 = FakeConsole(["Health update", "Learning update", "Nothing else"])
    orchestrator = ConversationOrchestrator(
        session_repo=DailySessionRepository(db),
        queue_repo=SessionTopicQueueRepository(db),
        topic_repo=topic_repo,
        settings_repo=AgentSettingRepository(db),
        turn_repo=SessionTurnRepository(db),
        diary_repo=DiaryEntryRepository(db),
        console=console1,
    )
    daily = orchestrator.run(date(2026, 3, 29))

    queue_repo = SessionTopicQueueRepository(db)
    queue = queue_repo.list_for_session(daily.id)
    queue[0].status = "done"
    queue[1].status = "queued"
    db.flush()

    turns_before = len(SessionTurnRepository(db).list_for_session(daily.id))

    console2 = FakeConsole(["Updated only second topic", "Still nothing else"])
    orchestrator2 = ConversationOrchestrator(
        session_repo=DailySessionRepository(db),
        queue_repo=queue_repo,
        topic_repo=topic_repo,
        settings_repo=AgentSettingRepository(db),
        turn_repo=SessionTurnRepository(db),
        diary_repo=DiaryEntryRepository(db),
        console=console2,
    )
    orchestrator2.run(date(2026, 3, 29))

    turns_after = len(SessionTurnRepository(db).list_for_session(daily.id))
    assert turns_after > turns_before
    # Ensure resumed run did not re-ask topic1 kickoff question
    asked_topic1 = [
        t for t in SessionTurnRepository(db).list_for_session(daily.id) if t.topic_id == topic1.id and t.role == "agent" and t.message_kind == "question"
    ]
    assert len(asked_topic1) == 1
