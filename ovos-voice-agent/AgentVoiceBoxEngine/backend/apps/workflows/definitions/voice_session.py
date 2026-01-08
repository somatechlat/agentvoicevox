"""
Voice session workflow for processing voice interactions.

Orchestrates STT -> LLM -> TTS pipeline with durable execution.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)


@dataclass
class VoiceSessionInput:
    """Input for voice session workflow."""

    tenant_id: str
    session_id: str
    project_id: str
    config: dict[str, Any]


@dataclass
class AudioChunk:
    """An audio chunk to process."""

    chunk_id: str
    audio_data: bytes
    audio_format: str
    is_final: bool = False


@dataclass
class VoiceSessionResult:
    """Result of voice session workflow."""

    session_id: str
    status: str
    total_audio_seconds: float
    total_input_tokens: int
    total_output_tokens: int
    turns: int


@workflow.defn(name="VoiceSessionWorkflow")
class VoiceSessionWorkflow:
    """
    Workflow for processing voice session interactions.

    Handles the full STT -> LLM -> TTS pipeline with:
    - Audio transcription via STT
    - Response generation via LLM
    - Speech synthesis via TTS
    - Usage tracking for billing
    """

    def __init__(self):
        """
        Initializes the workflow state for a voice session.

        Sets up variables to track the tenant, session ID, configuration,
        conversation history, usage metrics, and active status.
        """
        self.tenant_id: str = ""
        self.session_id: str = ""
        self.config: dict[str, Any] = {}
        self.conversation: list[dict[str, str]] = []
        self.total_audio_seconds: float = 0.0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.turns: int = 0
        self.is_active: bool = True

    @workflow.run
    async def run(self, input: VoiceSessionInput) -> VoiceSessionResult:
        """
        Run the voice session workflow.

        Args:
            input: VoiceSessionInput with session configuration

        Returns:
            VoiceSessionResult with session metrics
        """
        self.tenant_id = input.tenant_id
        self.session_id = input.session_id
        self.config = input.config

        # Initialize conversation with system prompt
        system_prompt = self.config.get(
            "system_prompt",
            "You are a helpful voice assistant. Keep responses concise and natural.",
        )
        self.conversation = [{"role": "system", "content": system_prompt}]

        workflow.logger.info(
            f"Started voice session workflow for session {self.session_id}"
        )

        # Wait for audio chunks via signals
        while self.is_active:
            await workflow.wait_condition(
                lambda: not self.is_active,
                timeout=timedelta(hours=24),
            )

        return VoiceSessionResult(
            session_id=self.session_id,
            status="completed",
            total_audio_seconds=self.total_audio_seconds,
            total_input_tokens=self.total_input_tokens,
            total_output_tokens=self.total_output_tokens,
            turns=self.turns,
        )

    @workflow.signal(name="audio_chunk")
    async def handle_audio_chunk(self, chunk: AudioChunk) -> None:
        """
        Handle incoming audio chunk signal.

        Args:
            chunk: AudioChunk to process
        """
        from datetime import datetime

        from apps.workflows.activities.billing import BillingActivities, UsageEvent
        from apps.workflows.activities.llm import LLMActivities, LLMRequest, Message
        from apps.workflows.activities.stt import STTActivities, TranscriptionRequest
        from apps.workflows.activities.tts import SynthesisRequest, TTSActivities

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3,
        )

        # 1. Transcribe audio
        transcription = await workflow.execute_activity(
            STTActivities.transcribe_audio,
            TranscriptionRequest(
                tenant_id=self.tenant_id,
                session_id=self.session_id,
                audio_data=chunk.audio_data,
                audio_format=chunk.audio_format,
                language=self.config.get("language"),
                model=self.config.get("stt_model", "tiny"),
            ),
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )

        self.total_audio_seconds += transcription.duration_seconds

        if not transcription.text.strip():
            return  # No speech detected

        # Add user message to conversation
        self.conversation.append(
            {
                "role": "user",
                "content": transcription.text,
            }
        )

        # 2. Generate LLM response
        llm_result = await workflow.execute_activity(
            LLMActivities.generate_response,
            LLMRequest(
                tenant_id=self.tenant_id,
                session_id=self.session_id,
                messages=[
                    Message(role=m["role"], content=m["content"])
                    for m in self.conversation
                ],
                model=self.config.get("llm_model", "llama-3.1-8b-instant"),
                provider=self.config.get("llm_provider", "groq"),
                max_tokens=self.config.get("max_tokens", 512),
                temperature=self.config.get("temperature", 0.7),
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )

        self.total_input_tokens += llm_result.input_tokens
        self.total_output_tokens += llm_result.output_tokens

        # Add assistant response to conversation
        self.conversation.append(
            {
                "role": "assistant",
                "content": llm_result.content,
            }
        )

        # 3. Synthesize speech (result used for streaming via signals)
        await workflow.execute_activity(
            TTSActivities.synthesize_speech,
            SynthesisRequest(
                tenant_id=self.tenant_id,
                session_id=self.session_id,
                text=llm_result.content,
                voice_id=self.config.get("voice_id", "af_heart"),
                language=self.config.get("language", "en-us"),
                speed=self.config.get("speed", 1.0),
            ),
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=retry_policy,
        )

        self.turns += 1

        # 4. Record usage for billing
        await workflow.execute_activity(
            BillingActivities.record_usage,
            UsageEvent(
                tenant_id=self.tenant_id,
                event_type="audio_minutes",
                quantity=transcription.duration_seconds / 60,
                timestamp=datetime.utcnow(),
                metadata={"session_id": self.session_id},
            ),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=retry_policy,
        )

        await workflow.execute_activity(
            BillingActivities.record_usage,
            UsageEvent(
                tenant_id=self.tenant_id,
                event_type="input_tokens",
                quantity=llm_result.input_tokens,
                timestamp=datetime.utcnow(),
                metadata={"session_id": self.session_id},
            ),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=retry_policy,
        )

        await workflow.execute_activity(
            BillingActivities.record_usage,
            UsageEvent(
                tenant_id=self.tenant_id,
                event_type="output_tokens",
                quantity=llm_result.output_tokens,
                timestamp=datetime.utcnow(),
                metadata={"session_id": self.session_id},
            ),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=retry_policy,
        )

        # Send TTS audio back via signal
        # The consumer will receive this and stream to client

    @workflow.signal(name="end_session")
    async def end_session(self) -> None:
        """Signal to end the session."""
        self.is_active = False
        workflow.logger.info(f"Ending voice session {self.session_id}")

    @workflow.query(name="get_status")
    def get_status(self) -> dict[str, Any]:
        """Query current session status."""
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "turns": self.turns,
            "total_audio_seconds": self.total_audio_seconds,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "conversation_length": len(self.conversation),
        }

    @workflow.query(name="get_conversation")
    def get_conversation(self) -> list[dict[str, str]]:
        """Query current conversation history."""
        return self.conversation
