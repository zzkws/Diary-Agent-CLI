from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    system_instruction: str = ""
    temperature: float = 0.2


class LLMProvider(Protocol):
    name: str
    model: str

    def is_available(self) -> bool:
        ...

    def generate_text(self, request: LLMRequest) -> str:
        ...
