"""
OpenAI Realtime API compatible models.

These models implement the exact data structures required by the
OpenAI Realtime API specification for 100% compatibility.
"""
import secrets
import uuid
from typing import Optional

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from apps.tenants.models import TenantScopedManager, TenantScopedModel


def generate_session_id() -> str:
    """Generate OpenAI-style session ID (sess_xxx)."""
    return f"sess_{secrets.token_hex(16)}"


def generate_conversation_id() -> str:
    """Generate OpenAI-style conversation ID (conv_xxx)."""
    return f"conv_{secrets.token_hex(16)}"


def generate_item_id() -> str:
    """Generate OpenAI-style item ID (item_xxx)."""
    return f"item_{secrets.token_hex(16)}"


def generate_response_id() -> str:
    """Generate OpenAI-style response ID (resp_xxx)."""
    return f"resp_{secrets.token_hex(16)}"


def generate_event_id() -> str:
    """Generate OpenAI-style event ID (evt_xxx)."""
    return f"evt_{secrets.token_hex(16)}"


class RealtimeSessionManager(TenantScopedManager):
    """Manager for RealtimeSession model."""
    
    def active(self):
        """Return only active sessions."""
        return self.filter(status="active")
    
    def expired(self):
        """Return expired sessions."""
        return self.filter(expires_at__lt=timezone.now())


class RealtimeSession(TenantScopedModel):
    """
    OpenAI Realtime API session.
    
    Stores session configuration and state exactly matching
    the OpenAI Realtime API specification.
    """
    
    class Voice(models.TextChoices):
        """Supported voice options."""
        ALLOY = "alloy", "Alloy"
        ASH = "ash", "Ash"
        BALLAD = "ballad", "Ballad"
        CORAL = "coral", "Coral"
        ECHO = "echo", "Echo"
        SAGE = "sage", "Sage"
        SHIMMER = "shimmer", "Shimmer"
        VERSE = "verse", "Verse"
    
    class AudioFormat(models.TextChoices):
        """Supported audio formats."""
        PCM16 = "pcm16", "PCM 16-bit (24kHz, mono, little-endian)"
        G711_ULAW = "g711_ulaw", "G.711 μ-law (8kHz)"
        G711_ALAW = "g711_alaw", "G.711 A-law (8kHz)"
    
    class Status(models.TextChoices):
        """Session status."""
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"
        ERROR = "error", "Error"
    
    # Primary key - OpenAI format: sess_xxx
    id = models.CharField(
        max_length=64,
        primary_key=True,
        default=generate_session_id,
        editable=False,
    )
    
    # Object type (always "realtime.session")
    object = models.CharField(
        max_length=32,
        default="realtime.session",
        editable=False,
    )
    
    # Model identifier
    model = models.CharField(
        max_length=64,
        default="gpt-4o-realtime-preview",
        help_text="Model identifier",
    )
    
    # === Session Configuration ===
    
    # Modalities: ["text"] or ["text", "audio"]
    modalities = ArrayField(
        models.CharField(max_length=16),
        default=list,
        help_text="Enabled modalities",
    )
    
    # System instructions
    instructions = models.TextField(
        blank=True,
        default="",
        help_text="System prompt / instructions",
    )
    
    # Voice selection
    voice = models.CharField(
        max_length=32,
        choices=Voice.choices,
        default=Voice.ALLOY,
        help_text="Voice for audio output",
    )
    
    # Audio formats
    input_audio_format = models.CharField(
        max_length=16,
        choices=AudioFormat.choices,
        default=AudioFormat.PCM16,
        help_text="Input audio format",
    )
    output_audio_format = models.CharField(
        max_length=16,
        choices=AudioFormat.choices,
        default=AudioFormat.PCM16,
        help_text="Output audio format",
    )
    
    # Input audio transcription config
    # {"model": "whisper-1"}
    input_audio_transcription = models.JSONField(
        null=True,
        blank=True,
        help_text="Transcription configuration",
    )
    
    # Turn detection (VAD) config
    # {"type": "server_vad", "threshold": 0.5, ...}
    turn_detection = models.JSONField(
        null=True,
        blank=True,
        help_text="Turn detection configuration",
    )
    
    # Tools for function calling
    # [{"type": "function", "name": "...", "description": "...", "parameters": {...}}]
    tools = models.JSONField(
        default=list,
        help_text="Function tools",
    )
    
    # Tool choice: "auto", "none", "required", or function name
    tool_choice = models.CharField(
        max_length=64,
        default="auto",
        help_text="Tool choice mode",
    )
    
    # Temperature (0.6 to 1.2)
    temperature = models.FloatField(
        default=0.8,
        help_text="Sampling temperature",
    )
    
    # Max response output tokens (integer or "inf")
    max_response_output_tokens = models.CharField(
        max_length=16,
        default="inf",
        help_text="Max output tokens",
    )
    
    # Input audio noise reduction
    # {"type": "near_field"} or {"type": "far_field"} or null
    input_audio_noise_reduction = models.JSONField(
        null=True,
        blank=True,
        help_text="Noise reduction configuration",
    )
    
    # === Status and Metadata ===
    
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text="Session status",
    )
    
    # API key used to create session (optional)
    api_key = models.ForeignKey(
        "api_keys.APIKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="realtime_sessions",
        help_text="API key used to create session",
    )
    
    # Project association (optional)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="realtime_sessions",
        help_text="Associated project",
    )
    
    # Client info
    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address",
    )
    
    # === Timestamps ===
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Session expiration time",
    )
    
    # Manager
    objects = RealtimeSessionManager()
    
    class Meta:
        db_table = "realtime_sessions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "created_at"]),
        ]
    
    def __str__(self) -> str:
        return f"RealtimeSession {self.id} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Set default modalities if not provided."""
        if not self.modalities:
            self.modalities = ["text", "audio"]
        super().save(*args, **kwargs)
    
    def to_openai_dict(self) -> dict:
        """Convert to OpenAI API response format."""
        return {
            "id": self.id,
            "object": self.object,
            "model": self.model,
            "modalities": self.modalities,
            "instructions": self.instructions,
            "voice": self.voice,
            "input_audio_format": self.input_audio_format,
            "output_audio_format": self.output_audio_format,
            "input_audio_transcription": self.input_audio_transcription,
            "turn_detection": self.turn_detection,
            "tools": self.tools,
            "tool_choice": self.tool_choice,
            "temperature": self.temperature,
            "max_response_output_tokens": self.max_response_output_tokens,
            "input_audio_noise_reduction": self.input_audio_noise_reduction,
        }


