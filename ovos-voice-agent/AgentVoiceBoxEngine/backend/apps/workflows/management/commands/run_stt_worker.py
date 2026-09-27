"""
Run the STT worker for realtime voice sessions.

Consumes Redis stream STT_WORKER.STREAM_AUDIO, runs faster-whisper transcription,
and publishes results to the session channel group (type: transcription_result)
and Redis pub/sub STT_WORKER.TRANSCRIPTION_CHANNEL:{session_id}.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import signal
import struct
import time
import uuid
from typing import Any, Optional

import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.workflows.redis_client import RedisClient

logger = logging.getLogger(__name__)


def pcm16_bytes_to_float32(audio_bytes: bytes) -> np.ndarray:
    """Decode little-endian PCM16 mono bytes to float32 in [-1, 1]."""
    if not audio_bytes:
        raise ValueError("empty audio payload")
    if len(audio_bytes) % 2 != 0:
        audio_bytes = audio_bytes[:-1]
    samples = np.frombuffer(audio_bytes, dtype="<i2")
    return samples.astype(np.float32) / 32768.0


def _resample_linear(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Linear-interpolation resampler for mono float32 waveforms."""
    if src_rate == dst_rate or audio.size == 0:
        return audio
    duration = audio.shape[0] / float(src_rate)
    dst_length = max(1, int(round(duration * dst_rate)))
    x_old = np.linspace(0.0, 1.0, num=audio.shape[0], endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=dst_length, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def decode_audio_payload(payload: str, audio_format: str) -> tuple[np.ndarray, int]:
    """
    Decode a base64 audio payload into a float32 waveform and sample rate.

    Supported formats:
    - pcm16: raw little-endian mono PCM16 (sample rate from STT_WORKER.SAMPLE_RATE)
    - wav: RIFF/WAVE container
    """
    raw = base64.b64decode(payload)
    fmt = (audio_format or "pcm16").lower()
    sample_rate = int(settings.STT_WORKER.get("SAMPLE_RATE", 16000))

    if fmt in {"pcm16", "raw", "s16le"}:
        return pcm16_bytes_to_float32(raw), sample_rate

    if fmt in {"wav", "wave"}:
        if len(raw) < 44 or raw[0:4] != b"RIFF" or raw[8:12] != b"WAVE":
            raise ValueError("invalid WAV payload")
        # Minimal RIFF parse: find fmt and data chunks
        offset = 12
        channels = 1
        rate = sample_rate
        bits = 16
        data = b""
        while offset + 8 <= len(raw):
            chunk_id = raw[offset : offset + 4]
            chunk_size = struct.unpack_from("<I", raw, offset + 4)[0]
            body = raw[offset + 8 : offset + 8 + chunk_size]
            if chunk_id == b"fmt ":
                if len(body) < 16:
                    raise ValueError("invalid WAV fmt chunk")
                audio_format_code, channels, rate, _byte_rate, _block_align, bits = struct.unpack_from(
                    "<HHIIHH", body, 0
                )
                if audio_format_code not in (1, 0xFFFE):
                    raise ValueError(f"unsupported WAV format code {audio_format_code}")
            elif chunk_id == b"data":
                data = body
            offset += 8 + chunk_size + (chunk_size % 2)
        if not data:
            raise ValueError("WAV missing data chunk")
        if bits != 16:
            raise ValueError(f"unsupported WAV bit depth {bits}")
        if channels not in (1, 2):
            raise ValueError(f"unsupported WAV channels {channels}")
        samples = np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768.0
        if channels == 2:
            samples = samples.reshape(-1, 2).mean(axis=1)
        return samples, int(rate)

    raise ValueError(f"unsupported audio_format: {audio_format}")


class FasterWhisperTranscriber:
    """Lazy-loaded faster-whisper model wrapper."""

    def __init__(self) -> None:
        self._model = None
        self._model_name: str = ""

    def load(self, model_name: str, device: str, compute_type: str) -> None:
        from faster_whisper import WhisperModel

        if self._model is not None and self._model_name == model_name:
            return
        logger.info(
            "Loading faster-whisper model",
            extra={"model": model_name, "device": device, "compute_type": compute_type},
        )
        self._model = WhisperModel(
            model_name,
            device=device if device != "auto" else "auto",
            compute_type=compute_type,
        )
        self._model_name = model_name

    def transcribe(
        self,
        waveform: np.ndarray,
        sample_rate: int,
        language: Optional[str],
    ) -> tuple[str, str, float]:
        if self._model is None:
            raise RuntimeError("STT model not loaded")
        # faster-whisper expects 16 kHz mono float32 when given a waveform array.
        # There is no sampling_rate= argument on WhisperModel.transcribe().
        audio = np.asarray(waveform, dtype=np.float32)
        if sample_rate and int(sample_rate) != 16000:
            audio = _resample_linear(audio, int(sample_rate), 16000)
        segments, info = self._model.transcribe(
            audio,
            language=language or None,
            beam_size=5,
            vad_filter=True,
        )
        parts: list[str] = []
        for segment in segments:
            text = (segment.text or "").strip()
            if text:
                parts.append(text)
        text = " ".join(parts).strip()
        detected = getattr(info, "language", None) or language or ""
        duration = float(getattr(info, "duration", 0.0) or 0.0)
        return text, str(detected), duration


class STTWorker:
    """Processes speech audio from Redis and emits transcription events."""

    def __init__(self) -> None:
        self._worker_id = f"stt-{uuid.uuid4().hex[:12]}"
        self._redis = RedisClient()
        self._running = False
        self._tasks: set[asyncio.Task] = set()
        self._transcriber = FasterWhisperTranscriber()
        self._requests_total = 0
        self._requests_failed = 0

    async def start(self) -> None:
        logger.info("Starting STT worker", extra={"worker_id": self._worker_id})
        await self._redis.connect()
        self._transcriber.load(
            settings.STT_WORKER["MODEL"],
            settings.STT_WORKER.get("DEVICE", "auto"),
            settings.STT_WORKER.get("COMPUTE_TYPE", "int8"),
        )
        await self._ensure_consumer_group()
        self._running = True

    async def stop(self) -> None:
        logger.info("Stopping STT worker", extra={"worker_id": self._worker_id})
        self._running = False
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        await self._redis.disconnect()
        logger.info(
            "STT worker stopped",
            extra={
                "worker_id": self._worker_id,
                "requests_total": self._requests_total,
                "requests_failed": self._requests_failed,
            },
        )

    async def _ensure_consumer_group(self) -> None:
        client = self._redis.client
        stream = settings.STT_WORKER["STREAM_AUDIO"]
        group = settings.STT_WORKER["GROUP_WORKERS"]
        try:
            await client.xgroup_create(stream, group, id="0", mkstream=True)
            logger.info("Created STT consumer group", extra={"group": group})
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                logger.warning(
                    "Failed to create STT consumer group", extra={"error": str(exc)}
                )

    async def run(self) -> None:
        client = self._redis.client
        stream = settings.STT_WORKER["STREAM_AUDIO"]
        group = settings.STT_WORKER["GROUP_WORKERS"]

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
                    "STT worker loop error", extra={"error": str(exc)}, exc_info=True
                )
                await asyncio.sleep(1)

    async def _process_message(self, message_id: str, data: dict[str, Any]) -> None:
        stream = settings.STT_WORKER["STREAM_AUDIO"]
        group = settings.STT_WORKER["GROUP_WORKERS"]
        session_id = str(data.get("session_id") or "")
        correlation_id = str(data.get("correlation_id") or uuid.uuid4().hex)
        audio_b64 = str(data.get("audio") or "")
        audio_format = str(data.get("audio_format") or "pcm16")
        language = data.get("language") or None
        if isinstance(language, str) and not language.strip():
            language = None

        start = time.time()
        try:
            if not session_id:
                raise ValueError("session_id is required")
            if not audio_b64:
                raise ValueError("audio payload is required")

            waveform, sample_rate = decode_audio_payload(audio_b64, audio_format)
            if waveform.size == 0:
                raise ValueError("decoded audio is empty")

            text, detected_lang, duration = await asyncio.to_thread(
                self._transcriber.transcribe,
                waveform,
                sample_rate,
                language,
            )

            payload = {
                "type": "stt.completed",
                "session_id": session_id,
                "correlation_id": correlation_id,
                "text": text,
                "language": detected_lang,
                "duration_seconds": duration,
                "timestamp": time.time(),
            }
            await self._emit(session_id, payload)
            self._requests_total += 1
            logger.info(
                "STT request completed",
                extra={
                    "session_id": session_id,
                    "chars": len(text),
                    "duration_ms": int((time.time() - start) * 1000),
                },
            )
        except Exception as exc:
            self._requests_failed += 1
            logger.error(
                "STT request failed",
                extra={"session_id": session_id, "error": str(exc)},
                exc_info=True,
            )
            if session_id:
                await self._emit(
                    session_id,
                    {
                        "type": "stt.failed",
                        "session_id": session_id,
                        "correlation_id": correlation_id,
                        "error": str(exc),
                        "timestamp": time.time(),
                    },
                )
        finally:
            await self._redis.client.xack(stream, group, message_id)

    async def _emit(self, session_id: str, payload: dict[str, Any]) -> None:
        """Deliver to WebSocket session group and Redis pub/sub."""
        try:
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if channel_layer is not None:
                event_type = (
                    "transcription_result"
                    if payload.get("type") == "stt.completed"
                    else "session_event"
                )
                await channel_layer.group_send(
                    f"session_{session_id}",
                    {"type": event_type, "data": payload},
                )
        except Exception as exc:
            logger.error(
                "STT channel_layer emit failed",
                extra={"session_id": session_id, "error": str(exc)},
            )

        channel = f"{settings.STT_WORKER['TRANSCRIPTION_CHANNEL']}:{session_id}"
        await self._redis.publish(channel, json.dumps(payload))


class Command(BaseCommand):
    """Django management command: run the realtime STT worker."""

    help = "Run the realtime STT worker (faster-whisper)"

    def handle(self, *args, **options) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        async def _run() -> None:
            worker = STTWorker()
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
