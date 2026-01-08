"""
Run the LLM worker for realtime sessions.
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import time
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.workflows.redis_client import RedisClient

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for provider failover."""

    threshold: int
    timeout: float
    failure_count: int = 0
    last_failure_time: float = 0.0
    state: CircuitState = CircuitState.CLOSED

    def record_success(self) -> None:
        """Records a successful operation, resetting failure count and state."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """
        Records a failed operation, incrementing failure count.
        Opens the circuit if the failure threshold is met.
        """
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker opened", extra={"failures": self.failure_count}
            )

    def can_execute(self) -> bool:
        """
        Checks if an operation can be executed based on the current circuit state.

        Returns:
            bool: True if execution is allowed, False otherwise.
        """
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker half-open, testing recovery")
                return True
            return False
        return True


class LLMProvider:
    """Base class for LLM providers, defining common interface and lifecycle methods."""

    def __init__(self) -> None:
        """Initializes the LLMProvider."""
        self._client: Optional["httpx.AsyncClient"] = None

    async def start(self) -> None:
        """Starts the provider, initializing any necessary clients or connections."""
        import httpx

        self._client = httpx.AsyncClient(timeout=60.0)

    async def stop(self) -> None:
        """Stops the provider, closing any open clients or connections."""
        if self._client:
            await self._client.aclose()

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """
        Abstract method to generate a streaming response from the LLM.

        Args:
            messages: A list of message dictionaries representing the conversation history.
            model: The specific LLM model to use.
            max_tokens: The maximum number of tokens to generate.
            temperature: The sampling temperature for creativity.

        Yields:
            str: Chunks of the generated text response.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """
        Generates a streaming response from the OpenAI API.

        Args:
            messages: A list of message dictionaries representing the conversation history.
            model: The specific OpenAI model to use.
            max_tokens: The maximum number of tokens to generate.
            temperature: The sampling temperature for creativity.

        Yields:
            str: Chunks of the generated text response.

        Raises:
            RuntimeError: If the OpenAI client is not initialized or not configured.
            httpx.HTTPStatusError: If the API call returns a non-2xx status code.
        """
        if not self._client:
            raise RuntimeError("OpenAI client not initialized")

        api_key = settings.LLM_PROVIDERS["openai"]["api_key"]
        base_url = settings.LLM_PROVIDERS["openai"]["base_url"]
        if not api_key or not base_url:
            raise RuntimeError("OpenAI not configured")

        async with self._client.stream(
            "POST",
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


class GroqProvider(LLMProvider):
    """Groq API provider."""

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """
        Generates a streaming response from the Groq API.

        Args:
            messages: A list of message dictionaries representing the conversation history.
            model: The specific Groq model to use.
            max_tokens: The maximum number of tokens to generate.
            temperature: The sampling temperature for creativity.

        Yields:
            str: Chunks of the generated text response.

        Raises:
            RuntimeError: If the Groq client is not initialized or not configured.
            httpx.HTTPStatusError: If the API call returns a non-2xx status code.
        """
        if not self._client:
            raise RuntimeError("Groq client not initialized")

        api_key = settings.LLM_PROVIDERS["groq"]["api_key"]
        base_url = settings.LLM_PROVIDERS["groq"]["base_url"]
        if not api_key or not base_url:
            raise RuntimeError("Groq not configured")

        async with self._client.stream(
            "POST",
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


class OllamaProvider(LLMProvider):
    """Ollama (self-hosted) provider."""

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """
        Generates a streaming response from a self-hosted Ollama instance.

        Args:
            messages: A list of message dictionaries representing the conversation history.
            model: The specific Ollama model to use.
            max_tokens: The maximum number of tokens to generate.
            temperature: The sampling temperature for creativity.

        Yields:
            str: Chunks of the generated text response.

        Raises:
            RuntimeError: If the Ollama client is not initialized or not configured.
            httpx.HTTPStatusError: If the API call returns a non-2xx status code.
        """
        if not self._client:
            raise RuntimeError("Ollama client not initialized")

        base_url = settings.LLM_PROVIDERS["ollama"]["base_url"]
        if not base_url:
            raise RuntimeError("Ollama base URL not configured")

        async with self._client.stream(
            "POST",
            f"{base_url.rstrip('/')}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": True,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue


class LLMWorker:
    """
    LLM worker with provider failover and streaming capabilities.

    This worker consumes LLM requests from a Redis stream, routes them to
    appropriate LLM providers (OpenAI, Groq, Ollama) with circuit breaker
    failover, and publishes streaming responses back to a Redis channel.
    """

    def __init__(self) -> None:
        """Initializes the LLM worker with Redis client, providers, and circuit breakers."""
        self._redis = RedisClient()
        self._running = False
        self._tasks: set[asyncio.Task] = set()
        self._worker_id = f"llm-{uuid.uuid4().hex[:8]}"

        self._providers: dict[str, LLMProvider] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._provider_priority = settings.LLM_WORKER["PROVIDER_PRIORITY"]

        self._requests_total = 0
        self._requests_failed = 0
        self._tokens_generated = 0

    async def start(self) -> None:
        """
        Starts the LLM worker, establishing Redis connection, initializing
        LLM providers, and ensuring the consumer group exists.
        """
        logger.info("Starting LLM worker", extra={"worker_id": self._worker_id})
        await self._redis.connect()
        await self._init_providers()
        await self._ensure_consumer_group()
        self._running = True
        logger.info("LLM worker started", extra={"worker_id": self._worker_id})

    async def stop(self) -> None:
        """
        Stops the LLM worker, gracefully shutting down all active tasks,
        LLM providers, and closing the Redis connection.
        """
        logger.info("Stopping LLM worker", extra={"worker_id": self._worker_id})
        self._running = False

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        for provider in self._providers.values():
            await provider.stop()

        await self._redis.disconnect()
        logger.info(
            "LLM worker stopped",
            extra={
                "worker_id": self._worker_id,
                "requests_total": self._requests_total,
                "requests_failed": self._requests_failed,
                "tokens_generated": self._tokens_generated,
            },
        )

    async def _init_providers(self) -> None:
        """
        Initializes and starts all configured LLM providers and their
        associated circuit breakers based on the provider priority.
        """
        provider_map = {
            "openai": OpenAIProvider,
            "groq": GroqProvider,
            "ollama": OllamaProvider,
        }

        for name in self._provider_priority:
            provider_cls = provider_map.get(name)
            if not provider_cls:
                continue
            provider = provider_cls()
            await provider.start()
            self._providers[name] = provider
            self._circuit_breakers[name] = CircuitBreaker(
                threshold=settings.LLM_WORKER["CIRCUIT_BREAKER_THRESHOLD"],
                timeout=settings.LLM_WORKER["CIRCUIT_BREAKER_TIMEOUT"],
            )
            logger.info("LLM provider initialized", extra={"provider": name})

    async def _ensure_consumer_group(self) -> None:
        """
        Ensures the Redis consumer group for LLM requests exists.
        Creates it if it does not already exist.
        """
        client = self._redis.client
        stream = settings.LLM_WORKER["STREAM_REQUESTS"]
        group = settings.LLM_WORKER["GROUP_WORKERS"]

        try:
            await client.xgroup_create(stream, group, id="0", mkstream=True)
            logger.info("Created consumer group", extra={"group": group})
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                logger.warning(
                    "Failed to create consumer group", extra={"error": str(exc)}
                )

    async def run(self) -> None:
        """
        Main loop of the LLM worker, continuously reading and processing
        LLM requests from the Redis stream.
        """
        client = self._redis.client
        stream = settings.LLM_WORKER["STREAM_REQUESTS"]
        group = settings.LLM_WORKER["GROUP_WORKERS"]

        while self._running:
            try:
                messages = await client.xreadgroup(
                    group,
                    self._worker_id,
                    {stream: ">"},
                    count=1,
                    block=1000,
                )
                if not messages:
                    continue

                for _, stream_messages in messages:
                    for message_id, data in stream_messages:
                        task = asyncio.create_task(
                            self._process_message(message_id, data)
                        )
                        self._tasks.add(task)
                        task.add_done_callback(self._tasks.discard)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(
                    "Worker loop error", extra={"error": str(exc)}, exc_info=True
                )
                await asyncio.sleep(1)

    async def _process_message(self, message_id: str, data: dict[str, Any]) -> None:
        """
        Processes a single LLM request message from the Redis stream.

        This method extracts request parameters, calls the LLM provider
        (with failover), and publishes the streaming response.
        """
        session_id = data.get("session_id", "")
        messages_json = data.get("messages", "[]")
        provider_name = data.get("provider", settings.LLM_WORKER["DEFAULT_PROVIDER"])
        model = data.get("model", settings.LLM_WORKER["DEFAULT_MODEL"])
        correlation_id = data.get("correlation_id", "")

        start_time = time.time()

        try:
            messages = (
                json.loads(messages_json)
                if isinstance(messages_json, str)
                else messages_json
            )

            full_response = ""
            async for token in self._generate_with_failover(
                messages=messages,
                preferred_provider=provider_name,
                model=model,
            ):
                full_response += token
                self._tokens_generated += 1
                await self._publish_token(session_id, token, correlation_id)

            await self._publish_completion(session_id, full_response, correlation_id)

            await self._redis.client.xack(
                settings.LLM_WORKER["STREAM_REQUESTS"],
                settings.LLM_WORKER["GROUP_WORKERS"],
                message_id,
            )

            self._requests_total += 1
            duration = time.time() - start_time
            logger.info(
                "LLM request completed",
                extra={
                    "session_id": session_id,
                    "response_length": len(full_response),
                    "duration_ms": int(duration * 1000),
                },
            )

        except Exception as exc:
            self._requests_failed += 1
            logger.error(
                "LLM request failed",
                extra={"session_id": session_id, "error": str(exc)},
                exc_info=True,
            )
            await self._publish_error(session_id, str(exc), correlation_id)
            await self._redis.client.xack(
                settings.LLM_WORKER["STREAM_REQUESTS"],
                settings.LLM_WORKER["GROUP_WORKERS"],
                message_id,
            )

    async def _generate_with_failover(
        self,
        messages: list[dict[str, str]],
        preferred_provider: str,
        model: str,
    ) -> AsyncGenerator[str, None]:
        """
        Attempts to generate an LLM response, with failover to alternative
        providers if the preferred one fails or its circuit breaker is open.
        """
        providers_to_try = [preferred_provider] + [
            name for name in self._provider_priority if name != preferred_provider
        ]

        last_error: Optional[Exception] = None
        for provider_name in providers_to_try:
            provider = self._providers.get(provider_name)
            circuit = self._circuit_breakers.get(provider_name)
            if not provider or not circuit:
                continue
            if not circuit.can_execute():
                continue

            try:
                async for token in provider.generate_stream(
                    messages=messages,
                    model=model,
                    max_tokens=settings.LLM_WORKER["MAX_TOKENS"],
                    temperature=settings.LLM_WORKER["TEMPERATURE"],
                ):
                    yield token

                circuit.record_success()
                return

            except Exception as exc:
                circuit.record_failure()
                last_error = exc
                logger.warning(
                    "Provider failed",
                    extra={"provider": provider_name, "error": str(exc)},
                )
                continue

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

    async def _publish_token(
        self, session_id: str, token: str, correlation_id: str
    ) -> None:
        """Publishes a single LLM response token to the appropriate Redis channel."""
        channel = f"{settings.LLM_WORKER['RESPONSE_CHANNEL']}:{session_id}"
        message = json.dumps(
            {
                "type": "llm.token",
                "session_id": session_id,
                "token": token,
                "correlation_id": correlation_id,
                "timestamp": time.time(),
            }
        )
        await self._redis.publish(channel, message)

    async def _publish_completion(
        self,
        session_id: str,
        text: str,
        correlation_id: str,
    ) -> None:
        """Publishes the final completed LLM response to the appropriate Redis channel."""
        channel = f"{settings.LLM_WORKER['RESPONSE_CHANNEL']}:{session_id}"
        message = json.dumps(
            {
                "type": "llm.completed",
                "session_id": session_id,
                "text": text,
                "correlation_id": correlation_id,
                "timestamp": time.time(),
            }
        )
        await self._redis.publish(channel, message)

    async def _publish_error(
        self, session_id: str, error: str, correlation_id: str
    ) -> None:
        """Publishes an error message to the appropriate Redis channel if an LLM request fails."""
        channel = f"{settings.LLM_WORKER['RESPONSE_CHANNEL']}:{session_id}"
        message = json.dumps(
            {
                "type": "llm.failed",
                "session_id": session_id,
                "error": error,
                "correlation_id": correlation_id,
                "timestamp": time.time(),
            }
        )
        await self._redis.publish(channel, message)


class Command(BaseCommand):
    """
    Django management command to run the Large Language Model (LLM) worker.

    This worker listens to LLM requests from a Redis stream, routes them to
    various LLM providers (e.g., OpenAI, Groq, Ollama) with failover
    capabilities, and publishes streaming responses back to a Redis channel.
    """

    help = "Run the realtime LLM worker"

    def handle(self, *args, **options) -> None:
        """
        Starts the asynchronous LLM worker.

        This method sets up basic logging, initializes the `LLMWorker`,
        and manages its lifecycle, including graceful shutdown on signals.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        async def _run() -> None:
            """
            Asynchronous main loop for the LLM worker.

            Initializes and starts the `LLMWorker`, sets up signal handlers
            for graceful shutdown, and runs the worker's message processing loop.
            """
            worker = LLMWorker()

            loop = asyncio.get_running_loop()

            def _shutdown() -> None:
                """
                Initiates a graceful shutdown of the LLM worker.

                This function is registered as a signal handler and schedules
                the worker's `stop` method to be run asynchronously.
                """
                asyncio.create_task(worker.stop())

            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, _shutdown)

            await worker.start()
            try:
                await worker.run()
            finally:
                await worker.stop()

        asyncio.run(_run())
