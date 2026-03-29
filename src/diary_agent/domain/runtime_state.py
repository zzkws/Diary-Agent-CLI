from __future__ import annotations

from dataclasses import dataclass, field

from diary_agent.domain.enums import RuntimePhase


@dataclass(slots=True)
class RuntimeSessionState:
    session_id: str
    phase: RuntimePhase
    current_topic_id: str | None = None
    selected_topic_ids: list[str] = field(default_factory=list)
    completed_topic_ids: list[str] = field(default_factory=list)
    skipped_topic_ids: list[str] = field(default_factory=list)
    new_topic_candidate_ids: list[str] = field(default_factory=list)
    turn_count: int = 0
    current_topic_followup_count: int = 0
    max_topics: int = 5
    max_followups_per_topic: int = 1
