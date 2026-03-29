from __future__ import annotations

from datetime import date

from rich.console import Console

from diary_agent.db.models import DailySession, SessionTopicQueue, Topic
from diary_agent.db.repositories.diary import DiaryEntryRepository
from diary_agent.db.repositories.sessions import DailySessionRepository, SessionTopicQueueRepository, SessionTurnRepository
from diary_agent.db.repositories.settings import AgentSettingRepository
from diary_agent.db.repositories.topics import TopicRepository
from diary_agent.domain.enums import MessageKind, MessageRole, QueueStatus, SessionStatus
from diary_agent.domain.schemas import DailySessionCreate, SessionTopicQueueCreate
from diary_agent.services.diary_synthesizer import DiarySynthesizer
from diary_agent.services.memory_writer import MemoryWriter
from diary_agent.services.question_composer import QuestionComposer
from diary_agent.services.session_planner import PlannerConfig, SessionPlanner
from diary_agent.services.signal_extractor import SignalExtractor
from diary_agent.services.topic_registry import TopicRegistry


class ConversationOrchestrator:
    def __init__(
        self,
        session_repo: DailySessionRepository,
        queue_repo: SessionTopicQueueRepository,
        topic_repo: TopicRepository,
        settings_repo: AgentSettingRepository,
        turn_repo: SessionTurnRepository,
        diary_repo: DiaryEntryRepository,
        console: Console,
    ) -> None:
        self.session_repo = session_repo
        self.queue_repo = queue_repo
        self.topic_repo = topic_repo
        self.settings_repo = settings_repo
        self.turn_repo = turn_repo
        self.diary_repo = diary_repo
        self.console = console

        self.extractor = SignalExtractor()
        self.question_composer = QuestionComposer()
        self.topic_registry = TopicRegistry(topic_repo)
        self.memory_writer = MemoryWriter(topic_repo, queue_repo, self.topic_registry)
        self.diary_synth = DiarySynthesizer()

    def run(self, session_date: date) -> DailySession:
        daily_session = self._load_or_create_session(session_date)
        self.session_repo.mark_status(daily_session, SessionStatus.IN_PROGRESS)
        queue_items = self._ensure_topic_plan(daily_session)
        self._maybe_open(daily_session, queue_items)

        for queue_item in queue_items:
            if queue_item.status == QueueStatus.DONE.value:
                continue
            topic = self.topic_repo.get(queue_item.topic_id)
            if topic is None:
                queue_item.status = QueueStatus.SKIPPED.value
                continue
            self._run_topic_turn(daily_session, queue_item, topic)

        settings = self.settings_repo.get_default()
        if settings and settings.ask_for_free_share:
            self._run_free_share(daily_session)

        self._finish_session(daily_session)
        return daily_session

    def _load_or_create_session(self, session_date: date) -> DailySession:
        session = self.session_repo.get_by_date(session_date)
        if session is None:
            session = self.session_repo.create(DailySessionCreate(session_date=session_date))
        return session

    def _ensure_topic_plan(self, daily_session: DailySession) -> list[SessionTopicQueue]:
        queue_items = self.queue_repo.list_for_session(daily_session.id)
        if queue_items:
            return queue_items

        settings = self.settings_repo.get_default()
        max_topics = settings.max_topics_per_session if settings else 5
        planner = SessionPlanner(PlannerConfig(max_topics=max_topics))
        plan = planner.build_plan(self.topic_repo.list_open_topics(), daily_session.session_date)

        for order, candidate in enumerate(plan.ordered_topics):
            self.queue_repo.create(
                SessionTopicQueueCreate(
                    session_id=daily_session.id,
                    topic_id=candidate.topic_id,
                    queue_order=order,
                    selection_reason=f"{candidate.layer}: {candidate.reason} (score={candidate.score:.1f})",
                )
            )
        daily_session.selected_topic_count = len(plan.ordered_topics)
        self.session_repo.session.add(daily_session)
        self.session_repo.session.flush()
        return self.queue_repo.list_for_session(daily_session.id)

    def _maybe_open(self, daily_session: DailySession, queue_items: list[SessionTopicQueue]) -> None:
        turns = self.turn_repo.list_for_session(daily_session.id)
        if turns:
            return
        msg = self.question_composer.opening_message(len(queue_items))
        self.console.print(f"\n[bold cyan]Agent:[/bold cyan] {msg}")
        self.turn_repo.create_turn(daily_session.id, None, MessageRole.AGENT, MessageKind.OPENING, msg)
        daily_session.opening_message = msg

    def _run_topic_turn(self, daily_session: DailySession, queue_item: SessionTopicQueue, topic: Topic) -> None:
        queue_item.status = QueueStatus.ACTIVE.value
        first_question = self.question_composer.topic_kickoff_question(topic)
        self.console.print(f"\n[bold cyan]Agent:[/bold cyan] {first_question}")
        self.turn_repo.create_turn(daily_session.id, topic.id, MessageRole.AGENT, MessageKind.QUESTION, first_question)
        user_reply = self.console.input("[bold green]You:[/bold green] ").strip()
        user_turn = self.turn_repo.create_turn(daily_session.id, topic.id, MessageRole.USER, MessageKind.REPLY, user_reply)

        extraction = self.extractor.extract(topic, user_reply)
        self.memory_writer.apply_topic_reply(
            daily_session,
            queue_item,
            topic,
            first_question,
            user_reply,
            user_turn.id,
            extraction,
        )

        settings = self.settings_repo.get_default()
        max_followups = settings.max_followups_per_topic if settings else 1
        if extraction.followup_needed and queue_item.asked_turn_count <= max_followups:
            followup = self.question_composer.followup_question(topic, extraction.followup_reason)
            self.console.print(f"[bold cyan]Agent:[/bold cyan] {followup}")
            self.turn_repo.create_turn(daily_session.id, topic.id, MessageRole.AGENT, MessageKind.FOLLOWUP, followup)
            follow_reply = self.console.input("[bold green]You:[/bold green] ").strip()
            follow_turn = self.turn_repo.create_turn(daily_session.id, topic.id, MessageRole.USER, MessageKind.REPLY, follow_reply)
            follow_extraction = self.extractor.extract(topic, follow_reply)
            follow_extraction.followup_needed = False
            self.memory_writer.apply_topic_reply(
                daily_session,
                queue_item,
                topic,
                followup,
                follow_reply,
                follow_turn.id,
                follow_extraction,
            )

        queue_item.status = QueueStatus.DONE.value
        daily_session.completed_topic_count += 1

    def _run_free_share(self, daily_session: DailySession) -> None:
        prior = self.turn_repo.list_for_session(daily_session.id)
        if any(turn.message_kind == MessageKind.FREE_SHARE.value for turn in prior):
            return
        prompt = self.question_composer.free_share_question()
        self.console.print(f"\n[bold cyan]Agent:[/bold cyan] {prompt}")
        self.turn_repo.create_turn(daily_session.id, None, MessageRole.AGENT, MessageKind.FREE_SHARE, prompt)
        reply = self.console.input("[bold green]You:[/bold green] ").strip()
        user_turn = self.turn_repo.create_turn(daily_session.id, None, MessageRole.USER, MessageKind.REPLY, reply)
        extraction = self.extractor.extract_free_share(reply)
        self.memory_writer.record_free_share(daily_session, reply, user_turn.id, extraction)

    def _finish_session(self, daily_session: DailySession) -> None:
        all_queue = self.queue_repo.list_for_session(daily_session.id)
        topics = {topic.id: topic for topic in self.topic_repo.list_all()}
        history_items = self.topic_repo.list_history_for_session(daily_session.id)

        title, summary, body, mood = self.diary_synth.synthesize(daily_session, all_queue, topics, history_items)
        entry = self.diary_repo.upsert_for_session(
            session_id=daily_session.id,
            entry_date=daily_session.session_date,
            title=title,
            summary=summary,
            body_markdown=body,
            mood=mood,
        )
        daily_session.diary_entry_id = entry.id

        closing = self.question_composer.closing_message()
        self.console.print(f"\n[bold cyan]Agent:[/bold cyan] {closing}\n")
        self.turn_repo.create_turn(daily_session.id, None, MessageRole.AGENT, MessageKind.CLOSING, closing)
        daily_session.closing_message = closing
        self.session_repo.mark_status(daily_session, SessionStatus.COMPLETED)
