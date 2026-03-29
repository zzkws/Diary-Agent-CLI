from __future__ import annotations

from diary_agent.db.models import Topic


class QuestionComposer:
    def opening_message(self, topic_count: int) -> str:
        return (
            f"Hey — quick daily check-in. I picked {topic_count} threads to revisit so this stays light. "
            "How are you feeling tonight?"
        )

    def topic_kickoff_question(self, topic: Topic) -> str:
        if topic.status_summary:
            return f"On {topic.title}: last I remember, {topic.status_summary}. What's the latest today?"
        return f"How did things go with {topic.title} today?"

    def followup_question(self, topic: Topic, reason: str) -> str:
        if reason:
            return f"Got it. One quick follow-up on {topic.title}: {reason}"
        return f"One quick follow-up on {topic.title}: what feels most important to remember from this update?"

    def free_share_question(self) -> str:
        return "Before we wrap: anything new, or anything else you want me to remember for later?"

    def closing_message(self) -> str:
        return "Thanks — I logged this and drafted today's entry. Good night."
