"""
Run the TTS worker for realtime sessions.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import signal
import time
import uuid
from typing import Any, Optional

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.workflows.redis_client import RedisClient

logger = logging.getLogger(__name__)

try:
    import kokoro_onnx as kokoro
except ImportError as exc:  # pragma: no cover
    raise ImportError("kokoro-onnx is required for TTS worker") from exc

try:
    import numpy as np
    import soundfile as sf
except ImportError as exc:  # pragma: no cover
    raise ImportError("numpy and soundfile are required for TTS worker") from exc


class TTSWorker:
    """Text-to-Speech worker using Kokoro ONNX."""

    def __init__(self) -> None:
        """Initializes the TTS worker with Redis client, TTS engine, and internal state."""
        self._redis = RedisClient()
        self._engine: Optional[Any] = None
        self._running = False
        self._tasks: set[asyncio.Task] = set()
        self._cancelled_sessions: set[str] = set()
        self._cancel_listener_task: Optional[asyncio.Task] = None
        self._worker_id = f"tts-{uuid.uuid4().hex[:8]}"

        self._synthesis_total = 0
        self._synthesis_failed = 0
        self._total_audio_seconds = 0.0
        self._total_characters = 0

    async def start(self) -> None:
        """
        Starts the TTS worker, establishing Redis connection, loading the TTS model,
        and ensuring the consumer group exists.
        """
        await self._redis.connect()
        self._load_model()
        await self._ensure_consumer_group()
        self._cancel_listener_task = asyncio.create_task(self._listen_for_cancels())
        self._running = True
        logger.info("TTS worker started", extra={"worker_id": self._worker_id})

    async def stop(self) -> None:
        """
        Stops the TTS worker, gracefully shutting down all active tasks,
        and closing the Redis connection.
        """
        self._running = False
        if self._cancel_listener_task:
            self._cancel_listener_task.cancel()
            try:
                await self._cancel_listener_task
            except asyncio.CancelledError:
                pass

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        await self._redis.disconnect()
        logger.info(
            "TTS worker stopped",
            extra={
                "worker_id": self._worker_id,
                "synthesis_total": self._synthesis_total,
                "synthesis_failed": self._synthesis_failed,
                "total_audio_seconds": self._total_audio_seconds,
                "total_characters": self._total_characters,
            },
        )

    def _load_model(self) -> None:
        """Loads the Kokoro TTS model from the specified model directory."""
        model_dir = settings.TTS_WORKER["MODEL_DIR"]
        model_file = settings.TTS_WORKER["MODEL_FILE"]
        voices_file = settings.TTS_WORKER["VOICES_FILE"]

        model_path = os.path.join(model_dir, model_file)
        voices_path = os.path.join(model_dir, voices_file)

        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Kokoro model file not found: {model_path}")
        if not os.path.isfile(voices_path):
            raise FileNotFoundError(f"Kokoro voices file not found: {voices_path}")

        self._engine = kokoro.Kokoro(model_path=model_path, voices_path=voices_path)
        logger.info("Kokoro model loaded", extra={"model_path": model_path})

    async def _ensure_consumer_group(self) -> None:
        """
        Ensures the Redis consumer group for TTS requests exists.
        Creates it if it does not already exist.
        """
        client = self._redis.client
        stream = settings.TTS_WORKER["STREAM_REQUESTS"]
        group = settings.TTS_WORKER["GROUP_WORKERS"]

        try:
            await client.xgroup_create(stream, group, id="0", mkstream=True)
            logger.info("Created consumer group", extra={"group": group})
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                logger.warning("Failed to create consumer group", extra={"error": str(exc)})

    async def _listen_for_cancels(self) -> None:
        """
        Listens for TTS cancellation messages on a Redis pub/sub channel.

        If a cancellation message is received for a session, the session ID is
        added to a set of cancelled sessions to stop ongoing synthesis.
        """
        pubsub = self._redis.client.pubsub()
        await pubsub.psubscribe(f"{settings.TTS_WORKER['CHANNEL_TTS']}:*")

        async for message in pubsub.listen():
            if not self._running:
                break
            if message["type"] == "pmessage":
                try:
                    data = json.loads(message["data"])
                    if data.get("type") == "tts.cancel":
                        session_id = data.get("session_id")
                        if session_id:
                            self._cancelled_sessions.add(session_id)
                except (json.JSONDecodeError, KeyError):
                    continue

    async def run(self) -> None:
        """
        Main loop of the TTS worker, continuously reading and processing
        TTS requests from the Redis stream.
        """
        client = self._redis.client
        stream = settings.TTS_WORKER["STREAM_REQUESTS"]
        group = settings.TTS_WORKER["GROUP_WORKERS"]

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
                        task = asyncio.create_task(self._process_message(message_id, data))
                        self._tasks.add(task)
                        task.add_done_callback(self._tasks.discard)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Worker loop error", extra={"error": str(exc)}, exc_info=True)
                await asyncio.sleep(1)

    async def _process_message(self, message_id: str, data: dict[str, Any]) -> None:
        """
        Processes a single TTS request message from the Redis stream.

        This method extracts request parameters, synthesizes speech,
        and publishes the audio chunks.
        """
        session_id = data.get("session_id", "")
        text = data.get("text", "")
        voice = data.get("voice", settings.TTS_WORKER["DEFAULT_VOICE"])
        speed = float(data.get("speed", settings.TTS_WORKER["DEFAULT_SPEED"]))
        response_id = data.get("response_id", "")
        correlation_id = data.get("correlation_id", "")

        start_time = time.time()
        self._cancelled_sessions.discard(session_id)

        try:
            if not text:
                raise ValueError("No text in message")

            self._total_characters += len(text)
            sequence = 0
            async for chunk_b64, sample_rate, is_final in self._synthesize_stream(
                text=text,
                voice=voice,
                speed=speed,
                session_id=session_id,
            ):
                if session_id in self._cancelled_sessions:
                    await self._publish_cancelled(session_id, response_id)
                    break

                await self._publish_audio_chunk(
                    session_id=session_id,
                    chunk_b64=chunk_b64,
                    sequence=sequence,
                    sample_rate=sample_rate,
                    is_final=is_final,
                )
                sequence += 1

            await self._redis.client.xack(
                settings.TTS_WORKER["STREAM_REQUESTS"],
                settings.TTS_WORKER["GROUP_WORKERS"],
                message_id,
            )

            self._synthesis_total += 1
            duration = time.time() - start_time
            logger.info(
                "Synthesis completed",
                extra={
                    "session_id": session_id,
                    "text_length": len(text),
                    "chunks": sequence,
                    "duration_ms": int(duration * 1000),
                },
            )

        except Exception as exc:
            self._synthesis_failed += 1
            logger.error(
                "Synthesis failed",
                extra={"session_id": session_id, "error": str(exc)},
                exc_info=True,
            )
            await self._publish_error(session_id, str(exc), response_id, correlation_id)
            await self._redis.client.xack(
                settings.TTS_WORKER["STREAM_REQUESTS"],
                settings.TTS_WORKER["GROUP_WORKERS"],
                message_id,
            )

    async def _synthesize_stream(
        self,
        text: str,
        voice: str,
        speed: float,
        session_id: str,
    ):
        """
        Synthesizes speech from text into a stream of audio chunks.

        Args:
            text: The text to synthesize.
            voice: The voice ID to use for synthesis.
            speed: The speech speed multiplier.
            session_id: The ID of the current session, used for cancellation checks.

        Yields:
            tuple[str, int, bool]: A tuple containing base64 encoded audio chunk,
                                   sample rate, and a boolean indicating if it's the final chunk.
        """
        if not self._engine:
            raise RuntimeError("Kokoro engine not initialized")

        try:
            available_voices = self._engine.get_voices()
            if voice not in available_voices:
                raise ValueError("Requested voice not available")
        except Exception as exc:
            raise RuntimeError("Failed to validate voice") from exc

        chunk_count = 0
        async for audio_arr, sample_rate in self._engine.create_stream(
            text=text,
            voice=voice,
            speed=speed,
        ):
            if session_id in self._cancelled_sessions:
                break

            self._total_audio_seconds += len(audio_arr) / sample_rate
            buf = io.BytesIO()
            sf.write(buf, audio_arr, sample_rate, format="WAV")
            chunk_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            chunk_count += 1
            yield chunk_b64, sample_rate, False

        if chunk_count > 0:
            buf = io.BytesIO()
            sf.write(buf, np.zeros(1, dtype=np.float32), sample_rate, format="WAV")
            yield base64.b64encode(buf.getvalue()).decode("utf-8"), sample_rate, True

    async def _publish_audio_chunk(
        self,
        session_id: str,
        chunk_b64: str,
        sequence: int,
        sample_rate: int,
        is_final: bool,
    ) -> None:
        """Publishes a synthesized audio chunk to the appropriate Redis stream."""
        stream_name = f"{settings.TTS_WORKER['CHANNEL_AUDIO_OUT']}:{session_id}"
        await self._redis.client.xadd(
            stream_name,
            {
                "chunk": chunk_b64,
                "sequence": str(sequence),
                "sample_rate": str(sample_rate),
                "is_final": "1" if is_final else "0",
                "timestamp": str(time.time()),
            },
            maxlen=1000,
        )

    async def _publish_cancelled(self, session_id: str, response_id: str) -> None:
        """Publishes a cancellation message to the appropriate Redis channel."""
        channel = f"{settings.TTS_WORKER['CHANNEL_TTS']}:{session_id}"
        message = json.dumps(
            {
                "type": "tts.cancelled",
                "session_id": session_id,
                "response_id": response_id,
                "timestamp": time.time(),
            }
        )
        await self._redis.publish(channel, message)

    async def _publish_error(
        self,
        session_id: str,
        error: str,
        response_id: str,
        correlation_id: str,
    ) -> None:
        """Publishes an error message to the appropriate Redis channel if TTS synthesis fails."""
        channel = f"{settings.TTS_WORKER['CHANNEL_TTS']}:{session_id}"
        message = json.dumps(
            {
                "type": "tts.failed",
                "session_id": session_id,
                "response_id": response_id,
                "correlation_id": correlation_id,
                "error": error,
                "timestamp": time.time(),
            }
        )
        await self._redis.publish(channel, message)


class Command(BaseCommand):
    """
    Django management command to run the Text-to-Speech (TTS) worker.

    This worker listens to TTS requests from a Redis stream, synthesizes speech
    using the Kokoro ONNX engine, and publishes the audio chunks back to a
    Redis stream for real-time delivery to clients.
    """

    help = "Run the realtime TTS worker"

    def handle(self, *args, **options) -> None:
        """
        Starts the asynchronous TTS worker.

        This method sets up basic logging, initializes the `TTSWorker`,
        and manages its lifecycle, including graceful shutdown on signals.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        async def _run() -> None:
            """
            Asynchronous main loop for the TTS worker.

            Initializes and starts the `TTSWorker`, sets up signal handlers
            for graceful shutdown, and runs the worker's message processing loop.
            """
            worker = TTSWorker()
            loop = asyncio.get_running_loop()

            def _shutdown() -> None:
                """
                Initiates a graceful shutdown of the TTS worker.

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
