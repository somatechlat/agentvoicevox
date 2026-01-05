"""
Large Language Model (LLM) Workflow Activities
=============================================

This module defines a set of Temporal Workflow Activities specifically designed
for interacting with Large Language Models (LLMs). These activities encapsulate
the logic for generating LLM responses, managing token counts, and executing
LLM-driven tool calls, integrating with various LLM providers like Groq, OpenAI,
and Ollama.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """
    Represents a single chat message in a conversation.

    Attributes:
        role (str): The role of the sender (e.g., 'system', 'user', 'assistant', 'tool').
        content (str): The text content of the message.
    """

    role: str
    content: str


@dataclass
class LLMRequest:
    """
    Defines the parameters for requesting an LLM response generation.

    Attributes:
        tenant_id (str): The ID of the tenant initiating the request.
        session_id (str): A unique identifier for the current session or interaction.
        messages (list[Message]): A list of `Message` objects representing the conversation history.
        model (str): The specific LLM model to use (e.g., 'llama-3.1-8b-instant', 'gpt-4').
        provider (str): The LLM provider to interact with (e.g., 'groq', 'openai', 'ollama').
        max_tokens (int): The maximum number of tokens the LLM should generate in its response.
        temperature (float): The sampling temperature, controlling randomness (0.0 to 1.0).
        system_prompt (Optional[str]): An optional system-level instruction to guide the LLM's behavior.
        tools (list[dict[str, Any]]): A list of tool definitions the LLM can call.
        api_keys (dict[str, str]): A dictionary of API keys, keyed by provider name (e.g., {'groq': '...', 'openai': '...'}).
        ollama_base_url (Optional[str]): The base URL for an Ollama instance, if applicable.
    """

    tenant_id: str
    session_id: str
    messages: list[Message]
    model: str = "llama-3.1-8b-instant"
    provider: str = "groq"
    max_tokens: int = 1024
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    api_keys: dict[str, str] = field(default_factory=dict)
    ollama_base_url: Optional[str] = None


@dataclass
class LLMResult:
    """
    Represents the structured result of an LLM response generation.

    Attributes:
        content (str): The generated text content from the LLM.
        model (str): The actual LLM model that generated the response.
        provider (str): The LLM provider that generated the response.
        input_tokens (int): The number of tokens in the input prompt/messages.
        output_tokens (int): The number of tokens in the generated response.
        total_tokens (int): The sum of input and output tokens.
        processing_time_ms (float): The time taken for LLM processing in milliseconds.
        finish_reason (str): The reason the LLM stopped generating (e.g., 'stop', 'length', 'tool_calls').
        tool_calls (list[dict[str, Any]]): A list of tool calls suggested by the LLM, if any.
    """

    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    processing_time_ms: float
    finish_reason: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TokenUsage:
    """
    Represents token usage statistics.

    Attributes:
        input_tokens (int): Number of tokens in the input.
        output_tokens (int): Number of tokens in the output.
        total_tokens (int): Total number of tokens (input + output).
    """

    input_tokens: int
    output_tokens: int
    total_tokens: int


class LLMActivities:
    """
    A collection of Temporal Workflow Activities for Large Language Model (LLM) operations.

    These activities are designed to be executed within a Temporal workflow,
    providing robust and fault-tolerant interactions with various LLM providers.
    """

    @activity.defn(name="llm_generate_response")
    async def generate_response(
        self,
        request: LLMRequest,
    ) -> LLMResult:
        """
        Generates a response from an LLM based on the provided request parameters.

        This activity dynamically dispatches the request to the appropriate LLM
        provider (Groq, OpenAI, Ollama) and measures the processing time.

        Args:
            request: An `LLMRequest` object containing all necessary parameters
                     for LLM generation.

        Returns:
            An `LLMResult` object with the generated content and usage metadata.

        Raises:
            ValueError: If an unsupported LLM provider is specified in the request.
            Exception: If LLM generation fails for any other reason (e.g., API error).
        """
        start_time = time.time()  # Record start time for latency calculation.

        try:
            if request.provider == "groq":
                result = await self._generate_groq(request)
            elif request.provider == "openai":
                result = await self._generate_openai(request)
            elif request.provider == "ollama":
                result = await self._generate_ollama(request)
            else:
                raise ValueError(f"Unsupported LLM provider: {request.provider}")

            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds.
            result.processing_time_ms = processing_time

            logger.info(
                f"Generated LLM response for session {request.session_id}: "
                f"{result.output_tokens} tokens, {processing_time:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"LLM generation failed for session {request.session_id}: {e}")
            raise  # Re-raise the exception for Temporal to handle.

    async def _generate_groq(self, request: LLMRequest) -> LLMResult:
        """
        Internal helper to generate an LLM response using the Groq API.

        This method handles message formatting, API key retrieval (from `request.api_keys`
        or Django settings), and parsing the Groq API response.
        """
        import httpx
        from django.conf import settings  # Local import to avoid module-level dependency.

        provider_config = settings.LLM_PROVIDERS.get("groq", {})
        api_key = request.api_keys.get("groq") or provider_config.get("api_key", "")
        base_url = provider_config.get("base_url", "https://api.groq.com/openai/v1")
        if not api_key:
            raise ValueError("Groq API key not configured")

        # Build messages adhering to the Groq/OpenAI chat completion API format.
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
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
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses.
            data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        # Extract tool calls if the LLM suggested any.
        tool_calls = []
        if choice.get("message", {}).get("tool_calls"):
            for tc in choice["message"]["tool_calls"]:
                tool_calls.append(
                    {
                        "id": tc["id"],
                        "type": tc["type"],
                        "function": tc["function"],
                    }
                )

        return LLMResult(
            content=choice["message"].get("content", ""),
            model=data.get("model", request.model),
            provider="groq",
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            processing_time_ms=0,  # Set by the caller (generate_response).
            finish_reason=choice.get("finish_reason", "stop"),
            tool_calls=tool_calls,
        )

    async def _generate_openai(self, request: LLMRequest) -> LLMResult:
        """
        Internal helper to generate an LLM response using the OpenAI API.

        This method handles message formatting, API key retrieval (from `request.api_keys`
        or Django settings), and parsing the OpenAI API response.
        """
        import httpx
        from django.conf import settings  # Local import.

        provider_config = settings.LLM_PROVIDERS.get("openai", {})
        api_key = request.api_keys.get("openai") or provider_config.get("api_key", "")
        base_url = provider_config.get("base_url", "https://api.openai.com/v1")
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
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

        tool_calls = []
        if choice.get("message", {}).get("tool_calls"):
            for tc in choice["message"]["tool_calls"]:
                tool_calls.append(
                    {
                        "id": tc["id"],
                        "type": tc["type"],
                        "function": tc["function"],
                    }
                )

        return LLMResult(
            content=choice["message"].get("content", ""),
            model=data.get("model", request.model),
            provider="openai",
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            processing_time_ms=0,
            finish_reason=choice.get("finish_reason", "stop"),
            tool_calls=tool_calls,
        )

    async def _generate_ollama(self, request: LLMRequest) -> LLMResult:
        """
        Internal helper to generate an LLM response using an Ollama API.

        This method handles message formatting, base URL retrieval (from `request`
        or Django settings), and parsing the Ollama API response.
        """
        import httpx
        from django.conf import settings  # Local import.

        base_url = (
            request.ollama_base_url
            or request.api_keys.get("ollama_base_url")
            or settings.LLM_PROVIDERS.get("ollama", {}).get("base_url", "")
        )
        if not base_url:
            raise ValueError("Ollama base URL not configured")

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": request.model,
                    "messages": messages,
                    "stream": False,  # Only non-streaming generation is supported here.
                    "options": {
                        "num_predict": request.max_tokens,  # Ollama's equivalent of max_tokens.
                        "temperature": request.temperature,
                    },
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        # Ollama API response for token usage is not standardized across versions,
        # so these metrics are often not directly available or are approximated.
        return LLMResult(
            content=content,
            model=request.model,
            provider="ollama",
            input_tokens=0,  # Token metrics not easily available from Ollama's default /api/chat.
            output_tokens=0,
            total_tokens=0,
            processing_time_ms=0,
            finish_reason="stop",
            tool_calls=[],  # Ollama's tool calling support varies.
        )

    @activity.defn(name="llm_count_tokens")
    async def count_tokens(
        self,
        text: str,
        model: str = "llama-3.1-8b-instant",
    ) -> TokenUsage:
        """
        Counts the number of tokens in a given text string.

        This activity uses `tiktoken` for OpenAI models for precise counting.
        For other models or if `tiktoken` is unavailable, it provides a rough
        estimation.

        Args:
            text: The text content to tokenize.
            model: The LLM model name, used to select the correct tokenizer encoding.

        Returns:
            A `TokenUsage` object containing the estimated or precise token count.
        """
        try:
            import tiktoken  # Local import for optional dependency.

            try:
                # Attempt to get encoding specific to the model.
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to a common encoding if model-specific one is not found.
                encoding = tiktoken.get_encoding("cl100k_base")

            tokens = encoding.encode(text)
            return TokenUsage(
                input_tokens=len(tokens),
                output_tokens=0,  # This activity only counts input tokens.
                total_tokens=len(tokens),
            )

        except ImportError:
            # Provide a rough estimate if `tiktoken` is not installed.
            # Common rough estimate: ~4 characters per token on average for English.
            estimated_tokens = len(text) // 4
            logger.warning("tiktoken not available, using rough token estimation.")
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
        tool_args: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Executes a specific tool (function call) as dictated by an LLM.

        This activity integrates with a function calling engine to validate
        and execute external functions or API calls.

        Args:
            tenant_id: The ID of the tenant.
            session_id: The ID of the session.
            tool_name: The name of the tool/function to execute.
            tool_args: A dictionary of arguments for the tool.

        Returns:
            A dictionary containing the result of the tool execution.

        Raises:
            ValueError: If the tool arguments are invalid.
            RuntimeError: If the tool execution itself fails.
        """
        logger.info(f"Executing tool '{tool_name}' for session {session_id}")

        from apps.realtime.services.function_calling import get_function_engine  # Local import.

        engine = get_function_engine()
        is_valid, error = engine.validate_arguments(tool_name, tool_args)
        if not is_valid:
            raise ValueError(error or "Invalid tool arguments")

        result = await engine.execute_function(tool_name, tool_args)
        if not result.get("success"):
            raise RuntimeError(result.get("error") or "Tool execution failed")

        return result
