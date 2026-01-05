"""
Voice Configuration and Data Models
=====================================

This module defines the Django models for storing all voice-related configurations
and data. These models are central to the platform's functionality, defining the
structure for voice personas, available TTS voices, custom-trained voices, and
wake words.

- `VoicePersona`: A tenant-specific configuration that defines a complete voice
  assistant's personality, including voice, STT, and LLM settings.
- `VoiceModel`: A system-wide registry of available, pre-built TTS voices.
- `CustomVoice`: A tenant-specific model representing a voice cloned from a
  user-provided audio sample.
- `WakeWord`: A tenant-specific model for configuring and tracking wake word
  performance.
"""

import uuid

from django.db import models

from apps.tenants.models import TenantScopedManager, TenantScopedModel


class VoicePersona(TenantScopedModel):
    """
    Represents a complete, reusable voice assistant configuration (a "persona").

    Each persona is scoped to a specific tenant and combines settings for TTS (voice),
    STT (transcription), and LLM (language model) to define a unique assistant
    identity. This allows tenants to create and switch between different voices and
    personalities.
    """

    # --- Core Identification ---
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the voice persona.",
    )
    name = models.CharField(
        max_length=255,
        help_text="A human-readable name for the persona (e.g., 'Friendly Helper').",
    )
    description = models.TextField(
        blank=True,
        help_text="A description of the persona's character or purpose.",
    )

    # --- Text-to-Speech (TTS) Settings ---
    voice_id = models.CharField(
        max_length=100,
        default="af_heart",
        help_text="The identifier of the TTS voice model to use (e.g., a Kokoro voice ID).",
    )
    voice_speed = models.FloatField(
        default=1.0,
        help_text="Speech speed multiplier. 1.0 is normal speed, <1.0 is slower, >1.0 is faster.",
    )

    # --- Speech-to-Text (STT) Settings ---
    stt_model = models.CharField(
        max_length=100,
        default="tiny",
        help_text="The Whisper model size to use for transcription (e.g., 'tiny', 'base', 'small').",
    )
    stt_language = models.CharField(
        max_length=10,
        default="en",
        help_text="The language code for STT processing (e.g., 'en', 'es').",
    )

    # --- Large Language Model (LLM) Settings ---
    llm_provider = models.CharField(
        max_length=50,
        default="groq",
        help_text="The LLM provider to use (e.g., 'groq', 'openai', 'ollama').",
    )
    llm_model = models.CharField(
        max_length=100,
        default="llama-3.3-70b-versatile",
        help_text="The specific LLM model to use for generating responses.",
    )
    system_prompt = models.TextField(
        blank=True,
        help_text="The instruction prompt that defines the LLM's personality and rules.",
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="LLM creativity control. Higher values (e.g., 0.9) are more creative, lower values (e.g., 0.2) are more deterministic.",
    )
    max_tokens = models.PositiveIntegerField(
        default=1024,
        help_text="The maximum number of tokens to generate in an LLM response.",
    )

    # --- Advanced Features ---
    solvers = models.JSONField(
        default=list,
        blank=True,
        help_text="A list of enabled 'solver' plugins that can execute tools or actions.",
    )

    # --- Analytics and State ---
    usage_count = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="A counter for how many times this persona has been used in a session.",
    )

    # --- Voice Activity Detection (VAD) / Turn Detection Settings ---
    turn_detection_enabled = models.BooleanField(
        default=True,
        help_text="If enabled, the system will automatically detect when the user has finished speaking.",
    )
    turn_detection_threshold = models.FloatField(
        default=0.5,
        help_text="The confidence threshold for detecting the end of a user's turn.",
    )
    silence_duration_ms = models.PositiveIntegerField(
        default=500,
        help_text="The duration of silence (in milliseconds) to wait for before considering a turn to be over.",
    )

    # --- Status and Timestamps ---
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Inactive personas cannot be used in new sessions.",
    )
    is_default = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Marks this as the default persona for the tenant. Only one can be default.",
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    # --- Django Managers ---
    # Default manager, automatically filters queries by the current tenant.
    objects = TenantScopedManager()
    # Manager to access all records, bypassing the default tenant scoping. Use with caution.
    all_objects = models.Manager()

    class Meta:
        """Model metadata options."""

        db_table = "voice_personas"
        ordering = ["-is_default", "-created_at"]
        constraints = [
            # Enforces that each persona within a tenant must have a unique name.
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_persona_name_per_tenant",
            ),
        ]

    def __str__(self) -> str:
        """Returns a string representation of the voice persona."""
        return self.name

    def to_config(self) -> dict:
        """
        Serializes the persona's settings into a structured dictionary.

        This configuration object is designed to be sent to a client application
        (e.g., a voice agent) to configure its runtime behavior for a voice session.

        Returns:
            A dictionary organized by feature (voice, stt, llm, turn_detection).
        """
        return {
            "voice": {
                "id": self.voice_id,
                "speed": self.voice_speed,
            },
            "stt": {
                "model": self.stt_model,
                "language": self.stt_language,
            },
            "llm": {
                "provider": self.llm_provider,
                "model": self.llm_model,
                "system_prompt": self.system_prompt,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
            "turn_detection": {
                "enabled": self.turn_detection_enabled,
                "threshold": self.turn_detection_threshold,
                "silence_duration_ms": self.silence_duration_ms,
            },
        }


class VoiceModel(models.Model):
    """
    A system-wide registry of available, pre-built TTS voice models.

    This model acts as a catalog of voices that can be assigned to a persona.
    It is not tenant-scoped and is managed by system administrators.
    """

    class Provider(models.TextChoices):
        """Enumeration of supported third-party voice providers."""

        KOKORO = "kokoro", "Kokoro"
        PHOONNX = "phoonnx", "Phoonnx"

    # --- Core Identification ---
    id = models.CharField(
        max_length=100,
        primary_key=True,
        help_text="Unique voice model ID, typically formatted as '{provider}-{name}'.",
    )
    name = models.CharField(
        max_length=255,
        help_text="Human-readable display name for the voice.",
    )
    provider = models.CharField(
        max_length=50,
        choices=Provider.choices,
        help_text="The TTS provider that this voice belongs to.",
    )

    # --- Voice Characteristics ---
    language = models.CharField(
        max_length=10,
        default="en",
        help_text="The primary language code of the voice (e.g., 'en-US').",
    )
    gender = models.CharField(
        max_length=20,
        blank=True,
        help_text="The perceived gender of the voice (e.g., 'Male', 'Female').",
    )
    description = models.TextField(
        blank=True,
        help_text="A brief description of the voice's accent or character.",
    )

    # --- Sample and Status ---
    sample_url = models.URLField(
        blank=True,
        help_text="A URL to an audio file demonstrating the voice.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this voice is available for use in personas.",
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        """Model metadata options."""

        db_table = "voice_models"
        ordering = ["provider", "name"]

    def __str__(self) -> str:
        """Returns a string representation of the voice model."""
        return f"{self.name} ({self.provider})"


class CustomVoice(TenantScopedModel):
    """
    A custom voice cloned from a user-provided audio sample.

    This model tracks the state of a voice cloning job. Each instance is scoped
    to a specific tenant. The process involves uploading an audio sample, which
    is then processed asynchronously to create a new voice.
    """

    class Status(models.TextChoices):
        """The current status of the voice cloning process."""

        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    # --- Core Identification ---
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the custom voice.",
    )
    name = models.CharField(
        max_length=255,
        help_text="A human-readable name for the custom voice.",
    )

    # --- Cloning Job Details ---
    language = models.CharField(
        max_length=10,
        default="en",
        help_text="The language code of the audio sample.",
    )
    quality = models.CharField(
        max_length=50,
        default="balanced",
        help_text="The requested training quality for the voice cloning process.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
        db_index=True,
        help_text="The current status of the voice training job.",
    )
    sample_audio = models.FileField(
        upload_to="voice_cloning/",
        help_text="The uploaded audio file used for training.",
    )
    sample_duration_seconds = models.FloatField(
        default=0,
        help_text="The duration of the sample audio in seconds.",
    )
    error_message = models.TextField(
        blank=True,
        help_text="Contains failure reasons if the cloning job status is 'failed'.",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default custom voice for the tenant.",
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    # --- Django Managers ---
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        """Model metadata options."""

        db_table = "voice_custom_voices"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self) -> str:
        """Returns a string representation of the custom voice."""
        return self.name


class WakeWord(TenantScopedModel):
    """
    Configuration and analytics for a wake word.

    Each instance is scoped to a specific tenant and represents a phrase
    used to activate the voice assistant. This model also stores performance
    metrics for the wake word.
    """

    # --- Core Identification ---
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the wake word configuration.",
    )
    phrase = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The wake word phrase (e.g., 'Hey Mycroft').",
    )

    # --- Configuration and Status ---
    sensitivity = models.FloatField(
        default=0.5,
        help_text="The detection sensitivity threshold (0.0 to 1.0). Higher is more sensitive.",
    )
    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this wake word is actively being listened for.",
    )

    # --- Analytics ---
    detection_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of times this wake word was successfully detected.",
    )
    false_positive_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times the wake word was detected incorrectly.",
    )
    missed_activation_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times the user said the wake word, but it was not detected.",
    )
    last_detected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last time this wake word was successfully detected.",
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    # --- Django Managers ---
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        """Model metadata options."""

        db_table = "voice_wake_words"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self) -> str:
        """Returns a string representation of the wake word."""
        return self.phrase
