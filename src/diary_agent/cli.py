from __future__ import annotations

from datetime import date
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from diary_agent.config import get_settings
from diary_agent.db.session import create_all_tables, session_scope
from diary_agent.db.repositories.diary import DiaryEntryRepository
from diary_agent.db.repositories.sessions import DailySessionRepository, SessionTopicQueueRepository, SessionTurnRepository
from diary_agent.db.repositories.topics import TopicRepository
from diary_agent.db.repositories.settings import AgentSettingRepository
from diary_agent.domain.schemas import AgentSettingCreate, TopicCreate
from diary_agent.llm import build_provider
from diary_agent.services.conversation_orchestrator import ConversationOrchestrator
from diary_agent.services.diary_synthesizer import DiarySynthesizer
from diary_agent.services.question_composer import QuestionComposer
from diary_agent.services.signal_extractor import SignalExtractor
from diary_agent.services.topic_registry import TopicRegistry


app = typer.Typer(help="CLI-first, local-first diary agent.")
topics_app = typer.Typer(help="Topic management commands.")
diary_app = typer.Typer(help="Diary commands.")
session_app = typer.Typer(help="Session inspection commands.")
app.add_typer(topics_app, name="topics")
app.add_typer(diary_app, name="diary")
app.add_typer(session_app, name="session")

console = Console()


@app.command("init-db")
def init_db() -> None:
    """Create tables and seed default settings if missing."""
    create_all_tables()
    app_settings = get_settings()
    with session_scope() as db_session:
        settings_repo = AgentSettingRepository(db_session)
        if settings_repo.get_default() is None:
            settings_repo.create_default(
                AgentSettingCreate(
                    llm_provider=app_settings.llm_provider,
                    llm_model=app_settings.llm_model,
                    temperature=0.2,
                    max_topics_per_session=5,
                    max_followups_per_topic=1,
                    default_question_style="lightweight",
                    diary_style="reflective",
                    ask_for_free_share=True,
                )
            )
    console.print("Database initialized.")


@topics_app.command("list")
def list_topics() -> None:
    """List all topics."""
    with session_scope() as db_session:
        topics = TopicRepository(db_session).list_all()

    table = Table(title="Topics")
    table.add_column("ID")
    table.add_column("Slug")
    table.add_column("Title")
    table.add_column("State")
    table.add_column("Priority")
    table.add_column("Last Touched")

    for topic in topics:
        table.add_row(
            topic.id,
            topic.slug,
            topic.title,
            topic.state,
            topic.priority_mode,
            topic.last_touched_at.isoformat() if topic.last_touched_at else "-",
        )

    console.print(table)


@topics_app.command("add")
def add_topic(
    title: str,
    description: str = typer.Option("", help="Optional topic description."),
    category: str = typer.Option("", help="Optional topic category."),
    pinned: bool = typer.Option(False, help="Pin topic so planner prioritizes it."),
) -> None:
    """Add a topic."""
    with session_scope() as db_session:
        repo = TopicRepository(db_session)
        topic = TopicRegistry(repo).create_topic(
            TopicCreate(
                title=title,
                description=description,
                category=category or None,
                is_pinned=pinned,
            )
        )
    console.print(f"Created topic {topic.slug} ({topic.id}).")


@topics_app.command("show")
def show_topic(identifier: str) -> None:
    """Show a topic by ID or slug."""
    with session_scope() as db_session:
        repo = TopicRepository(db_session)
        topic = repo.get(identifier)
        history = repo.list_history(topic.id, limit=5) if topic else []

    if topic is None:
        console.print("Topic not found.")
        raise typer.Exit(code=1)

    console.print(
        {
            "id": topic.id,
            "title": topic.title,
            "slug": topic.slug,
            "description": topic.description,
            "status_summary": topic.status_summary,
            "category": topic.category,
            "state": topic.state,
            "priority_mode": topic.priority_mode,
            "cadence_days": topic.cadence_days,
            "importance_score": topic.importance_score,
            "energy_score": topic.energy_score,
            "confidence_score": topic.confidence_score,
            "source": topic.source,
            "is_pinned": topic.is_pinned,
            "ask_count": topic.ask_count,
            "update_count": topic.update_count,
            "last_asked_at": topic.last_asked_at,
            "last_updated_at": topic.last_updated_at,
            "last_touched_at": topic.last_touched_at,
            "recent_history": [item.agent_record for item in history],
        }
    )


@diary_app.command("today")
def diary_today() -> None:
    """Show today's diary entry if present."""
    with session_scope() as db_session:
        entry = DiaryEntryRepository(db_session).get_by_entry_date(date.today())

    if entry is None:
        console.print("No diary entry for today.")
        raise typer.Exit(code=0)

    console.print(entry.body_markdown)


@session_app.command("show")
def show_session(identifier: Optional[str] = None) -> None:
    """Show a session by date string or ID."""
    with session_scope() as db_session:
        repo = DailySessionRepository(db_session)
        queue_repo = SessionTopicQueueRepository(db_session)
        turns_repo = SessionTurnRepository(db_session)
        daily_session = repo.get(identifier) if identifier else repo.get_by_date(date.today())
        queue = queue_repo.list_for_session(daily_session.id) if daily_session else []
        turns = turns_repo.list_for_session(daily_session.id) if daily_session else []

    if daily_session is None:
        console.print("Session not found.")
        raise typer.Exit(code=1)

    console.print(
        {
            "id": daily_session.id,
            "session_date": daily_session.session_date.isoformat(),
            "status": daily_session.status,
            "selected_topic_count": daily_session.selected_topic_count,
            "completed_topic_count": daily_session.completed_topic_count,
            "started_at": daily_session.started_at,
            "finished_at": daily_session.finished_at,
            "created_at": daily_session.created_at,
            "updated_at": daily_session.updated_at,
            "queue": [
                {
                    "topic_id": item.topic_id,
                    "status": item.status,
                    "order": item.queue_order,
                    "asked_turn_count": item.asked_turn_count,
                    "reason": item.selection_reason,
                }
                for item in queue
            ],
            "turn_count": len(turns),
        }
    )


@app.command("run")
def run_session(session_date: Optional[str] = typer.Option(None, help="Optional ISO date override (YYYY-MM-DD).")) -> None:
    """Run the daily interview loop end-to-end."""
    target_date = date.fromisoformat(session_date) if session_date else date.today()
    app_settings = get_settings()
    llm_provider = build_provider(app_settings)

    with session_scope() as db_session:
        orchestrator = ConversationOrchestrator(
            session_repo=DailySessionRepository(db_session),
            queue_repo=SessionTopicQueueRepository(db_session),
            topic_repo=TopicRepository(db_session),
            settings_repo=AgentSettingRepository(db_session),
            turn_repo=SessionTurnRepository(db_session),
            diary_repo=DiaryEntryRepository(db_session),
            console=console,
            question_composer=QuestionComposer(llm_provider=llm_provider),
            signal_extractor=SignalExtractor(llm_provider=llm_provider),
            diary_synthesizer=DiarySynthesizer(llm_provider=llm_provider),
        )
        session = orchestrator.run(target_date)
    console.print(f"Session complete ({session.id}).")


if __name__ == "__main__":
    app()
