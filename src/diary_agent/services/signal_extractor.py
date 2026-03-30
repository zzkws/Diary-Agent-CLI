from __future__ import annotations

import json
import re

from diary_agent.db.models import Topic
from diary_agent.domain.enums import TopicState
from diary_agent.domain.schemas import TopicCreate, TopicSignalExtraction
from diary_agent.llm.base import LLMProvider, LLMRequest

POSITIVE_WORDS = {"good", "great", "happy", "progress", "better", "calm", "excited", "grateful"}
NEGATIVE_WORDS = {"bad", "stuck", "anxious", "stressed", "tired", "worried", "sad", "overwhelmed"}
FOLLOWUP_CUES = {"because", "but", "however", "blocked", "unclear", "maybe", "not sure", "decision"}
TOPIC_HINTS = ("new topic", "i also want to track", "another thing", "also about")


class SignalExtractor:
    """Heuristic extractor with optional LLM augmentation and deterministic fallback."""

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self.llm_provider = llm_provider

    def extract(self, topic: Topic, user_reply: str) -> TopicSignalExtraction:
        llm_result = self._extract_with_llm(topic.title, user_reply)
        if llm_result is not None:
            return llm_result

        clean = user_reply.strip()
        lower = clean.lower()
        mood = self._detect_mood(lower)
        salience = self._salience_score(clean, lower)
        followup_needed = self._needs_followup(lower)

        summary = self._build_summary(topic.title, clean)
        formal_record = self._formal_record(topic.title, clean, mood, salience)
        new_candidates = self._new_topic_candidates(lower)

        state = None
        if "done" in lower or "finished" in lower:
            state = TopicState.DORMANT

        return TopicSignalExtraction(
            topic_status_summary=summary,
            topic_state=state,
            salience_score=salience,
            mood=mood,
            followup_needed=followup_needed,
            followup_reason="can you clarify the key blocker or next decision?" if followup_needed else "",
            formal_memory_record=formal_record,
            new_topic_candidates=new_candidates,
        )

    def extract_free_share(self, user_reply: str) -> TopicSignalExtraction:
        lower = user_reply.lower()
        return TopicSignalExtraction(
            topic_status_summary=user_reply.strip(),
            salience_score=self._salience_score(user_reply, lower),
            mood=self._detect_mood(lower),
            formal_memory_record=f"Free-share note: {user_reply.strip()}",
            new_topic_candidates=self._new_topic_candidates(lower),
        )

    def _extract_with_llm(self, topic_title: str, user_reply: str) -> TopicSignalExtraction | None:
        if self.llm_provider is None or not self.llm_provider.is_available():
            return None

        prompt = (
            "Extract structured diary signal JSON from the user's reply. "
            "Return strict JSON with keys: summary (string), salience (0-1 number), mood (string|null), "
            "followup_needed (bool), followup_reason (string), formal_record (string), state (active|dormant|null), "
            "new_topics (array of short topic titles). "
            f"Topic: {topic_title}. User reply: {user_reply}"
        )
        raw = self.llm_provider.generate_text(
            LLMRequest(
                prompt=prompt,
                system_instruction="You are an extraction engine. Output only valid JSON.",
                temperature=0.1,
            )
        ).strip()
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None

        state_value = data.get("state")
        mapped_state = None
        if state_value == "dormant":
            mapped_state = TopicState.DORMANT
        if state_value == "active":
            mapped_state = TopicState.ACTIVE

        new_topics = []
        for title in data.get("new_topics", []):
            clean_title = str(title).strip()
            if clean_title:
                new_topics.append(TopicCreate(title=clean_title, source="session_extractor"))

        try:
            salience = float(data.get("salience", 0.5))
        except (TypeError, ValueError):
            salience = 0.5

        return TopicSignalExtraction(
            topic_status_summary=str(data.get("summary", "")).strip() or self._build_summary(topic_title, user_reply),
            topic_state=mapped_state,
            salience_score=max(0.0, min(salience, 1.0)),
            mood=data.get("mood") if data.get("mood") else None,
            followup_needed=bool(data.get("followup_needed", False)),
            followup_reason=str(data.get("followup_reason", "")).strip(),
            formal_memory_record=str(data.get("formal_record", "")).strip()
            or self._formal_record(topic_title, user_reply, data.get("mood"), salience),
            new_topic_candidates=new_topics,
        )

    def _detect_mood(self, text: str) -> str | None:
        pos = sum(1 for w in POSITIVE_WORDS if w in text)
        neg = sum(1 for w in NEGATIVE_WORDS if w in text)
        if pos == neg == 0:
            return None
        if pos > neg:
            return "positive"
        if neg > pos:
            return "strained"
        return "mixed"

    def _salience_score(self, raw: str, lower: str) -> float:
        score = 0.4 + min(len(raw) / 400.0, 0.3)
        if any(cue in lower for cue in FOLLOWUP_CUES):
            score += 0.1
        if any(token in lower for token in {"important", "major", "big", "urgent"}):
            score += 0.2
        return round(min(score, 1.0), 2)

    def _needs_followup(self, lower: str) -> bool:
        return any(cue in lower for cue in FOLLOWUP_CUES) and len(lower.split()) > 8

    def _build_summary(self, title: str, reply: str) -> str:
        trimmed = re.sub(r"\s+", " ", reply).strip()
        excerpt = trimmed[:150] + ("..." if len(trimmed) > 150 else "")
        return f"{title}: {excerpt}" if excerpt else title

    def _formal_record(self, title: str, reply: str, mood: str | None, salience: float) -> str:
        mood_part = mood or "undetected"
        cleaned = reply.strip()
        return (
            f"Record|topic={title}; salience={salience:.2f}; mood={mood_part}; "
            f"update={cleaned}"
        )

    def _new_topic_candidates(self, lower: str) -> list[TopicCreate]:
        if not any(hint in lower for hint in TOPIC_HINTS):
            return []

        candidate = lower
        for hint in TOPIC_HINTS:
            if hint in lower:
                candidate = lower.split(hint, maxsplit=1)[-1].strip(" .,:;")
                break
        if not candidate:
            return []
        title = candidate[:50].title()
        return [
            TopicCreate(
                title=title,
                description=f"Auto-captured from free response: {candidate}",
                source="session_extractor",
            )
        ]
