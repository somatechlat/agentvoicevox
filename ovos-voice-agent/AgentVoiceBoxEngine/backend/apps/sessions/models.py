"""
Session models for voice agent sessions.

Sessions track voice interactions and their metrics.
"""
import uuid

from django.db import models
from django.utils import timezone

from apps.tenants.models import TenantScopedManager, TenantScopedModel


class SessionManager(TenantScopedManager):
    """Manager for Session model."""

    def active(self):
        """Return only active sessions."""
        return self.filter(status=Session.Status.ACTIVE)

    def completed(self):
        """Return completed sessions."""
        return self.filter(status=Session.Status.COMPLETED)


class Session(TenantScopedModel):
    """
    Voice agent session.

    Tracks a single voice interaction session with metrics.
    """

    class Status(models.TextChoices):
        """Session status."""
        CREATED = "created", "Created"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ERROR = "error", "Error"
        TERMINATED = "terminated", "Terminated"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Associations
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="Associated project",
    )
    api_key = models.ForeignKey(
        "api_keys.APIKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
        help_text="API key used to create session",
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
        help_text="User who created session (if authenticated)",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
        help_text="Session status",
    )

    # Configuration snapshot
    config = models.JSONField(
        default=dict,
        help_text="Session configuration snapshot",
    )

    # Client info
    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Client user agent",
    )

    # Metrics
    duration_seconds = models.FloatField(
        default=0,
        help_text="Session duration in seconds",
    )
    input_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Total input tokens (LLM)",
    )
    output_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Total output tokens (LLM)",
    )
    audio_input_seconds = models.FloatField(
        default=0,
        help_text="Total audio input duration in seconds",
    )
    audio_output_seconds = models.FloatField(
        default=0,
        help_text="Total audio output duration in seconds",
    )
    turn_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of conversation turns",
    )

    # Error tracking
    error_code = models.CharField(
        max_length=100,
        blank=True,
        help_text="Error code if session ended in error",
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if session ended in error",
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional session metadata",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When session became active",
    )
    terminated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When session was terminated",
    )

    # Manager
    objects = SessionManager()

    class Meta:
        db_table = "sessions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["project"]),
            models.Index(fields=["api_key"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Session {self.id} ({self.status})"

    def start(self) -> None:
        """Start the session."""
        self.status = self.Status.ACTIVE
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at", "updated_at"])

    def complete(self) -> None:
        """Complete the session normally."""
        self.status = self.Status.COMPLETED
        self.terminated_at = timezone.now()
        if self.started_at:
            self.duration_seconds = (self.terminated_at - self.started_at).total_seconds()
        self.save(update_fields=[
            "status",
            "terminated_at",
            "duration_seconds",
            "updated_at",
        ])

    def terminate(self, reason: str = "") -> None:
        """Terminate the session."""
        self.status = self.Status.TERMINATED
        self.terminated_at = timezone.now()
        if self.started_at:
            self.duration_seconds = (self.terminated_at - self.started_at).total_seconds()
        if reason:
            self.metadata["termination_reason"] = reason
        self.save(update_fields=[
            "status",
            "terminated_at",
            "duration_seconds",
            "metadata",
            "updated_at",
        ])

    def set_error(self, error_code: str, error_message: str) -> None:
        """Set session to error state."""
        self.status = self.Status.ERROR
        self.error_code = error_code
        self.error_message = error_message
        self.terminated_at = timezone.now()
        if self.started_at:
            self.duration_seconds = (self.terminated_at - self.started_at).total_seconds()
        self.save(update_fields=[
            "status",
            "error_code",
            "error_message",
            "terminated_at",
            "duration_seconds",
            "updated_at",
        ])

    def update_metrics(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        audio_input_seconds: float = 0,
        audio_output_seconds: float = 0,
        increment_turns: bool = False,
    ) -> None:
        """Update session metrics."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.audio_input_seconds += audio_input_seconds
        self.audio_output_seconds += audio_output_seconds
        if increment_turns:
            self.turn_count += 1
        self.save(update_fields=[
            "input_tokens",
            "output_tokens",
            "audio_input_seconds",
            "audio_output_seconds",
            "turn_count",
            "updated_at",
        ])

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return self.status == self.Status.ACTIVE

    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self.input_tokens + self.output_tokens

    @property
    def total_audio_seconds(self) -> float:
        """Get total audio duration."""
        return self.audio_input_seconds + self.audio_output_seconds


class SessionEvent(models.Model):
    """
    Session event log.

    Tracks individual events within a session.
    """

    class EventType(models.TextChoices):
        """Event types."""
        SESSION_CREATED = "session.created", "Session Created"
        SESSION_STARTED = "session.started", "Session Started"
        SESSION_COMPLETED = "session.completed", "Session Completed"
        SESSION_ERROR = "session.error", "Session Error"
        SESSION_TERMINATED = "session.terminated", "Session Terminated"
        AUDIO_INPUT = "audio.input", "Audio Input"
        AUDIO_OUTPUT = "audio.output", "Audio Output"
        TRANSCRIPTION = "transcription", "Transcription"
        LLM_REQUEST = "llm.request", "LLM Request"
        LLM_RESPONSE = "llm.response", "LLM Response"
        TTS_REQUEST = "tts.request", "TTS Request"
        TTS_RESPONSE = "tts.response", "TTS Response"
        TURN_START = "turn.start", "Turn Start"
        TURN_END = "turn.end", "Turn End"
        ERROR = "error", "Error"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Session association
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="events",
        help_text="Associated session",
    )

    # Event data
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        help_text="Event type",
    )
    data = models.JSONField(
        default=dict,
        help_text="Event data",
    )

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "session_events"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "event_type"]),
            models.Index(fields=["session", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.created_at}"
