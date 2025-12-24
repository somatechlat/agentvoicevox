"""
LLM (Large Language Model) activities for Temporal workflows.

Handles response generation via Groq, OpenAI, or other LLM providers.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A chat message."""

    role: str  # system, user, assistant
    content: str


@dataclass
class LLMRequest:
    """Request for LLM response generation."""

    tenant_id: str
    session_id: str
    messages: List[Message]
    model: str = "llama-3.1-8b-instant"
    provider: str = "groq"
    max_tokens: int = 1024
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    tools: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class LLMResult:
    """Result of LLM response generation."""

    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    processing_time_ms: float
    finish_reason: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TokenUsage:
    """Token usage statistics."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


class LLMActivities:
    """
    LLM activities for voice processing workflows.

    Activities:
    - generate_response: Generate LLM response
    - stream_response: Generate streaming LLM response
    - count_tokens: Count tokens in text
    """

    @activity.defn(name="llm_generate_response")
    async def generate_response(
        self,
        request: LLMRequest,
    ) -> LLMResult:
        """
        Generate LLM response using configured provider.

        Args:
            request: LLMRequest with messages and config

        Returns:
            LLMResult with generated response and metadata

        Raises:
            Exception: If generation fails
        """
        import time

        start_time = time.time()

        try:
            if request.provider == "groq":
                result = await self._generate_groq(request)
            elif request.provider == "openai":
                result = await self._generate_openai(request)
            else:
                raise ValueError(f"Unsupported LLM provider: {request.provider}")

            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time

            logger.info(
                f"Generated LLM response for session {request.session_id}: "
                f"{result.output_tokens} tokens, {processing_time:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(
                f"LLM generation failed for session {request.session_id}: {e}"
            )
            raise

    async def _generate_groq(self, request: LLMRequest) -> LLMResult:
        """Generate response using Groq API."""
        from django.conf import settings
        import httpx

        api_key = settings.LLM_PROVIDERS.get("groq", {}).get("api_key", "")
        if not api_key:
            raise ValueError("Groq API key not configured")

        # Build messages
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": request.model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "tools": request.tools if request.tools else None,
                },
                timeout=60.0,
            )

            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        # Extract tool calls if present
        tool_calls = []
        if choice.get("message", {}).get("tool_calls"):
            for tc in choice["message"]["tool_calls"]:
                tool_calls.append({
                    "id": tc["id"],
                    "type": tc["type"],
                    "function": tc["function"],
                })

        return LLMResult(
            content=choice["message"].get("content", ""),
            model=data.get("model", request.model),
            provider="groq",
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            processing_time_ms=0,  # Set by caller
            finish_reason=choice.get("finish_reason", "stop"),
            tool_calls=tool_calls,
        )

    async def _generate_openai(self, request: LLMRequest) -> LLMResult:
        """Generate response using OpenAI API."""
        from django.conf import settings
        import httpx

        api_key = settings.LLM_PROVIDERS.get("openai", {}).get("api_key", "")
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        # Build messages
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": request.model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "tools": request.tools if request.tools else None,
                },
                timeout=60.0,
            )

            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        # Extract tool calls if present
        tool_calls = []
        if choice.get("message", {}).get("tool_calls"):
            for tc in choice["message"]["tool_calls"]:
                tool_calls.append({
                    "id": tc["id"],
                    "type": tc["type"],
                    "function": tc["function"],
                })

        return LLMResult(
            content=choice["message"].get("content", ""),
            model=data.get("model", request.model),
            provider="openai",
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            processing_time_ms=0,  # Set by caller
            finish_reason=choice.get("finish_reason", "stop"),
            tool_calls=tool_calls,
        )

    @activity.defn(name="llm_count_tokens")
    async def count_tokens(
        self,
        text: str,
        model: str = "llama-3.1-8b-instant",
    ) -> TokenUsage:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for
            model: Model to use for tokenization

        Returns:
            TokenUsage with token count
        """
        try:
            # Use tiktoken for OpenAI models
            import tiktoken

            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base for unknown models
                encoding = tiktoken.get_encoding("cl100k_base")

            tokens = encoding.encode(text)
            return TokenUsage(
                input_tokens=len(tokens),
                output_tokens=0,
                total_tokens=len(tokens),
            )

        except ImportError:
            # Rough estimate if tiktoken not available
            # ~4 chars per token on average
            estimated_tokens = len(text) // 4
            return TokenUsage(
                input_tokens=estimated_tokens,
                output_tokens=0,
                total_tokens=estimated_tokens,
            )

    @activity.defn(name="llm_execute_tool")
    async def execute_tool(
        self,
        tenant_id: str,
        session_id: str,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a tool call from LLM.

        Args:
            tenant_id: Tenant identifier
            session_id: Session identifier
            tool_name: Name of tool to execute
            tool_args: Tool arguments

        Returns:
            Tool execution result
        """
        logger.info(
            f"Executing tool {tool_name} for session {session_id}"
        )

        # Tool implementations would go here
        # For now, return a placeholder
        return {
            "tool": tool_name,
            "result": f"Tool {tool_name} executed with args: {tool_args}",
            "success": True,
        }
