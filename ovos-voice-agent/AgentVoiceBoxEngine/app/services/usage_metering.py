"""Usage Metering Service for Voice Pipeline.

Provides centralized usage tracking for:
- API requests
- Audio input (STT) minutes
- Audio output (TTS) minutes
- LLM tokens (input/output)
- Connection time

Implements Requirements E5.1, E5.2, E5.3, E5.4, E5.5:
- Record usage events in Lago with correct tenant_id and metric code
- Track audio minutes for STT and TTS
- Track LLM token consumption

**Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
**Validates: Requirements E5.1**
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class UsageMeteringService:
    """Centralized usage metering service.

    Wraps Lago service methods with additional logging and validation.
    All methods require tenant_id for proper billing attribution.
    """

    def __init__(self):
        self._lago = None

    def _get_lago(self):
        """Lazy load Lago service."""
        if self._lago is None:
            try:
                from .lago_service import get_lago_service
                self._lago = get_lago_service()
            except Exception as e:
                logger.warning(f"Lago service not available: {e}")
        return self._lago

    def track_api_request(self, tenant_id: str) -> bool:
        """Track an API request for billing.

        Args:
            tenant_id: Tenant ID (REQUIRED)

        Returns:
            True if tracked successfully

        **Validates: Requirements E5.1**
        """
        if not tenant_id:
            logger.warning("Cannot track API request without tenant_id")
            return False

        lago = self._get_lago()
        if lago:
            result = lago.track_api_request(tenant_id)
            logger.debug(f"Tracked API request for tenant {tenant_id}")
            return result
        return False

    def track_stt_audio(
        self,
        tenant_id: str,
        duration_seconds: float,
    ) -> bool:
        """Track STT audio input for billing.

        Args:
            tenant_id: Tenant ID (REQUIRED)
            duration_seconds: Audio duration in seconds

        Returns:
            True if tracked successfully

        **Validates: Requirements E5.2**
        """
        if not tenant_id:
            logger.warning("Cannot track STT audio without tenant_id")
            return False

        if duration_seconds <= 0:
            return True  # Nothing to track

        duration_minutes = duration_seconds / 60.0
        lago = self._get_lago()
        if lago:
            result = lago.track_audio_input(tenant_id, duration_minutes)
            logger.debug(
                f"Tracked STT audio for tenant {tenant_id}: {duration_minutes:.2f} minutes"
            )
            return result
        return False

    def track_tts_audio(
        self,
        tenant_id: str,
        duration_seconds: float,
    ) -> bool:
        """Track TTS audio output for billing.

        Args:
            tenant_id: Tenant ID (REQUIRED)
            duration_seconds: Audio duration in seconds

        Returns:
            True if tracked successfully

        **Validates: Requirements E5.3**
        """
        if not tenant_id:
            logger.warning("Cannot track TTS audio without tenant_id")
            return False

        if duration_seconds <= 0:
            return True  # Nothing to track

        duration_minutes = duration_seconds / 60.0
        lago = self._get_lago()
        if lago:
            result = lago.track_audio_output(tenant_id, duration_minutes)
            logger.debug(
                f"Tracked TTS audio for tenant {tenant_id}: {duration_minutes:.2f} minutes"
            )
            return result
        return False

    def track_llm_usage(
        self,
        tenant_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> bool:
        """Track LLM token usage for billing.

        Args:
            tenant_id: Tenant ID (REQUIRED)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            True if tracked successfully

        **Validates: Requirements E5.4**
        """
        if not tenant_id:
            logger.warning("Cannot track LLM usage without tenant_id")
            return False

        if input_tokens <= 0 and output_tokens <= 0:
            return True  # Nothing to track

        lago = self._get_lago()
        if lago:
            result = lago.track_llm_tokens(tenant_id, input_tokens, output_tokens)
            logger.debug(
                f"Tracked LLM tokens for tenant {tenant_id}: "
                f"{input_tokens} input, {output_tokens} output"
            )
            return result
        return False

    def track_connection_time(
        self,
        tenant_id: str,
        duration_seconds: float,
    ) -> bool:
        """Track WebSocket connection time for billing.

        Args:
            tenant_id: Tenant ID (REQUIRED)
            duration_seconds: Connection duration in seconds

        Returns:
            True if tracked successfully
        """
        if not tenant_id:
            logger.warning("Cannot track connection time without tenant_id")
            return False

        if duration_seconds <= 0:
            return True  # Nothing to track

        duration_minutes = duration_seconds / 60.0
        lago = self._get_lago()
        if lago:
            result = lago.track_connection(tenant_id, duration_minutes)
            logger.debug(
                f"Tracked connection time for tenant {tenant_id}: {duration_minutes:.2f} minutes"
            )
            return result
        return False


# Global singleton
_usage_metering: Optional[UsageMeteringService] = None


def get_usage_metering() -> UsageMeteringService:
    """Get or create the usage metering service singleton."""
    global _usage_metering
    if _usage_metering is None:
        _usage_metering = UsageMeteringService()
    return _usage_metering


# Convenience functions for direct usage
def track_api_request(tenant_id: str) -> bool:
    """Track an API request for billing."""
    return get_usage_metering().track_api_request(tenant_id)


def track_stt_audio(tenant_id: str, duration_seconds: float) -> bool:
    """Track STT audio input for billing."""
    return get_usage_metering().track_stt_audio(tenant_id, duration_seconds)


def track_tts_audio(tenant_id: str, duration_seconds: float) -> bool:
    """Track TTS audio output for billing."""
    return get_usage_metering().track_tts_audio(tenant_id, duration_seconds)


def track_llm_usage(tenant_id: str, input_tokens: int, output_tokens: int) -> bool:
    """Track LLM token usage for billing."""
    return get_usage_metering().track_llm_usage(tenant_id, input_tokens, output_tokens)


def track_connection_time(tenant_id: str, duration_seconds: float) -> bool:
    """Track WebSocket connection time for billing."""
    return get_usage_metering().track_connection_time(tenant_id, duration_seconds)


__all__ = [
    "UsageMeteringService",
    "get_usage_metering",
    "track_api_request",
    "track_stt_audio",
    "track_tts_audio",
    "track_llm_usage",
    "track_connection_time",
]
