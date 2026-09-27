"""
Run the TTS worker for realtime voice sessions.

Consumes Redis stream TTS_WORKER.STREAM_REQUESTS, synthesizes speech with
Kokoro ONNX, and streams PCM16 audio chunks to the session channel group
(type: response_chunk) plus Redis pub/sub TTS_WORKER.AUDIO_OUT_CHANNEL:{session_id}.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import signal
import time
import uuid
from typing import Any, Optional

import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.workflows.redis_client import RedisClient

logger = logging.getLogger(__name__)


def float32_to_pcm16_bytes(samples: np.ndarray) -> bytes:
    """Convert float32 waveform in [-1, 1] to little-endian PCM16 bytes."""
    clipped = np.clip(samples.astype(np.float32), -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    return pcm.tobytes()


class KokoroTTS:
    """Lazy-loaded Kokoro ONNX synthesizer."""

    def __init__(self) -> None:
        self._kokoro = None
        self._sample_rate = 24000

    def load(self, model_dir: str, model_file: str, voices_file: str) -> None:
        if self._kokoro is not None:
            return
        import os

        from kokoro_onnx import Kokoro

        model_path = (
            model_file
            if os.path.isabs(model_file)
            else os.path.join(model_dir, model_file)
        )
        voices_path = (
            voices_file
            if os.path.isabs(voices_file)
            else os.path.join(model_dir, voices_file)
        )
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"Kokoro model not found: {model_path}")
        if not os.path.isfile(voices_path):
            raise FileNotFoundError(f"Kokoro voices not found: {voices_path}")
        logger.info(
            "Loading Kokoro ONNX",
            extra={"model_path": model_path, "voices_path": voices_path},
        )
        self._kokoro = Kokoro(model_path, voices_path)
        # kokoro-onnx uses 24 kHz output
        self._sample_rate = 24000

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def synthesize(
        self,
        text: str,
        voice: str,
        speed: float,
        lang: str,
    ) -> tuple[np.ndarray, int]:
        if self._kokoro is None:
            raise RuntimeError("TTS model not loaded")
        samples, sample_rate = self._kokoro.create(
            text,
            voice=voice,
            speed=float(speed),
            lang=lang,
        )
        audio = np.asarray(samples, dtype=np.float32)
        rate = int(sample_rate or self._sample_rate)
        return audio, rate


class TTSWorker:
    """Synthesizes speech from Redis jobs and emits audio events."""

    def __init__(self) -> None:
        self._worker_id = f"tts-{uuid.uuid4().hex[:12]}"
        self._redis = RedisClient()
        self._running = False
        self._tasks: set[asyncio.Task] = set()
        self._tts = KokoroTTS()
        self._requests_total = 0
        self._requests_failed = 0

    async def start(self) -> None:
        logger.info("Starting TTS worker", extra={"worker_id": self._worker_id})
        await self._redis.connect()
        self._tts.load(
            settings.TTS_WORKER["MODEL_DIR"],
            settings.TTS_WORKER["MODEL_FILE"],
            settings.TTS_WORKER["VOICES_FILE"],
        )
        await self._ensure_consumer_group()
        self._running = True

    async def stop(self) -> None:
        logger.info("Stopping TTS worker", extra={"worker_id": self._worker_id})
        self._running = False
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        await self._redis.disconnect()
        logger.info(
            "TTS worker stopped",
            extra={
                "worker_id": self._worker_id,
                "requests_total": self._requests_total,
                "requests_failed": self._requests_failed,
            },
        )

    async def _ensure_consumer_group(self) -> None:
        client = self._redis.client
        stream = settings.TTS_WORKER["STREAM_REQUESTS"]
        group = settings.TTS_WORKER["GROUP_WORKERS"]
        try:
            await client.xgroup_create(stream, group, id="0", mkstream=True)
            logger.info("Created TTS consumer group", extra={"group": group})
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                logger.warning(
                    "Failed to create TTS consumer group", extra={"error": str(exc)}
                )

    async def run(self) -> None:
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
                        task = asyncio.create_task(
                            self._process_message(message_id, data)
                        )
                        self._tasks.add(task)
                        task.add_done_callback(self._tasks.discard)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(
                    "TTS worker loop error", extra={"error": str(exc)}, exc_info=True
                )
                await asyncio.sleep(1)

    async def _process_message(self, message_id: str, data: dict[str, Any]) -> None:
        stream = settings.TTS_WORKER["STREAM_REQUESTS"]
        group = settings.TTS_WORKER["GROUP_WORKERS"]
        session_id = str(data.get("session_id") or "")
        response_id = str(data.get("response_id") or f"resp_{uuid.uuid4().hex[:12]}")
        correlation_id = str(data.get("correlation_id") or "")
        text = str(data.get("text") or "").strip()
        voice = str(
            data.get("voice") or settings.TTS_WORKER.get("DEFAULT_VOICE") or "af_heart"
        )
        try:
            speed = float(data.get("speed") or settings.TTS_WORKER.get("DEFAULT_SPEED") or 1.0)
        except (TypeError, ValueError):
            speed = float(settings.TTS_WORKER.get("DEFAULT_SPEED") or 1.0)
        lang = str(data.get("language") or data.get("lang") or "en-us")

        start = time.time()
        try:
            if not session_id:
                raise ValueError("session_id is required")
            if not text:
                raise ValueError("text is required")

            samples, sample_rate = await asyncio.to_thread(
                self._tts.synthesize, text, voice, speed, lang
            )
            if samples.size == 0:
                raise ValueError("TTS produced empty audio")

            pcm = float32_to_pcm16_bytes(samples)
            chunk_samples = int(settings.TTS_WORKER.get("CHUNK_SIZE") or 4800)
            chunk_bytes = max(2, chunk_samples * 2)
            item_id = f"item_{uuid.uuid4().hex[:12]}"
            total_bytes = len(pcm)

            for offset in range(0, total_bytes, chunk_bytes):
                chunk = pcm[offset : offset + chunk_bytes]
                await self._emit_chunk(
                    session_id=session_id,
                    response_id=response_id,
                    item_id=item_id,
                    correlation_id=correlation_id,
                    audio_b64=base64.b64encode(chunk).decode("ascii"),
                    sample_rate=sample_rate,
                    sequence=offset // chunk_bytes,
                )

            await self._emit_done(
                session_id=session_id,
                response_id=response_id,
                correlation_id=correlation_id,
                sample_rate=sample_rate,
                duration_seconds=total_bytes / 2.0 / float(sample_rate),
            )
            self._requests_total += 1
            logger.info(
                "TTS request completed",
                extra={
                    "session_id": session_id,
                    "bytes": total_bytes,
                    "duration_ms": int((time.time() - start) * 1000),
                },
            )
        except Exception as exc:
            self._requests_failed += 1
            logger.error(
                "TTS request failed",
                extra={"session_id": session_id, "error": str(exc)},
                exc_info=True,
            )
            if session_id:
                await self._emit_error(session_id, response_id, correlation_id, str(exc))
        finally:
            await self._redis.client.xack(stream, group, message_id)

    async def _group_send(self, session_id: str, event_type: str, data: dict[str, Any]) -> None:
        try:
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if channel_layer is not None:
                await channel_layer.group_send(
                    f"session_{session_id}",
                    {"type": event_type, "data": data},
                )
        except Exception as exc:
            logger.error(
                "TTS channel_layer emit failed",
                extra={"session_id": session_id, "error": str(exc)},
            )

    async def _emit_chunk(
        self,
        *,
        session_id: str,
        response_id: str,
        item_id: str,
        correlation_id: str,
        audio_b64: str,
        sample_rate: int,
        sequence: int,
    ) -> None:
        payload = {
            "type": "tts.chunk",
            "session_id": session_id,
            "response_id": response_id,
            "item_id": item_id,
            "correlation_id": correlation_id,
            "audio": audio_b64,
            "sample_rate": sample_rate,
            "format": "pcm16",
            "sequence": sequence,
            "timestamp": time.time(),
        }
        await self._group_send(session_id, "response_chunk", payload)
        channel = f"{settings.TTS_WORKER['AUDIO_OUT_CHANNEL']}:{session_id}"
        await self._redis.publish(channel, json.dumps(payload))

    async def _emit_done(
        self,
        *,
        session_id: str,
        response_id: str,
        correlation_id: str,
        sample_rate: int,
        duration_seconds: float,
    ) -> None:
        payload = {
            "type": "tts.completed",
            "session_id": session_id,
            "response_id": response_id,
            "correlation_id": correlation_id,
            "sample_rate": sample_rate,
            "duration_seconds": duration_seconds,
            "timestamp": time.time(),
        }
        await self._group_send(session_id, "response_completed", payload)
        channel = f"{settings.TTS_WORKER['AUDIO_OUT_CHANNEL']}:{session_id}"
        await self._redis.publish(channel, json.dumps(payload))

    async def _emit_error(
        self, session_id: str, response_id: str, correlation_id: str, error: str
    ) -> None:
        payload = {
            "type": "tts.failed",
            "session_id": session_id,
            "response_id": response_id,
            "correlation_id": correlation_id,
            "error": error,
            "timestamp": time.time(),
        }
        await self._group_send(session_id, "session_event", payload)
        channel = f"{settings.TTS_WORKER['AUDIO_OUT_CHANNEL']}:{session_id}"
        await self._redis.publish(channel, json.dumps(payload))


class Command(BaseCommand):
    """Django management command: run the realtime TTS worker."""

    help = "Run the realtime TTS worker (Kokoro ONNX)"

    def handle(self, *args, **options) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        async def _run() -> None:
            worker = TTSWorker()
            loop = asyncio.get_running_loop()

            def _shutdown() -> None:
                asyncio.create_task(worker.stop())

            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, _shutdown)

            await worker.start()
            try:
                await worker.run()
            finally:
                await worker.stop()

        asyncio.run(_run())
