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
        summary = f"Covered {len(unique_topics)} topics today, led by {', '.join(unique_topics[:3])}."

        continuity_lines = [
            "- Carry unresolved decisions into tomorrow's check-in.",
            "- Keep momentum on high-salience topics with tighter cadence.",
        ]
        if new_topics:
            continuity_lines.append(f"- New topics captured: {', '.join(new_topics)}.")

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