class Conversation(models.Model):
    """
    Conversation within a realtime session.
    
    Each session has one active conversation containing items.
    """
    
    # Primary key - OpenAI format: conv_xxx
    id = models.CharField(
        max_length=64,
        primary_key=True,
        default=generate_conversation_id,
        editable=False,
    )
    
    # Object type (always "realtime.conversation")
    object = models.CharField(
        max_length=32,
        default="realtime.conversation",
        editable=False,
    )
    
    # Session association
    session = models.ForeignKey(
        RealtimeSession,
        on_delete=models.CASCADE,
        related_name="conversations",
        help_text="Parent session",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "realtime_conversations"
        ordering = ["created_at"]
    
    def __str__(self) -> str:
        return f"Conversation {self.id}"
    
    def to_openai_dict(self) -> dict:
        """Convert to OpenAI API response format."""
        return {
            "id": self.id,
            "object": self.object,
        }


class ConversationItem(models.Model):
    """
    Item within a conversation.
    
    Items can be messages, function calls, or function call outputs.
    """
    
    class ItemType(models.TextChoices):
        """Item types."""
        MESSAGE = "message", "Message"
        FUNCTION_CALL = "function_call", "Function Call"
        FUNCTION_CALL_OUTPUT = "function_call_output", "Function Call Output"
    
    class Role(models.TextChoices):
        """Message roles."""
        SYSTEM = "system", "System"
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
    
    class ItemStatus(models.TextChoices):
        """Item status."""
        COMPLETED = "completed", "Completed"
        INCOMPLETE = "incomplete", "Incomplete"
        IN_PROGRESS = "in_progress", "In Progress"
    
    # Primary key - OpenAI format: item_xxx
    id = models.CharField(
        max_length=64,
        primary_key=True,
        default=generate_item_id,
        editable=False,
    )
    
    # Object type (always "realtime.item")
    object = models.CharField(
        max_length=32,
        default="realtime.item",
        editable=False,
    )
    
    # Conversation association
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Parent conversation",
    )
    
    # Item type
    type = models.CharField(
        max_length=32,
        choices=ItemType.choices,
        help_text="Item type",
    )
    
    # Role (for message items only)
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        null=True,
        blank=True,
        help_text="Message role",
    )
    
    # Status
    status = models.CharField(
        max_length=16,
        choices=ItemStatus.choices,
        default=ItemStatus.COMPLETED,
        help_text="Item status",
    )
    
    # Content (array of content parts)
    # [{"type": "input_text", "text": "..."}, {"type": "audio", "audio": "base64..."}]
    content = models.JSONField(
        default=list,
        help_text="Content parts",
    )
    
    # Function call specific fields
    name = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        help_text="Function name (for function_call)",
    )
    call_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="Function call ID",
    )
    arguments = models.TextField(
        null=True,
        blank=True,
        help_text="Function arguments JSON",
    )
    output = models.TextField(
        null=True,
        blank=True,
        help_text="Function output (for function_call_output)",
    )
    
    # Ordering within conversation
    position = models.PositiveIntegerField(
        default=0,
        help_text="Position in conversation",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "realtime_conversation_items"
        ordering = ["position", "created_at"]
        indexes = [
            models.Index(fields=["conversation", "position"]),
            models.Index(fields=["type"]),
            models.Index(fields=["call_id"]),
        ]
    
    def __str__(self) -> str:
        return f"Item {self.id} ({self.type})"
    
    def to_openai_dict(self) -> dict:
        """Convert to OpenAI API response format."""
        result = {
            "id": self.id,
            "object": self.object,
            "type": self.type,
            "status": self.status,
        }
        
        if self.type == self.ItemType.MESSAGE:
            result["role"] = self.role
            result["content"] = self.content
        elif self.type == self.ItemType.FUNCTION_CALL:
            result["name"] = self.name
            result["call_id"] = self.call_id
            result["arguments"] = self.arguments
        elif self.type == self.ItemType.FUNCTION_CALL_OUTPUT:
            result["call_id"] = self.call_id
            result["output"] = self.output
        
        return result


class Response(models.Model):
    """
    Response generated by the model.
    
    Tracks response lifecycle and usage statistics.
    """
    
    class ResponseStatus(models.TextChoices):
        """Response status."""
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        INCOMPLETE = "incomplete", "Incomplete"
        FAILED = "failed", "Failed"
    
    # Primary key - OpenAI format: resp_xxx
    id = models.CharField(
        max_length=64,
        primary_key=True,
        default=generate_response_id,
        editable=False,
    )
    
    # Object type (always "realtime.response")
    object = models.CharField(
        max_length=32,
        default="realtime.response",
        editable=False,
    )
    
    # Session association
    session = models.ForeignKey(
        RealtimeSession,
        on_delete=models.CASCADE,
        related_name="responses",
        help_text="Parent session",
    )
    
    # Status
    status = models.CharField(
        max_length=16,
        choices=ResponseStatus.choices,
        default=ResponseStatus.IN_PROGRESS,
        help_text="Response status",
    )
    
    # Status details (for incomplete/failed)
    # {"type": "incomplete", "reason": "..."}
    status_details = models.JSONField(
        null=True,
        blank=True,
        help_text="Status details",
    )
    
    # Output items (array of item IDs)
    output = models.JSONField(
        default=list,
        help_text="Output item IDs",
    )
    
    # Usage statistics
    # {
    #   "total_tokens": 100,
    #   "input_tokens": 50,
    #   "output_tokens": 50,
    #   "input_token_details": {"cached_tokens": 0, "text_tokens": 40, "audio_tokens": 10},
    #   "output_token_details": {"text_tokens": 30, "audio_tokens": 20}
    # }
    usage = models.JSONField(
        null=True,
        blank=True,
        help_text="Token usage statistics",
    )
    
    # Response configuration used
    config = models.JSONField(
        default=dict,
        help_text="Response configuration",
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Completion timestamp",
    )
    
    class Meta:
        db_table = "realtime_responses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["session", "status"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self) -> str:
        return f"Response {self.id} ({self.status})"
    
    def to_openai_dict(self) -> dict:
        """Convert to OpenAI API response format."""
        return {
            "id": self.id,
            "object": self.object,
            "status": self.status,
            "status_details": self.status_details,
            "output": self.output,
            "usage": self.usage,
        }


class EphemeralToken(models.Model):
    """
    Ephemeral token for WebSocket authentication.
    
    Short-lived tokens for browser clients to connect
    without exposing API keys.
    """
    
    # Token value (stored hashed)
    token_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="SHA-256 hash of token",
    )
    
    # Token prefix for identification
    token_prefix = models.CharField(
        max_length=16,
        db_index=True,
        help_text="Token prefix for identification",
    )
    
    # Tenant association
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="ephemeral_tokens",
        help_text="Associated tenant",
    )
    
    # API key that created this token
    api_key = models.ForeignKey(
        "api_keys.APIKey",
        on_delete=models.CASCADE,
        related_name="ephemeral_tokens",
        help_text="API key that created this token",
    )
    
    # Pre-configured session settings
    session_config = models.JSONField(
        default=dict,
        help_text="Pre-configured session settings",
    )
    
    # Expiration
    expires_at = models.DateTimeField(
        help_text="Token expiration time",
    )
    
    # Usage tracking
    used = models.BooleanField(
        default=False,
        help_text="Whether token has been used",
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When token was used",
    )
    
    # Created session (if used)
    session = models.OneToOneField(
        RealtimeSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ephemeral_token",
        help_text="Session created with this token",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "realtime_ephemeral_tokens"
        indexes = [
            models.Index(fields=["token_hash"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["tenant", "expires_at"]),
        ]
    
    def __str__(self) -> str:
        return f"EphemeralToken {self.token_prefix}..."
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired, not used)."""
        return not self.is_expired and not self.used
    
    @classmethod
    def generate_token(cls) -> tuple:
        """
        Generate a new ephemeral token.
        
        Returns:
            Tuple of (full_token, prefix, hash)
        """
        import hashlib
        
        # Generate 32 random bytes
        token_bytes = secrets.token_bytes(32)
        full_token = f"eph_{token_bytes.hex()}"
        
        # Prefix for identification
        prefix = full_token[:12]
        
        # SHA-256 hash for storage
        token_hash = hashlib.sha256(full_token.encode()).hexdigest()
        
        return full_token, prefix, token_hash
    
    @classmethod
    def hash_token(cls, token: str) -> str:
        """Hash a token for comparison."""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()
