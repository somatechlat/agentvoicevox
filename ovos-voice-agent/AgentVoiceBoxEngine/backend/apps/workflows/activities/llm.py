"""
LLM workflow activities for agent voice responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx
from django.conf import settings
from temporalio import activity


@dataclass
class Message:
    """Chat message passed to an LLM provider."""

    role: str
    content: str


@dataclass
class LLMRequest:
    """Provider-neutral LLM request."""

    tenant_id: str
    session_id: str
    messages: list[Message]
    model: str
    provider: str
    max_tokens: int
    temperature: float
    system_prompt: str = ""
    tools: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class LLMResult:
    """Provider-neutral LLM result."""

    content: str
    input_tokens: int
    output_tokens: int
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


class LLMActivities:
    """Activities that call configured LLM providers."""

    @activity.defn
    async def generate_response(self, request: LLMRequest) -> LLMResult:
        provider = request.provider or settings.LLM_WORKER["DEFAULT_PROVIDER"]
        if provider == "openai":
            return await self._openai_chat(request)
        if provider == "groq":
            return await self._groq_chat(request)
        if provider == "ollama":
            return await self._ollama_chat(request)
        raise RuntimeError(f"Unsupported LLM provider: {provider}")

    async def _openai_chat(self, request: LLMRequest) -> LLMResult:
        from integrations.vault import get_app_secret

        api_key = (
            get_app_secret("OPENAI_API_KEY")
            or settings.LLM_PROVIDERS["openai"]["api_key"]
        )
        if not api_key:
            raise RuntimeError("OpenAI API key is not configured")
        return await self._openai_compatible_chat(
            request=request,
            base_url=settings.LLM_PROVIDERS["openai"]["base_url"].rstrip("/"),
            api_key=api_key,
        )

    async def _groq_chat(self, request: LLMRequest) -> LLMResult:
        from integrations.vault import get_app_secret

        api_key = (
            get_app_secret("GROQ_API_KEY")
            or settings.LLM_PROVIDERS["groq"]["api_key"]
        )
        if not api_key:
            raise RuntimeError("Groq API key is not configured")
        return await self._openai_compatible_chat(
            request=request,
            base_url=settings.LLM_PROVIDERS["groq"]["base_url"].rstrip("/"),
            api_key=api_key,
        )

    async def _openai_compatible_chat(
        self,
        request: LLMRequest,
        base_url: str,
        api_key: str,
    ) -> LLMResult:
        messages = self._messages(request)
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.tools:
            payload["tools"] = request.tools

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            response.raise_for_status()
        data = response.json()
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})
        return LLMResult(
            content=message.get("content") or "",
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            tool_calls=message.get("tool_calls") or [],
        )

    async def _ollama_chat(self, request: LLMRequest) -> LLMResult:
        base_url = settings.LLM_PROVIDERS["ollama"]["base_url"].rstrip("/")
        payload = {
            "model": request.model,
            "messages": self._messages(request),
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{base_url}/api/chat", json=payload)
            response.raise_for_status()
        data = response.json()
        content = data.get("message", {}).get("content", "")
        return LLMResult(
            content=content,
            input_tokens=int(data.get("prompt_eval_count") or 0),
            output_tokens=int(data.get("eval_count") or 0),
        )

    def _messages(self, request: LLMRequest) -> list[dict[str, str]]:
        messages = [
            {"role": item.role, "content": item.content}
            for item in request.messages
        ]
        if request.system_prompt:
            messages.insert(0, {"role": "system", "content": request.system_prompt})
        return messages
