"""
Pydantic Schemas for Speech-to-Text (STT) API
==============================================

This module defines the Pydantic schemas used for validating and serializing
data related to Speech-to-Text (STT) configurations, performance metrics,
and testing results. These schemas are crucial for managing STT integration
settings and understanding its operational characteristics.
"""

from typing import Optional

from ninja import Schema


class STTConfigOut(Schema):
    """
    Defines the response structure for a Speech-to-Text (STT) configuration.
    """

    model: str  # The STT model currently in use (e.g., 'tiny', 'base', 'medium').
    language: str  # The language code configured for STT processing (e.g., 'en', 'es').
    vad_enabled: bool  # Indicates if Voice Activity Detection (VAD) is enabled.
    beam_size: int  # The beam size parameter used by the STT engine for decoding.


class STTConfigUpdate(Schema):
    """
    Defines the request payload for updating an STT configuration.
    All fields are optional to allow for partial updates (PATCH).
    """

    model: Optional[str] = None
    language: Optional[str] = None
    vad_enabled: Optional[bool] = None
    beam_size: Optional[int] = None


class STTMetricsOut(Schema):
    """
    Defines the response structure for STT performance metrics.
    """

    avg_latency_ms: float  # Average latency for STT processing in milliseconds.
    total_minutes: float  # Total audio minutes processed by the STT engine.
    accuracy_estimate: float  # An estimated accuracy score for the STT (e.g., Word Error Rate or similar).


class STTTestOut(Schema):
    """
    Defines the response structure for an STT test.
    """

    transcription: str  # The transcribed text result from the STT engine.
