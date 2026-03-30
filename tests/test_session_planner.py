from __future__ import annotations

from datetime import date, timezone, datetime

from diary_agent.db.models import Topic
from diary_agent.domain.enums import PriorityMode, TopicState
from diary_agent.services.session_planner import PlannerConfig, SessionPlanner


def _topic(title: str, **kwargs) -> Topic:
    now = datetime.now(timezone.utc)
    base = dict(
        id=title,
        title=title,
        slug=title,
        description="",
        status_summary="",
        state=TopicState.ACTIVE.value,
        priority_mode=PriorityMode.SPORADIC.value,
        cadence_days=None,
        importance_score=0.5,
        energy_score=0.5,
        confidence_score=0.5,
        source="manual",
        is_pinned=False,
        ask_count=0,
        update_count=0,
        last_asked_at=None,
        last_updated_at=None,
        last_touched_at=None,
        created_at=now,
        archived_at=None,
    )
    base.update(kwargs)
    return Topic(**base)


def test_planner_prioritizes_pinned_and_daily_then_due_and_filters_closed() -> None:
    today = date(2026, 3, 29)
    planner = SessionPlanner(PlannerConfig(max_topics=5))
    topics = [
        _topic("Pinned", is_pinned=True),
        _topic("Daily", priority_mode=PriorityMode.DAILY.value),
        _topic(
            "CadenceDue",
            cadence_days=3,
            last_asked_at=datetime(2026, 3, 20, tzinfo=timezone.utc),
            importance_score=0.7,
        ),
        _topic("Recent", last_touched_at=datetime(2026, 3, 28, tzinfo=timezone.utc)),
        _topic("Dormant", state=TopicState.DORMANT.value),
        _topic("Archived", state=TopicState.ARCHIVED.value),
        _topic("Closed", priority_mode=PriorityMode.CLOSED.value),
    ]

    plan = planner.build_plan(topics, today)
    ordered_titles = [c.title for c in plan.ordered_topics]

    assert "Archived" not in ordered_titles
    assert "Closed" not in ordered_titles
    assert ordered_titles[0] in {"Pinned", "Daily"}
    assert any(c.layer == "cadence_due" and c.title == "CadenceDue" for c in plan.ordered_topics)
    assert any(c.layer == "dormant_resurface" and c.title == "Dormant" for c in plan.ordered_topics)


def test_planner_respects_max_topics() -> None:
    today = date(2026, 3, 29)
    planner = SessionPlanner(PlannerConfig(max_topics=2))
    topics = [_topic(f"T{i}", importance_score=0.1 * i) for i in range(6)]

    plan = planner.build_plan(topics, today)

    assert len(plan.ordered_topics) == 2
