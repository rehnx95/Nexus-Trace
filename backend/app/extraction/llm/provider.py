import os
from typing import Protocol

import httpx


class LLMProvider(Protocol):
    def complete(self, prompt: str) -> str:
        ...


class OpenAICompatibleProvider:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = (
            base_url
            or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        ).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL", "")
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        if not self.model:
            raise ValueError("LLM_MODEL is required when LLM extraction is enabled")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices")
        if not choices:
            raise ValueError("LLM response did not contain choices")
        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("LLM response did not contain message content")
        return content
