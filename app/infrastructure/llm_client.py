"""OpenAI client wrapper.

Thin adapter around the OpenAI Python SDK.  The RAG service calls this;
nothing else in the codebase should import ``openai`` directly.
Centralising the client here makes it trivial to swap providers later.
"""

from __future__ import annotations

from openai import OpenAI

from app.core.config import settings


class LLMClient:
    """Wraps the OpenAI chat-completions API with structured-output support."""

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Copy .env.example → .env and add your key."
            )
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """Return the assistant's reply as a raw string."""
        response = self._client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
# Constructed lazily so that missing API keys only raise at evaluation time,
# not at import time (important for tests that don't hit the LLM).
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client  # noqa: PLW0603
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
