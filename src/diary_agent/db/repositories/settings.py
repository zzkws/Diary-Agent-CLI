from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from diary_agent.db.models import AgentSetting
from diary_agent.domain.schemas import AgentSettingCreate


class AgentSettingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_default(self) -> AgentSetting | None:
        stmt = select(AgentSetting).order_by(AgentSetting.created_at.asc())
        return self.session.scalar(stmt)

    def create_default(self, data: AgentSettingCreate) -> AgentSetting:
        setting = AgentSetting(
            llm_provider=data.llm_provider,
            llm_model=data.llm_model,
            temperature=data.temperature,
            max_topics_per_session=data.max_topics_per_session,
            max_followups_per_topic=data.max_followups_per_topic,
            default_question_style=data.default_question_style,
            diary_style=data.diary_style,
            ask_for_free_share=data.ask_for_free_share,
        )
        self.session.add(setting)
        self.session.flush()
        return setting
