from __future__ import annotations

from diary_agent.db.models import Topic
from diary_agent.llm.base import LLMProvider, LLMRequest


class QuestionComposer:
    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self.llm_provider = llm_provider

    def opening_message(self, topic_count: int) -> str:
        fallback = f"Hey — quick nightly check-in. I picked {topic_count} topics so this stays lightweight and focused."
        prompt = (
            "Write a warm one-sentence nightly check-in opener for a diary assistant. "
            f"Mention {topic_count} topics. Keep it concise and natural."
        )
        return self._generate_or_fallback(prompt, fallback)

    def topic_kickoff_question(self, topic: Topic) -> str:
        if topic.status_summary:
            fallback = f"On {topic.title}, last I noted: {topic.status_summary} What changed today?"
            prompt = (
                "Write one natural, lightweight check-in question about this topic. "
                f"Topic: {topic.title}. Prior summary: {topic.status_summary}."
            )
            return self._generate_or_fallback(prompt, fallback)
        fallback = f"How did {topic.title} go today?"
        prompt = f"Write one natural check-in question for topic: {topic.title}."
        return self._generate_or_fallback(prompt, fallback)

    def followup_question(self, topic: Topic, reason: str) -> str:
        if reason:
            fallback = f"Helpful. One quick follow-up on {topic.title}: {reason}"
            prompt = (
                "Write one short follow-up question that asks for clarification. "
                f"Topic: {topic.title}. Reason: {reason}."
            )
            return self._generate_or_fallback(prompt, fallback)
        fallback = f"One quick follow-up on {topic.title}: what's the key thing I should carry forward?"
        prompt = f"Write one short follow-up question for topic {topic.title} to capture carry-forward context."
        return self._generate_or_fallback(prompt, fallback)

    def free_share_question(self) -> str:
        fallback = "Before we wrap, anything new or anything else I should remember for future check-ins?"
        prompt = "Write one brief end-of-session free-share question for a diary assistant."
        return self._generate_or_fallback(prompt, fallback)

    def closing_message(self) -> str:
        fallback = "Thanks — I've saved this and drafted today's diary entry. Good night."
        prompt = "Write one short warm closing line for a diary check-in."
        return self._generate_or_fallback(prompt, fallback)

    def _generate_or_fallback(self, prompt: str, fallback: str) -> str:
        if self.llm_provider is None or not self.llm_provider.is_available():
            return fallback
        generated = self.llm_provider.generate_text(
            LLMRequest(
                prompt=prompt,
                system_instruction="You are a concise diary interviewer. Output one sentence only.",
                temperature=0.3,
            )
        ).strip()
        return generated if generated else fallback
