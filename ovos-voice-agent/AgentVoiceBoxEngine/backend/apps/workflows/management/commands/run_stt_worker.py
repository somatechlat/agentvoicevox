"""
Run the STT worker for realtime sessions.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import signal
import time
import uuid
from typing import Any, Optional

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.workflows.redis_client import RedisClient

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
except ImportError as exc:  # pragma: no cover
    raise ImportError("faster-whisper is required for STT worker") from exc

try:
    import numpy as np
    import soundfile as sf
except ImportError as exc:  # pragma: no cover
    raise ImportError("numpy and soundfile are required for STT worker") from exc


class STTWorker:
    """Speech-to-Text worker using Faster-Whisper."""

    def __init__(self) -> None:
        """Initializes the STT worker with Redis client, Whisper model, and VAD."""
        self._redis = RedisClient()
        self._model: Optional[WhisperModel] = None
        self._vad_model: Any = None
        self._running = False
        self._tasks: set[asyncio.Task] = set()
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._worker_id = f"stt-{uuid.uuid4().hex[:8]}"

        # Session buffers for VAD and accumulation
        self._buffers: dict[str, list[bytes]] = {}
        self._speech_states: dict[str, bool] = {}

        self._transcriptions_total = 0
        self._transcriptions_failed = 0
        self._total_audio_seconds = 0.0

    async def start(self) -> None:
        """Starts the STT worker, loading Whisper and VAD models."""
        await self._redis.connect()
        self._semaphore = asyncio.Semaphore(settings.STT_WORKER["BATCH_SIZE"])
        self._load_model()
        self._load_vad()
        await self._ensure_consumer_group()
        self._running = True
        logger.info("STT worker started", extra={"worker_id": self._worker_id})

    def _load_vad(self) -> None:
        """Loads Silero VAD model."""
        import torch
        self._vad_model, _ = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=True
        )
        logger.info("Silero VAD model loaded")

    def _load_model(self) -> None:
        """Loads the Faster-Whisper model into memory."""
        device = settings.STT_WORKER["DEVICE"]
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        compute_type = settings.STT_WORKER["COMPUTE_TYPE"]
        if device == "cpu" and compute_type == "float16":
            compute_type = "int8"

        self._model = WhisperModel(
            settings.STT_WORKER["MODEL"],
            device=device,
            compute_type=compute_type,
        )
        logger.info(
            "Whisper model loaded",
            extra={"model": settings.STT_WORKER["MODEL"], "device": device},
        )

    async def _process_message(self, message_id: str, data: dict[str, Any]) -> None:
        """
        Processes a single audio chunk message using VAD and buffering.
        """
        if not self._semaphore:
            return

        async with self._semaphore:
            session_id = data.get("session_id", "")
            correlation_id = data.get("correlation_id", "")

            try:
                audio_b64 = data.get("audio", "")
                if not audio_b64:
                    raise ValueError("No audio data in message")

                audio_bytes = base64.b64decode(audio_b64)

                # Run VAD on this chunk
                is_speech = await self._run_vad(audio_bytes)

                # Update session state and emit events
                was_speech = self._speech_states.get(session_id, False)
                if is_speech and not was_speech:
                    self._speech_states[session_id] = True
                    await self._publish_event(session_id, "input_audio_buffer.speech_started")
                elif not is_speech and was_speech:
                    # Silence detected after speech - trigger transcription
                    self._speech_states[session_id] = False
                    await self._publish_event(session_id, "input_audio_buffer.speech_stopped")

                    # Accumulate and transcribe
                    full_audio = b"".join(self._buffers.get(session_id, []))
                    if full_audio:
                        text, language, confidence = await self._transcribe(
                            full_audio,
                            language_hint=data.get("language") or None,
                        )
                        await self._publish_result(
                            session_id=session_id,
                            text=text,
                            language=language,
                            confidence=confidence,
                            correlation_id=correlation_id,
                        )
                        # Clear buffer after transcription
                        self._buffers[session_id] = []

                # Accumulate buffer
                if session_id not in self._buffers:
                    self._buffers[session_id] = []
                self._buffers[session_id].append(audio_bytes)

                await self._redis.client.xack(
                    settings.STT_WORKER["STREAM_AUDIO"],
                    settings.STT_WORKER["GROUP_WORKERS"],
                    message_id,
                )

            except Exception as exc:
                self._transcriptions_failed += 1
                logger.error(
                    "Error processing audio chunk",
                    extra={"session_id": session_id, "error": str(exc)},
                    exc_info=True,
                )
                await self._redis.client.xack(
                    settings.STT_WORKER["STREAM_AUDIO"],
                    settings.STT_WORKER["GROUP_WORKERS"],
                    message_id,
                )

    async def _run_vad(self, audio_bytes: bytes) -> bool:
        """Run Silero VAD on audio chunk."""
        # Simplified VAD check - in production you'd want proper windowing
        import numpy as np
        import torch

        # Convert bytes to tensor
        audio_io = io.BytesIO(audio_bytes)
        audio_data, _ = sf.read(audio_io)
        if len(audio_data) == 0:
            return False

        tensor = torch.from_numpy(audio_data.astype(np.float32))
        if self._vad_model:
            # Silero VAD returns probability
            speech_prob = self._vad_model(tensor, 16000).item()
            return speech_prob > 0.5
        return False

    async def _publish_event(self, session_id: str, event_type: str) -> None:
        """Publishes a lifecycle event to the session channel."""
        channel = f"{settings.STT_WORKER['CHANNEL_TRANSCRIPTION']}:{session_id}"
        message = json.dumps({
            "type": event_type,
            "session_id": session_id,
            "timestamp": time.time()
        })
        await self._redis.publish(channel, message)

    async def _ensure_consumer_group(self) -> None:
        """
        Ensures the Redis consumer group for STT audio streams exists.
        Creates the group if it does not already exist.
        """
        client = self._redis.client
        stream = settings.STT_WORKER["STREAM_AUDIO"]
        group = settings.STT_WORKER["GROUP_WORKERS"]

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
        Main loop of the STT worker, continuously reading and processing
        audio chunks from the Redis stream.
        """
        client = self._redis.client
        stream = settings.STT_WORKER["STREAM_AUDIO"]
        group = settings.STT_WORKER["GROUP_WORKERS"]

        while self._running:
            try:
                messages = await client.xreadgroup(
                    group,
                    self._worker_id,
                    {stream: ">"},
                    count=settings.STT_WORKER["BATCH_SIZE"],
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

    async def stop(self) -> None:
        """
        Stops the STT worker, gracefully shutting down all active tasks
        and closing the Redis connection.
        """
        self._running = False
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        await self._redis.disconnect()
        logger.info(
            "STT worker stopped",
            extra={
                "worker_id": self._worker_id,
                "transcriptions_total": self._transcriptions_total,
                "transcriptions_failed": self._transcriptions_failed,
                "total_audio_seconds": self._total_audio_seconds,
            },
        )

    async def _transcribe(
        self,
        audio_bytes: bytes,
        language_hint: Optional[str] = None,
    ) -> tuple[str, str, float]:
        """
        Transcribes the given audio bytes using the loaded Whisper model.

        Args:
            audio_bytes: Raw audio data in bytes.
            language_hint: Optional language hint for transcription.

        Returns:
            tuple[str, str, float]: A tuple containing the transcribed text,
                                   detected language, and transcription confidence.

        Raises:
            RuntimeError: If the STT model is not initialized.
        """
        if not self._model:
            raise RuntimeError("STT model not initialized")

        audio_io = io.BytesIO(audio_bytes)
        audio_data, sample_rate = sf.read(audio_io)
        target_rate = settings.STT_WORKER["SAMPLE_RATE"]
        if sample_rate != target_rate:
            ratio = target_rate / sample_rate
            new_length = int(len(audio_data) * ratio)
            audio_data = np.interp(
                np.linspace(0, len(audio_data), new_length),
                np.arange(len(audio_data)),
                audio_data,
            )
            sample_rate = target_rate

        self._total_audio_seconds += len(audio_data) / sample_rate

        loop = asyncio.get_event_loop()
        segments, info = await loop.run_in_executor(
            None,
            lambda: self._model.transcribe(
                audio_data,
                language=language_hint,
                beam_size=5,
                vad_filter=True,
            ),
        )

        text_parts = []
        total_confidence = 0.0
        segment_count = 0
        for segment in segments:
            text_parts.append(segment.text)
            total_confidence += segment.avg_logprob
            segment_count += 1

        text = " ".join(text_parts).strip()
        language = info.language or "en"
        confidence = (total_confidence / segment_count) if segment_count > 0 else 0.0
        confidence = min(1.0, max(0.0, 1.0 + confidence))

        return text, language, confidence

    async def _publish_result(
        self,
        session_id: str,
        text: str,
        language: str,
        confidence: float,
        correlation_id: str,
    ) -> None:
        """Publishes the transcription result to the session group via Channels layer."""
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        await channel_layer.group_send(
            f"session_{session_id}",
            {
                "type": "transcription_result",
                "data": {
                    "text": text,
                    "language": language,
                    "confidence": confidence,
                    "correlation_id": correlation_id,
                }
            }
        )

    async def _publish_error(
        self, session_id: str, error: str, correlation_id: str
    ) -> None:
        """Publishes an error message to the session group via Channels layer."""
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        await channel_layer.group_send(
            f"session_{session_id}",
            {
                "type": "transcription_error",
                "data": {
                    "error": error,
                    "correlation_id": correlation_id,
                }
            }
        )

    async def _publish_event(self, session_id: str, event_type: str) -> None:
        """Publishes a lifecycle event to the session group via Channels layer."""
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()

        await channel_layer.group_send(
            f"session_{session_id}",
            {
                "type": "session_event",
                "data": {
                    "type": event_type,
                    "session_id": session_id,
                }
            }
        )


class Command(BaseCommand):
    """
    Django management command to run the Speech-to-Text (STT) worker.

    This worker listens to an audio stream, transcribes audio chunks using
    Faster-Whisper, and publishes the transcription results.
    """

    help = "Run the realtime STT worker"

    def handle(self, *args, **options) -> None:
        """
        Starts the asynchronous STT worker.

        This method sets up basic logging, initializes the `STTWorker`,
        and manages its lifecycle, including graceful shutdown on signals.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        async def _run() -> None:
            """
            Asynchronous main loop for the STT worker.

            Initializes and starts the `STTWorker`, sets up signal handlers
            for graceful shutdown, and runs the worker's message processing loop.
            """
            worker = STTWorker()
            loop = asyncio.get_running_loop()

            def _shutdown() -> None:
                """
                Initiates a graceful shutdown of the STT worker.

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
