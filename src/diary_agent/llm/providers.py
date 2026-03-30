from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from diary_agent.llm.base import LLMRequest


@dataclass
class DeterministicProvider:
    model: str = "deterministic-v1"
    name: str = "stub"

    def is_available(self) -> bool:
        return True

    def generate_text(self, request: LLMRequest) -> str:
        return ""


@dataclass
class GeminiProvider:
    model: str
    api_key: str
    name: str = "gemini"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate_text(self, request: LLMRequest) -> str:
        if not self.api_key:
            return ""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": request.prompt,
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": request.temperature,
            },
        }
        if request.system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": request.system_instruction}],
            }

        body = json.dumps(payload).encode("utf-8")
        req = Request(endpoint, data=body, method="POST", headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=20) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return ""

        candidates = decoded.get("candidates", [])
        if not candidates:
            return ""
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        for part in parts:
            text = part.get("text", "").strip()
            if text:
                return text
        return ""


@dataclass
class AnthropicPlaceholderProvider:
    model: str
    api_key: str
    name: str = "anthropic"

    def is_available(self) -> bool:
        return False

    def generate_text(self, request: LLMRequest) -> str:
        return ""
