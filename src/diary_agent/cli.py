from __future__ import annotations

from datetime import date
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from diary_agent.db.session import create_all_tables, session_scope
from diary_agent.db.repositories.diary import DiaryEntryRepository
from diary_agent.db.repositories.sessions import DailySessionRepository
from diary_agent.db.repositories.topics import TopicRepository
from diary_agent.db.repositories.settings import AgentSettingRepository
from diary_agent.domain.schemas import AgentSettingCreate, TopicCreate


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
    with session_scope() as db_session:
        settings_repo = AgentSettingRepository(db_session)
        if settings_repo.get_default() is None:
            settings_repo.create_default(
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
) -> None:
    """Add a topic."""
    with session_scope() as db_session:
        topic = TopicRepository(db_session).create(
            TopicCreate(
                title=title,
                description=description,
                category=category or None,
            )
        )
    console.print(f"Created topic {topic.slug} ({topic.id}).")


@topics_app.command("show")
def show_topic(identifier: str) -> None:
    """Show a topic by ID or slug."""
    with session_scope() as db_session:
        repo = TopicRepository(db_session)
        topic = repo.get(identifier)

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
        daily_session = repo.get(identifier) if identifier else repo.get_by_date(date.today())

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
        }
    )


if __name__ == "__main__":
    app()
