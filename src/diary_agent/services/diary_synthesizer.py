from __future__ import annotations

from collections import Counter

from diary_agent.db.models import DailySession, SessionTopicQueue, Topic, TopicHistoryItem


class DiarySynthesizer:
    def synthesize(
        self,
        daily_session: DailySession,
        queue_items: list[SessionTopicQueue],
        topics_by_id: dict[str, Topic],
        history_items: list[TopicHistoryItem],
    ) -> tuple[str, str, str, str | None]:
        if not history_items:
            summary = "Light check-in completed with no substantial updates."
            body = "# Daily Diary\n\nNo significant updates were captured today."
            return "Quiet check-in", summary, body, None

        top_updates = sorted(history_items, key=lambda item: item.salience_score, reverse=True)[:4]
        highlights = []
        for item in top_updates:
            topic_title = topics_by_id.get(item.topic_id).title if item.topic_id in topics_by_id else "General"
            highlights.append(f"- **{topic_title}**: {item.agent_record}")

        mood_counter = Counter(item.mood for item in history_items if item.mood)
        mood = mood_counter.most_common(1)[0][0] if mood_counter else None
        topics_covered = [topics_by_id[item.topic_id].title for item in queue_items if item.topic_id in topics_by_id]
        summary = f"Checked in across {len(topics_covered)} topics. Main focus: {', '.join(topics_covered[:3])}."

        body = "\n".join(
            [
                f"# Diary — {daily_session.session_date.isoformat()}",
                "",
                "## Quick Summary",
                summary,
                "",
                "## Key Updates",
                *highlights,
                "",
                "## Continuity Notes",
                "- Carry forward unresolved items into tomorrow's check-in.",
                "- Preserve candidate topics discovered in free-share responses.",
            ]
        )

        title = f"Daily reflection: {daily_session.session_date.isoformat()}"
        return title, summary, body, mood
