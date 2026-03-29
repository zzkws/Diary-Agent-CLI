from __future__ import annotations

import re
from dataclasses import asdict

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from diary_agent.db.models import Topic
from diary_agent.domain.schemas import TopicCreate, TopicUpdate


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    return normalized.strip("-") or "topic"


class TopicRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Topic]:
        stmt: Select[tuple[Topic]] = select(Topic).order_by(Topic.created_at.desc())
        return list(self.session.scalars(stmt))

    def get(self, identifier: str) -> Topic | None:
        stmt = select(Topic).where((Topic.id == identifier) | (Topic.slug == identifier))
        return self.session.scalar(stmt)

    def get_by_slug(self, slug: str) -> Topic | None:
        return self.session.scalar(select(Topic).where(Topic.slug == slug))

    def create(self, data: TopicCreate) -> Topic:
        topic = Topic(
            title=data.title,
            slug=self._next_slug(data.title),
            description=data.description,
            status_summary=data.status_summary,
            category=data.category,
            state=data.state.value,
            priority_mode=data.priority_mode.value,
            cadence_days=data.cadence_days,
            importance_score=data.importance_score,
            energy_score=data.energy_score,
            confidence_score=data.confidence_score,
            source=data.source,
            is_pinned=data.is_pinned,
        )
        self.session.add(topic)
        self.session.flush()
        return topic

    def update(self, topic: Topic, data: TopicUpdate) -> Topic:
        payload = asdict(data)
        for key, value in payload.items():
            if value is None:
                continue
            if key in {"state", "priority_mode"}:
                setattr(topic, key, value.value)
            else:
                setattr(topic, key, value)
        self.session.add(topic)
        self.session.flush()
        return topic

    def _next_slug(self, title: str) -> str:
        base_slug = slugify(title)
        slug = base_slug
        index = 2
        while self.get_by_slug(slug) is not None:
            slug = f"{base_slug}-{index}"
            index += 1
        return slug
