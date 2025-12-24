"""
Voice configuration models.

Stores voice personas and configuration for TTS/STT/LLM.
"""
import uuid

from django.db import models

from apps.tenants.models import TenantScopedManager, TenantScopedModel


class VoicePersona(TenantScopedModel):
    """
    Voice persona model.

    Defines a reusable voice configuration with personality,
    voice settings, and LLM instructions.
    """

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Basic info
    name = models.CharField(
        max_length=255,
        help_text="Persona name",
    )
    description = models.TextField(
        blank=True,
        help_text="Persona description",
    )

    # Voice settings
    voice_id = models.CharField(
        max_length=100,
        default="af_heart",
        help_text="Kokoro voice ID",
    )
    voice_speed = models.FloatField(
        default=1.0,
        help_text="Voice speed multiplier",
    )

    # STT settings
    stt_model = models.CharField(
        max_length=100,
        default="tiny",
        help_text="Whisper STT model",
    )
    stt_language = models.CharField(
        max_length=10,
        default="en",
        help_text="STT language code",
    )

    # LLM settings
    llm_provider = models.CharField(
        max_length=50,
        default="groq",
        help_text="LLM provider",
    )
    llm_model = models.CharField(
        max_length=100,
        default="llama-3.3-70b-versatile",
        help_text="LLM model",
    )
    system_prompt = models.TextField(
        blank=True,
        help_text="System prompt for the LLM",
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="LLM temperature",
    )
    max_tokens = models.PositiveIntegerField(
        default=1024,
        help_text="Max tokens for LLM response",
    )

    # Turn detection
    turn_detection_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic turn detection",
    )
    turn_detection_threshold = models.FloatField(
        default=0.5,
        help_text="Turn detection threshold",
    )
    silence_duration_ms = models.PositiveIntegerField(
        default=500,
        help_text="Silence duration for turn detection (ms)",
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the persona is active",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default persona",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "voice_personas"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_persona_name_per_tenant",
            ),
        ]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_default"]),
        ]

    def __str__(self) -> str:
        return self.name

    def to_config(self) -> dict:
        """Convert persona to session configuration."""
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
    Available voice model registry.

    System-wide registry of available TTS voices.
    """

    class Provider(models.TextChoices):
        """Voice providers."""

        KOKORO = "kokoro", "Kokoro"
        PHOONNX = "phoonnx", "Phoonnx"

    # Primary key
    id = models.CharField(
        max_length=100,
        primary_key=True,
        help_text="Voice model ID",
    )

    # Basic info
    name = models.CharField(
        max_length=255,
        help_text="Voice display name",
    )
    provider = models.CharField(
        max_length=50,
        choices=Provider.choices,
        help_text="Voice provider",
    )
    language = models.CharField(
        max_length=10,
        default="en",
        help_text="Voice language",
    )
    gender = models.CharField(
        max_length=20,
        blank=True,
        help_text="Voice gender",
    )
    description = models.TextField(
        blank=True,
        help_text="Voice description",
    )

    # Sample audio
    sample_url = models.URLField(
        blank=True,
        help_text="Sample audio URL",
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the voice is available",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "voice_models"
        ordering = ["provider", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.provider})"
