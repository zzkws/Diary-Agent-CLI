from __future__ import annotations

from diary_agent.db.models import Topic


class QuestionComposer:
    def opening_message(self, topic_count: int) -> str:
        return (
            f"Hey — quick nightly check-in. I picked {topic_count} topics so this stays lightweight and focused."
        )

    def topic_kickoff_question(self, topic: Topic) -> str:
        if topic.status_summary:
            return f"On {topic.title}, last I noted: {topic.status_summary} What changed today?"
        return f"How did {topic.title} go today?"

    def followup_question(self, topic: Topic, reason: str) -> str:
        if reason:
            return f"Helpful. One quick follow-up on {topic.title}: {reason}"
        return f"One quick follow-up on {topic.title}: what's the key thing I should carry forward?"

    def free_share_question(self) -> str:
        return "Before we wrap, anything new or anything else I should remember for future check-ins?"

    def closing_message(self) -> str:
        return "Thanks — I've saved this and drafted today's diary entry. Good night."
