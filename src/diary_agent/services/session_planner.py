from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from diary_agent.db.models import Topic
from diary_agent.domain.enums import PriorityMode, TopicState
from diary_agent.domain.schemas import PlannerTopicCandidate, SessionPlan


@dataclass(slots=True)
class PlannerConfig:
    max_topics: int = 5


class SessionPlanner:
    """Layered, inspectable topic planner."""

    def __init__(self, config: PlannerConfig | None = None) -> None:
        self.config = config or PlannerConfig()

    def build_plan(self, topics: list[Topic], today: date) -> SessionPlan:
        candidates: list[PlannerTopicCandidate] = []
        for topic in topics:
            if topic.state == TopicState.ARCHIVED.value or topic.priority_mode == PriorityMode.CLOSED.value:
                continue
            days_since_asked = None
            if topic.last_asked_at is not None:
                days_since_asked = (today - topic.last_asked_at.date()).days
            cadence_due = bool(topic.cadence_days and (days_since_asked is None or days_since_asked >= topic.cadence_days))
            layer, score, reason = self._score(topic, cadence_due, days_since_asked)
            candidates.append(
                PlannerTopicCandidate(
                    topic_id=topic.id,
                    title=topic.title,
                    score=score,
                    layer=layer,
                    reason=reason,
                    cadence_due=cadence_due,
                    days_since_asked=days_since_asked,
                )
            )

        ordered = sorted(candidates, key=lambda c: (-c.score, c.title.lower()))[: self.config.max_topics]
        return SessionPlan(ordered_topics=ordered, max_topics=self.config.max_topics)

    def _score(self, topic: Topic, cadence_due: bool, days_since_asked: int | None) -> tuple[str, float, str]:
        if topic.is_pinned or topic.priority_mode == PriorityMode.DAILY.value:
            return "pinned_daily", 100.0 + topic.importance_score * 10.0, "Pinned/daily topic"

        if cadence_due and topic.state == TopicState.ACTIVE.value:
            due_bonus = min((days_since_asked or topic.cadence_days or 1) / (topic.cadence_days or 1), 2.0)
            return (
                "cadence_due",
                80.0 + due_bonus * 8.0 + topic.importance_score * 5.0,
                f"Cadence due (every {topic.cadence_days}d)",
            )

        if topic.last_touched_at:
            return (
                "recent_salient",
                60.0 + topic.importance_score * 10.0 + topic.energy_score * 5.0,
                "Recently updated/salient",
            )

        if topic.state == TopicState.DORMANT.value:
            return "dormant_resurface", 40.0 + topic.importance_score * 5.0, "Dormant resurfacing"

        return "default", 30.0 + topic.importance_score * 5.0, "General active topic"
