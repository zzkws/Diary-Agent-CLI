from __future__ import annotations

from collections import Counter

from diary_agent.db.models import DailySession, SessionTopicQueue, Topic, TopicHistoryItem
from diary_agent.llm.base import LLMProvider, LLMRequest


class DiarySynthesizer:
    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self.llm_provider = llm_provider

    def synthesize(
        self,
        daily_session: DailySession,
        queue_items: list[SessionTopicQueue],
        topics_by_id: dict[str, Topic],
        history_items: list[TopicHistoryItem],
    ) -> tuple[str, str, str, str | None]:
        if not history_items:
            summary = "Short check-in completed. No substantial updates were captured today."
            body = "# Diary\n\nNo significant updates were captured today."
            return "Quiet check-in", summary, body, None

        top_updates = sorted(history_items, key=lambda item: item.salience_score, reverse=True)[:5]
        highlights = []
        for item in top_updates:
            topic_title = topics_by_id.get(item.topic_id).title if item.topic_id in topics_by_id else "General"
            highlights.append(f"- **{topic_title}** — {item.agent_record}")

        mood_counter = Counter(item.mood for item in history_items if item.mood)
        mood = mood_counter.most_common(1)[0][0] if mood_counter else None

        unique_topics = []
        for item in queue_items:
            topic = topics_by_id.get(item.topic_id)
            if topic and topic.title not in unique_topics:
                unique_topics.append(topic.title)

        new_topics = [topics_by_id[item.topic_id].title for item in queue_items if item.was_new_topic and item.topic_id in topics_by_id]
        deterministic_summary = f"Covered {len(unique_topics)} topics today, led by {', '.join(unique_topics[:3])}."

        continuity_lines = [
            "- Carry unresolved decisions into tomorrow's check-in.",
            "- Keep momentum on high-salience topics with tighter cadence.",
        ]
        if new_topics:
            continuity_lines.append(f"- New topics captured: {', '.join(new_topics)}.")

        summary = self._llm_summary_or_fallback(deterministic_summary, top_updates)

        body = "\n".join(
            [
                f"# Diary — {daily_session.session_date.isoformat()}",
                "",
                "## Summary",
                summary,
                "",
                "## Topic Updates",
                *highlights,
                "",
                "## Continuity",
                *continuity_lines,
            ]
        )

        title = f"Daily reflection: {daily_session.session_date.isoformat()}"
        return title, summary, body, mood

    def _llm_summary_or_fallback(self, fallback: str, top_updates: list[TopicHistoryItem]) -> str:
        if self.llm_provider is None or not self.llm_provider.is_available():
            return fallback

        updates = "\n".join([f"- {item.agent_record}" for item in top_updates])
        prompt = (
            "Write a concise 1-2 sentence daily diary summary from these updates. "
            "Keep it grounded and reflective, no poetry.\n"
            f"Updates:\n{updates}"
        )
        generated = self.llm_provider.generate_text(
            LLMRequest(
                prompt=prompt,
                system_instruction="You write concise daily summary notes.",
                temperature=0.2,
            )
        ).strip()
        return generated if generated else fallback
