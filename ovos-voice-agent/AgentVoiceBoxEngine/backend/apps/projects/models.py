"""
Project Models
==============

This module defines the `Project` model, which serves as a central configuration
hub for a specific voice agent instance.
"""

import uuid
from typing import Optional

from django.db import models

from apps.tenants.models import TenantScopedManager, TenantScopedModel
from apps.users.models import User


class ProjectManager(TenantScopedManager):
    """
    Custom manager for the Project model.

    Inherits from `TenantScopedManager` to ensure that all default queries are
    automatically filtered by the current tenant context.
    """

    def active(self):
        """Returns a queryset containing only active projects."""
        return self.filter(is_active=True)

    def get_by_slug(self, slug: str) -> Optional["Project"]:
        """
        Retrieves a project by its slug, scoped to the current tenant.

        Args:
            slug: The URL-friendly slug of the project.

        Returns:
            A Project instance if found within the current tenant, otherwise None.
        """
        try:
            return self.get(slug=slug)
        except Project.DoesNotExist:
            return None


class Project(TenantScopedModel):
    """
    Represents a self-contained voice agent project.

    Architectural Note:
    A Project holds a complete, denormalized configuration for a voice agent,
    encompassing settings for STT, TTS, LLM, and more. This design allows each
    project to be a fully independent and configurable agent instance, separate
    from the user's default `VoicePersona`. API keys are typically scoped to a
    project, and all sessions run under a specific project's configuration.
    """

    # --- Core Identification ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="The human-readable name of the project.")
    slug = models.SlugField(
        max_length=100,
        help_text="A URL-friendly identifier for the project, unique within the tenant.",
    )
    description = models.TextField(
        blank=True, help_text="An optional description of the project's purpose."
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="If false, API keys for this project will be disabled.",
    )

    # --- Core Voice Agent Configuration ---

    # Speech-to-Text (STT) Configuration
    stt_model = models.CharField(
        max_length=100, default="tiny", help_text="The Whisper model size for transcription."
    )
    stt_language = models.CharField(
        max_length=10, default="en", help_text="The language code for STT processing (e.g., 'en')."
    )

    # Text-to-Speech (TTS) Configuration
    tts_model = models.CharField(
        max_length=100, default="kokoro", help_text="The TTS provider/model to use."
    )
    tts_voice = models.CharField(
        max_length=100,
        default="af_heart",
        help_text="The specific voice ID to use for speech synthesis.",
    )
    tts_speed = models.FloatField(default=1.0, help_text="Speech speed multiplier (1.0 is normal).")

    # Large Language Model (LLM) Configuration
    llm_provider = models.CharField(
        max_length=50, default="groq", help_text="The LLM provider (e.g., 'groq', 'openai')."
    )
    llm_model = models.CharField(
        max_length=100,
        default="llama-3.3-70b-versatile",
        help_text="The specific LLM for generating responses.",
    )
    llm_temperature = models.FloatField(
        default=0.7, help_text="LLM creativity control (0.0 to 2.0)."
    )
    llm_max_tokens = models.PositiveIntegerField(
        default=1024, help_text="The maximum number of tokens for an LLM response."
    )
    system_prompt = models.TextField(
        blank=True,
        help_text="The base instruction prompt that defines the agent's personality and rules for this project.",
    )

    # Voice Activity Detection (VAD) / Turn Detection Configuration
    turn_detection_enabled = models.BooleanField(
        default=True,
        help_text="If true, the system automatically detects when a user has finished speaking.",
    )
    turn_detection_threshold = models.FloatField(
        default=0.5, help_text="The confidence threshold for detecting the end of a user's turn."
    )
    turn_detection_prefix_padding = models.FloatField(
        default=0.3, help_text="Audio padding (in seconds) to include before speech starts."
    )
    turn_detection_silence_duration = models.FloatField(
        default=0.5, help_text="Duration of silence (in seconds) to consider a turn complete."
    )

    # --- Session and Webhook Configuration ---
    max_session_duration = models.PositiveIntegerField(
        default=3600, help_text="Maximum session duration in seconds (default is 1 hour)."
    )
    max_concurrent_sessions = models.PositiveIntegerField(
        default=10, help_text="Maximum number of concurrent sessions allowed for this project."
    )
    webhook_url = models.URLField(blank=True, help_text="A URL to send session-related events to.")
    webhook_events = models.JSONField(
        default=list,
        blank=True,
        help_text="A list of specific event types to send to the webhook (e.g., 'session_start', 'session_end').",
    )

    # --- Miscellaneous ---
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="A flexible JSON field for additional, unstructured project settings.",
    )
    voice_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Legacy or custom voice configuration overrides. Prefer specific fields where available.",
    )

    # --- Ownership and Timestamps ---
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_projects",
        help_text="The user who originally created the project.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Django Managers ---
    objects = ProjectManager()

    class Meta:
        """Model metadata options."""

        db_table = "projects"
        ordering = ["-created_at"]
        constraints = [
            # Ensures that each project within a tenant must have a unique slug.
            models.UniqueConstraint(
                fields=["tenant", "slug"],
                name="unique_project_slug_per_tenant",
            ),
        ]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["tenant", "is_active"]),
        ]

    def __str__(self) -> str:
        """Returns a string representation of the project."""
        return f"{self.name} ({self.tenant.slug if self.tenant else 'No Tenant'})"

    def deactivate(self) -> None:
        """Sets the project's status to inactive."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def activate(self) -> None:
        """Sets the project's status to active."""
        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])

    def get_voice_config(self) -> dict:
        """
        Assembles and returns the complete, structured voice configuration for this project.

        This method gathers all the individual STT, TTS, and LLM fields into a
        nested dictionary, suitable for configuring a client agent for a session.

        Returns:
            A dictionary containing the full agent configuration.
        """
        return {
            "stt": {"model": self.stt_model, "language": self.stt_language},
            "tts": {"model": self.tts_model, "voice": self.tts_voice, "speed": self.tts_speed},
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
            **self.voice_config,  # Merges any legacy or custom config.
        }

    def update_voice_config(self, config: dict) -> None:
        """
        Updates the project's voice configuration from a structured dictionary.

        This method de-structures a configuration dictionary (like one retrieved
        from `get_voice_config`) and applies its values to the corresponding
        fields on the model instance.

        Args:
            config: A dictionary containing the configuration to apply.
        """
        # The `get` method is used to safely access nested dictionaries.
        if stt_config := config.get("stt"):
            self.stt_model = stt_config.get("model", self.stt_model)
            self.stt_language = stt_config.get("language", self.stt_language)

        if tts_config := config.get("tts"):
            self.tts_model = tts_config.get("model", self.tts_model)
            self.tts_voice = tts_config.get("voice", self.tts_voice)
            self.tts_speed = tts_config.get("speed", self.tts_speed)

        if llm_config := config.get("llm"):
            self.llm_provider = llm_config.get("provider", self.llm_provider)
            self.llm_model = llm_config.get("model", self.llm_model)
            self.llm_temperature = llm_config.get("temperature", self.llm_temperature)
            self.llm_max_tokens = llm_config.get("max_tokens", self.llm_max_tokens)

        if td_config := config.get("turn_detection"):
            self.turn_detection_enabled = td_config.get("enabled", self.turn_detection_enabled)
            self.turn_detection_threshold = td_config.get(
                "threshold", self.turn_detection_threshold
            )
            self.turn_detection_prefix_padding = td_config.get(
                "prefix_padding", self.turn_detection_prefix_padding
            )
            self.turn_detection_silence_duration = td_config.get(
                "silence_duration", self.turn_detection_silence_duration
            )

        if "system_prompt" in config:
            self.system_prompt = config["system_prompt"]

        self.save()
