"""initial schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-03-29 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("priority_mode", sa.String(length=20), nullable=False, server_default="sporadic"),
        sa.Column("cadence_days", sa.Integer(), nullable=True),
        sa.Column("importance_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("energy_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("source", sa.String(length=100), nullable=False, server_default="manual"),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ask_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("update_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_asked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_touched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topics")),
        sa.UniqueConstraint("slug", name=op.f("uq_topics_slug")),
    )
    op.create_index(op.f("ix_topics_slug"), "topics", ["slug"], unique=False)

    op.create_table(
        "agent_settings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("llm_provider", sa.String(length=100), nullable=False),
        sa.Column("llm_model", sa.String(length=100), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("max_topics_per_session", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("max_followups_per_topic", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("default_question_style", sa.String(length=100), nullable=False, server_default="lightweight"),
        sa.Column("diary_style", sa.String(length=100), nullable=False, server_default="reflective"),
        sa.Column("ask_for_free_share", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_settings")),
    )

    op.create_table(
        "diary_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("body_markdown", sa.Text(), nullable=False, server_default=""),
        sa.Column("mood", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_diary_entries")),
        sa.UniqueConstraint("session_id", name=op.f("uq_diary_entries_session_id")),
    )
    op.create_index(op.f("ix_diary_entries_entry_date"), "diary_entries", ["entry_date"], unique=False)
    op.create_index(op.f("ix_diary_entries_session_id"), "diary_entries", ["session_id"], unique=False)

    op.create_table(
        "daily_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="planned"),
        sa.Column("opening_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("closing_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("diary_entry_id", sa.String(length=36), nullable=True),
        sa.Column("selected_topic_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_topic_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["diary_entry_id"], ["diary_entries.id"], name=op.f("fk_daily_sessions_diary_entry_id_diary_entries")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_daily_sessions")),
        sa.UniqueConstraint("session_date", name=op.f("uq_daily_sessions_session_date")),
    )
    op.create_index(op.f("ix_daily_sessions_session_date"), "daily_sessions", ["session_date"], unique=False)

    op.create_table(
        "topic_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("from_topic_id", sa.String(length=36), nullable=False),
        sa.Column("to_topic_id", sa.String(length=36), nullable=False),
        sa.Column("relation_type", sa.String(length=100), nullable=False, server_default="related"),
        sa.Column("strength", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["from_topic_id"], ["topics.id"], name=op.f("fk_topic_links_from_topic_id_topics")),
        sa.ForeignKeyConstraint(["to_topic_id"], ["topics.id"], name=op.f("fk_topic_links_to_topic_id_topics")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topic_links")),
    )
    op.create_index(op.f("ix_topic_links_from_topic_id"), "topic_links", ["from_topic_id"], unique=False)
    op.create_index(op.f("ix_topic_links_to_topic_id"), "topic_links", ["to_topic_id"], unique=False)

    op.create_table(
        "session_turns",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("topic_id", sa.String(length=36), nullable=True),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="agent"),
        sa.Column("message_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("message_kind", sa.String(length=30), nullable=False, server_default="note"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["daily_sessions.id"], name=op.f("fk_session_turns_session_id_daily_sessions")),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], name=op.f("fk_session_turns_topic_id_topics")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_turns")),
    )
    op.create_index(op.f("ix_session_turns_session_id"), "session_turns", ["session_id"], unique=False)
    op.create_index(op.f("ix_session_turns_topic_id"), "session_turns", ["topic_id"], unique=False)

    op.create_table(
        "session_topic_queue",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("topic_id", sa.String(length=36), nullable=False),
        sa.Column("queue_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("selection_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("asked_turn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("was_user_initiated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("was_new_topic", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["daily_sessions.id"], name=op.f("fk_session_topic_queue_session_id_daily_sessions")),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], name=op.f("fk_session_topic_queue_topic_id_topics")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_topic_queue")),
        sa.UniqueConstraint("session_id", "topic_id", name="uq_session_topic_queue_session_id_topic_id"),
    )
    op.create_index(op.f("ix_session_topic_queue_session_id"), "session_topic_queue", ["session_id"], unique=False)
    op.create_index(op.f("ix_session_topic_queue_topic_id"), "session_topic_queue", ["topic_id"], unique=False)

    op.create_table(
        "topic_history_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("topic_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=True),
        sa.Column("turn_id", sa.String(length=36), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("user_reply_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("agent_record", sa.Text(), nullable=False, server_default=""),
        sa.Column("event_type", sa.String(length=100), nullable=False, server_default="topic_update"),
        sa.Column("mood", sa.String(length=100), nullable=True),
        sa.Column("salience_score", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["daily_sessions.id"], name=op.f("fk_topic_history_items_session_id_daily_sessions")),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], name=op.f("fk_topic_history_items_topic_id_topics")),
        sa.ForeignKeyConstraint(["turn_id"], ["session_turns.id"], name=op.f("fk_topic_history_items_turn_id_session_turns")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_topic_history_items")),
    )
    op.create_index(op.f("ix_topic_history_items_session_id"), "topic_history_items", ["session_id"], unique=False)
    op.create_index(op.f("ix_topic_history_items_topic_id"), "topic_history_items", ["topic_id"], unique=False)
    op.create_index(op.f("ix_topic_history_items_turn_id"), "topic_history_items", ["turn_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_topic_history_items_turn_id"), table_name="topic_history_items")
    op.drop_index(op.f("ix_topic_history_items_topic_id"), table_name="topic_history_items")
    op.drop_index(op.f("ix_topic_history_items_session_id"), table_name="topic_history_items")
    op.drop_table("topic_history_items")

    op.drop_index(op.f("ix_session_topic_queue_topic_id"), table_name="session_topic_queue")
    op.drop_index(op.f("ix_session_topic_queue_session_id"), table_name="session_topic_queue")
    op.drop_table("session_topic_queue")

    op.drop_index(op.f("ix_session_turns_topic_id"), table_name="session_turns")
    op.drop_index(op.f("ix_session_turns_session_id"), table_name="session_turns")
    op.drop_table("session_turns")

    op.drop_index(op.f("ix_topic_links_to_topic_id"), table_name="topic_links")
    op.drop_index(op.f("ix_topic_links_from_topic_id"), table_name="topic_links")
    op.drop_table("topic_links")

    op.drop_index(op.f("ix_daily_sessions_session_date"), table_name="daily_sessions")
    op.drop_table("daily_sessions")

    op.drop_index(op.f("ix_diary_entries_session_id"), table_name="diary_entries")
    op.drop_index(op.f("ix_diary_entries_entry_date"), table_name="diary_entries")
    op.drop_table("diary_entries")

    op.drop_table("agent_settings")

    op.drop_index(op.f("ix_topics_slug"), table_name="topics")
    op.drop_table("topics")
