"""Property-based tests for usage metering accuracy.

**Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
**Validates: Requirements E5.1**

Tests that all API requests and usage events are properly recorded
with correct tenant_id and metric codes.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Ensure imports work
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.lago_service import MetricCode, UsageEvent


# =============================================================================
# Hypothesis Strategies
# =============================================================================


@st.composite
def tenant_id_strategy(draw):
    """Generate a random tenant ID."""
    return str(draw(st.uuids()))


@st.composite
def audio_duration_strategy(draw):
    """Generate a random audio duration in seconds."""
    return draw(st.floats(min_value=0.1, max_value=3600.0, allow_nan=False, allow_infinity=False))


@st.composite
def token_count_strategy(draw):
    """Generate a random token count."""
    return draw(st.integers(min_value=1, max_value=100000))


# =============================================================================
# Property Tests
# =============================================================================


class TestUsageMeteringAccuracy:
    """Property tests for usage metering accuracy.

    **Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
    **Validates: Requirements E5.1**
    """

    @given(
        tenant_id=tenant_id_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_api_request_includes_tenant_id(self, tenant_id):
        """Property: For any API request, the system SHALL record a usage event
        with the correct tenant_id.

        **Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
        **Validates: Requirements E5.1**
        """
        from app.services.usage_metering import UsageMeteringService

        # Create service with mocked Lago
        service = UsageMeteringService()
        mock_lago = MagicMock()
        mock_lago.track_api_request.return_value = True
        service._lago = mock_lago

        # Track API request
        result = service.track_api_request(tenant_id)

        # Property: Must call Lago with correct tenant_id
        assert result is True
        mock_lago.track_api_request.assert_called_once_with(tenant_id)

    @given(
        tenant_id=tenant_id_strategy(),
        duration_seconds=audio_duration_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_stt_audio_metering_accuracy(self, tenant_id, duration_seconds):
        """Property: For any STT audio, the system SHALL record audio_minutes_input
        with correct tenant_id and duration.

        **Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
        **Validates: Requirements E5.2**
        """
        from app.services.usage_metering import UsageMeteringService

        service = UsageMeteringService()
        mock_lago = MagicMock()
        mock_lago.track_audio_input.return_value = True
        service._lago = mock_lago

        # Track STT audio
        result = service.track_stt_audio(tenant_id, duration_seconds)

        # Property: Must call Lago with correct tenant_id and converted duration
        assert result is True
        expected_minutes = duration_seconds / 60.0
        mock_lago.track_audio_input.assert_called_once_with(tenant_id, expected_minutes)

    @given(
        tenant_id=tenant_id_strategy(),
        duration_seconds=audio_duration_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_tts_audio_metering_accuracy(self, tenant_id, duration_seconds):
        """Property: For any TTS audio, the system SHALL record audio_minutes_output
        with correct tenant_id and duration.

        **Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
        **Validates: Requirements E5.3**
        """
        from app.services.usage_metering import UsageMeteringService

        service = UsageMeteringService()
        mock_lago = MagicMock()
        mock_lago.track_audio_output.return_value = True
        service._lago = mock_lago

        # Track TTS audio
        result = service.track_tts_audio(tenant_id, duration_seconds)

        # Property: Must call Lago with correct tenant_id and converted duration
        assert result is True
        expected_minutes = duration_seconds / 60.0
        mock_lago.track_audio_output.assert_called_once_with(tenant_id, expected_minutes)

    @given(
        tenant_id=tenant_id_strategy(),
        input_tokens=token_count_strategy(),
        output_tokens=token_count_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_llm_token_metering_accuracy(self, tenant_id, input_tokens, output_tokens):
        """Property: For any LLM usage, the system SHALL record llm_tokens_input
        and llm_tokens_output with correct tenant_id and counts.

        **Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
        **Validates: Requirements E5.4**
        """
        from app.services.usage_metering import UsageMeteringService

        service = UsageMeteringService()
        mock_lago = MagicMock()
        mock_lago.track_llm_tokens.return_value = True
        service._lago = mock_lago

        # Track LLM tokens
        result = service.track_llm_usage(tenant_id, input_tokens, output_tokens)

        # Property: Must call Lago with correct tenant_id and token counts
        assert result is True
        mock_lago.track_llm_tokens.assert_called_once_with(
            tenant_id, input_tokens, output_tokens
        )

    @given(
        tenant_id=tenant_id_strategy(),
    )
    @settings(max_examples=50, deadline=None)
    def test_empty_tenant_id_rejected(self, tenant_id):
        """Property: Usage tracking SHALL reject empty tenant_id.

        **Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
        **Validates: Requirements E5.1**
        """
        from app.services.usage_metering import UsageMeteringService

        service = UsageMeteringService()
        mock_lago = MagicMock()
        service._lago = mock_lago

        # Empty tenant_id should be rejected
        result = service.track_api_request("")
        assert result is False
        mock_lago.track_api_request.assert_not_called()

        # None tenant_id should be rejected
        result = service.track_api_request(None)
        assert result is False
        mock_lago.track_api_request.assert_not_called()


class TestUsageEventFormat:
    """Property tests for usage event format.

    **Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
    **Validates: Requirements E5.1**
    """

    @given(
        tenant_id=tenant_id_strategy(),
        metric_code=st.sampled_from(list(MetricCode)),
    )
    @settings(max_examples=100, deadline=None)
    def test_usage_event_contains_required_fields(self, tenant_id, metric_code):
        """Property: For any usage event, the event SHALL contain
        transaction_id, external_customer_id, code, and timestamp.

        **Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
        **Validates: Requirements E5.1**
        """
        from datetime import datetime, timezone

        event = UsageEvent(
            transaction_id=f"evt_{uuid.uuid4().hex}",
            external_customer_id=tenant_id,
            code=metric_code.value,
            timestamp=datetime.now(timezone.utc),
            properties={"test": True},
        )

        event_dict = event.to_dict()

        # Property: All required fields must be present
        assert "transaction_id" in event_dict
        assert "external_customer_id" in event_dict
        assert "code" in event_dict
        assert "timestamp" in event_dict
        assert "properties" in event_dict

        # Property: tenant_id must match
        assert event_dict["external_customer_id"] == tenant_id

        # Property: metric code must match
        assert event_dict["code"] == metric_code.value

    @given(
        tenant_id=tenant_id_strategy(),
        duration_minutes=st.floats(min_value=0.01, max_value=1000.0, allow_nan=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_audio_event_properties(self, tenant_id, duration_minutes):
        """Property: Audio usage events SHALL include duration_minutes in properties.

        **Feature: portal-admin-complete, Property 11: Usage Metering Accuracy**
        **Validates: Requirements E5.2, E5.3**
        """
        from datetime import datetime, timezone

        event = UsageEvent(
            transaction_id=f"evt_{uuid.uuid4().hex}",
            external_customer_id=tenant_id,
            code=MetricCode.AUDIO_MINUTES_INPUT.value,
            timestamp=datetime.now(timezone.utc),
            properties={"duration_minutes": duration_minutes},
        )

        event_dict = event.to_dict()

        # Property: duration_minutes must be in properties
        assert "duration_minutes" in event_dict["properties"]
        assert event_dict["properties"]["duration_minutes"] == duration_minutes


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
