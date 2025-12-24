"""
Project models for voice agent configuration.

Projects contain voice agent configurations and settings.
"""
import uuid
from typing import Optional

from django.db import models
from django.utils import timezone

from apps.tenants.models import Tenant, TenantScopedManager, TenantScopedModel


class ProjectManager(TenantScopedManager):
    """Manager for Project model."""

    def active(self):
        """Return only active projects."""
        return self.filter(is_active=True)

    def get_by_slug(self, slug: str) -> Optional["Project"]:
        """Get project by slug within current tenant."""
        try:
            return self.get(slug=slug)
        except Project.DoesNotExist:
            return None


class Project(TenantScopedModel):
    """
    Voice agent project configuration.

    Projects define voice agent behavior, models, and settings.
    Each project can have multiple API keys and sessions.
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
        help_text="Project name",
    )
    slug = models.SlugField(
        max_length=100,
        help_text="URL-friendly identifier",
    )
    description = models.TextField(
        blank=True,
        help_text="Project description",
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the project is active",
    )

    # Voice configuration
    voice_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Voice agent configuration",
    )

    # STT configuration
    stt_model = models.CharField(
        max_length=100,
        default="tiny",
        help_text="Whisper STT model (tiny, base, small, medium, large)",
    )
    stt_language = models.CharField(
        max_length=10,
        default="en",
        help_text="STT language code",
    )

    # TTS configuration
    tts_model = models.CharField(
        max_length=100,
        default="kokoro",
        help_text="TTS model (kokoro, phoonnx)",
    )
    tts_voice = models.CharField(
        max_length=100,
        default="af_heart",
        help_text="TTS voice ID",
    )
    tts_speed = models.FloatField(
        default=1.0,
        help_text="TTS speech speed (0.5-2.0)",
    )

    # LLM configuration
    llm_provider = models.CharField(
        max_length=50,
        default="groq",
        help_text="LLM provider (groq, openai)",
    )
    llm_model = models.CharField(
        max_length=100,
        default="llama-3.3-70b-versatile",
        help_text="LLM model name",
    )
    llm_temperature = models.FloatField(
        default=0.7,
        help_text="LLM temperature (0.0-2.0)",
    )
    llm_max_tokens = models.PositiveIntegerField(
        default=1024,
        help_text="Maximum tokens for LLM response",
    )

    # System prompt
    system_prompt = models.TextField(
        blank=True,
        help_text="System prompt for the voice agent",
    )

    # Turn detection
    turn_detection_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic turn detection",
    )
    turn_detection_threshold = models.FloatField(
        default=0.5,
        help_text="Turn detection silence threshold (seconds)",
    )
    turn_detection_prefix_padding = models.FloatField(
        default=0.3,
        help_text="Audio prefix padding (seconds)",
    )
    turn_detection_silence_duration = models.FloatField(
        default=0.5,
        help_text="Silence duration to end turn (seconds)",
    )

    # Session limits
    max_session_duration = models.PositiveIntegerField(
        default=3600,
        help_text="Maximum session duration in seconds (default 1 hour)",
    )
    max_concurrent_sessions = models.PositiveIntegerField(
        default=10,
        help_text="Maximum concurrent sessions",
    )

    # Webhook configuration
    webhook_url = models.URLField(
        blank=True,
        help_text="Webhook URL for session events",
    )
    webhook_events = models.JSONField(
        default=list,
        blank=True,
        help_text="List of events to send to webhook",
    )

    # Metadata
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional project settings",
    )

    # Ownership
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects",
        help_text="User who created the project",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Manager
    objects = ProjectManager()

    class Meta:
        db_table = "projects"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_project_slug_per_tenant",
            ),
        ]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["tenant", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant.slug})"

    def deactivate(self) -> None:
        """Deactivate the project."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def activate(self) -> None:
        """Activate the project."""
        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])

    def get_voice_config(self) -> dict:
        """Get complete voice configuration."""
        return {
            "stt": {
                "model": self.stt_model,
                "language": self.stt_language,
            },
            "tts": {
                "model": self.tts_model,
                "voice": self.tts_voice,
                "speed": self.tts_speed,
            },
            "llm": {
                "provider": self.llm_provider,
                "model": self.llm_model,
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_max_tokens,
            },
            "turn_detection": {
                "enabled": self.turn_detection_enabled,
                "threshold": self.turn_detection_threshold,
                "prefix_padding": self.turn_detection_prefix_padding,
                "silence_duration": self.turn_detection_silence_duration,
            },
            "system_prompt": self.system_prompt,
            **self.voice_config,
        }

    def update_voice_config(self, config: dict) -> None:
        """Update voice configuration from dict."""
        if "stt" in config:
            stt = config["stt"]
            if "model" in stt:
                self.stt_model = stt["model"]
            if "language" in stt:
                self.stt_language = stt["language"]

        if "tts" in config:
            tts = config["tts"]
            if "model" in tts:
                self.tts_model = tts["model"]
            if "voice" in tts:
                self.tts_voice = tts["voice"]
            if "speed" in tts:
                self.tts_speed = tts["speed"]

        if "llm" in config:
            llm = config["llm"]
            if "provider" in llm:
                self.llm_provider = llm["provider"]
            if "model" in llm:
                self.llm_model = llm["model"]
            if "temperature" in llm:
                self.llm_temperature = llm["temperature"]
            if "max_tokens" in llm:
                self.llm_max_tokens = llm["max_tokens"]

        if "turn_detection" in config:
            td = config["turn_detection"]
            if "enabled" in td:
                self.turn_detection_enabled = td["enabled"]
            if "threshold" in td:
                self.turn_detection_threshold = td["threshold"]
            if "prefix_padding" in td:
                self.turn_detection_prefix_padding = td["prefix_padding"]
            if "silence_duration" in td:
                self.turn_detection_silence_duration = td["silence_duration"]

        if "system_prompt" in config:
            self.system_prompt = config["system_prompt"]

        self.save()
