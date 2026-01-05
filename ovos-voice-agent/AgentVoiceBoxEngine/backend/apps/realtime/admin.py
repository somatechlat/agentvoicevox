"""
Django admin configuration for OpenAI Realtime API models.
"""

from django.contrib import admin

from .models import (
    Conversation,
    ConversationItem,
    EphemeralToken,
    RealtimeSession,
    Response,
)


@admin.register(RealtimeSession)
class RealtimeSessionAdmin(admin.ModelAdmin):
    """Admin for RealtimeSession model."""

    list_display = [
        "id",
        "tenant",
        "status",
        "model",
        "voice",
        "created_at",
    ]
    list_filter = ["status", "voice", "model", "created_at"]
    search_fields = ["id", "tenant__name"]
    readonly_fields = ["id", "object", "created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin for Conversation model."""

    list_display = ["id", "session", "created_at"]
    search_fields = ["id", "session__id"]
    readonly_fields = ["id", "object", "created_at"]
    ordering = ["-created_at"]


@admin.register(ConversationItem)
class ConversationItemAdmin(admin.ModelAdmin):
    """Admin for ConversationItem model."""

    list_display = ["id", "conversation", "type", "role", "status", "position"]
    list_filter = ["type", "role", "status"]
    search_fields = ["id", "conversation__id"]
    readonly_fields = ["id", "object", "created_at"]
    ordering = ["conversation", "position"]


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    """Admin for Response model."""

    list_display = ["id", "session", "status", "created_at", "completed_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["id", "session__id"]
    readonly_fields = ["id", "object", "created_at"]
    ordering = ["-created_at"]


@admin.register(EphemeralToken)
class EphemeralTokenAdmin(admin.ModelAdmin):
    """Admin for EphemeralToken model."""

    list_display = [
        "token_prefix",
        "tenant",
        "used",
        "expires_at",
        "created_at",
    ]
    list_filter = ["used", "expires_at", "created_at"]
    search_fields = ["token_prefix", "tenant__name"]
    readonly_fields = ["token_hash", "token_prefix", "created_at"]
    ordering = ["-created_at"]
