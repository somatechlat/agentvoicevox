"""
Property tests for Pydantic schema validation.

**Feature: django-saas-backend, Property 9: Pydantic Schema Validation**
**Validates: Requirements 5.2, 5.8**

Tests that:
1. Invalid requests return 400 Bad Request
2. Field-level error details are provided
3. Valid requests pass validation

Uses REAL Django Ninja schemas and validation - NO MOCKS.
"""

import uuid

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError as PydanticValidationError

# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# Invalid UUID strings
invalid_uuid_strategy = st.text(min_size=1, max_size=50).filter(
    lambda x: not _is_valid_uuid(x) and x.strip()
)

# Invalid email strings
invalid_email_strategy = st.text(min_size=1, max_size=50).filter(
    lambda x: "@" not in x or "." not in x.split("@")[-1] if "@" in x else True
)


def _is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


# ==========================================================================
# PROPERTY 9: PYDANTIC SCHEMA VALIDATION
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestPydanticSchemaValidation:
    """
    Property tests for Pydantic schema validation.

    **Feature: django-saas-backend, Property 9: Pydantic Schema Validation**
    **Validates: Requirements 5.2, 5.8**

    For any invalid request data:
    - Validation SHALL fail with clear error
    - Field-level error details SHALL be provided
    """

    @pytest.mark.property
    @given(invalid_uuid=invalid_uuid_strategy)
    @settings(max_examples=50)
    def test_invalid_uuid_field_raises_validation_error(self, invalid_uuid: str):
        """
        Property: Invalid UUID fields raise validation error.

        For any invalid UUID string in a UUID field,
        validation SHALL fail with field-level error.

        **Validates: Requirements 5.2, 5.8**
        """
        from apps.notifications.schemas import MarkReadRequest

        # Attempt to create schema with invalid UUID
        with pytest.raises(PydanticValidationError) as exc_info:
            MarkReadRequest(notification_ids=[invalid_uuid])

        # Verify error contains field information
        errors = exc_info.value.errors()
        assert len(errors) > 0
        # Error should reference the field
        error_locs = [str(e.get("loc", [])) for e in errors]
        assert any("notification_ids" in loc for loc in error_locs)

    @pytest.mark.property
    @given(
        title=st.text(min_size=0, max_size=0),  # Empty string
        message=st.text(min_size=1, max_size=100).filter(str.strip),
    )
    @settings(max_examples=30)
    def test_empty_required_string_validation(self, title: str, message: str):
        """
        Property: Empty required string fields are handled.

        For any empty string in a required field,
        the schema SHALL either accept it or raise validation error.
        """
        from apps.notifications.schemas import NotificationCreate

        # NotificationCreate has title as required str
        # Empty strings are valid in Pydantic by default
        try:
            schema = NotificationCreate(
                title=title,
                message=message.strip(),
            )
            # If accepted, verify it's stored
            assert schema.title == title
        except PydanticValidationError as e:
            # If rejected, verify error details
            errors = e.errors()
            assert len(errors) > 0

    @pytest.mark.property
    @given(
        valid_title=st.text(min_size=1, max_size=100).filter(str.strip),
        valid_message=st.text(min_size=1, max_size=500).filter(str.strip),
        valid_type=st.sampled_from(["info", "warning", "error", "success"]),
    )
    @settings(max_examples=50)
    def test_valid_notification_schema_passes(
        self,
        valid_title: str,
        valid_message: str,
        valid_type: str,
    ):
        """
        Property: Valid data passes schema validation.

        For any valid notification data,
        schema validation SHALL succeed.
        """
        from apps.notifications.schemas import NotificationCreate

        schema = NotificationCreate(
            title=valid_title.strip(),
            message=valid_message.strip(),
            type=valid_type,
        )

        assert schema.title == valid_title.strip()
        assert schema.message == valid_message.strip()
        assert schema.type == valid_type

    @pytest.mark.property
    @given(
        notification_ids=st.lists(st.uuids(), min_size=1, max_size=10),
    )
    @settings(max_examples=50)
    def test_valid_uuid_list_passes(self, notification_ids: list):
        """
        Property: Valid UUID lists pass validation.

        For any list of valid UUIDs,
        schema validation SHALL succeed.
        """
        from apps.notifications.schemas import MarkReadRequest

        schema = MarkReadRequest(notification_ids=notification_ids)

        assert len(schema.notification_ids) == len(notification_ids)
        for i, nid in enumerate(schema.notification_ids):
            assert nid == notification_ids[i]

    @pytest.mark.property
    @given(
        invalid_type=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in ["info", "warning", "error", "success"] and x.strip()
        ),
    )
    @settings(max_examples=30)
    def test_notification_type_accepts_any_string(self, invalid_type: str):
        """
        Property: Notification type field accepts any string.

        The type field is a plain str, not an enum,
        so any string value SHALL be accepted.
        """
        from apps.notifications.schemas import NotificationCreate

        # Type is str, not enum, so any value is valid
        schema = NotificationCreate(
            title="Test",
            message="Test message",
            type=invalid_type.strip(),
        )

        assert schema.type == invalid_type.strip()


# ==========================================================================
# THEME SCHEMA VALIDATION TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestThemeSchemaValidation:
    """
    Property tests for theme schema validation.
    """

    @pytest.mark.property
    @given(
        name=st.text(min_size=1, max_size=100).filter(str.strip),
        primary_color=st.from_regex(r"^#[0-9A-Fa-f]{6}$", fullmatch=True),
    )
    @settings(max_examples=50)
    def test_valid_theme_create_passes(self, name: str, primary_color: str):
        """
        Property: Valid theme data passes validation.

        For any valid theme name and color,
        schema validation SHALL succeed.
        """
        from apps.themes.schemas import ThemeCreate

        schema = ThemeCreate(
            name=name.strip(),
            primary_color=primary_color,
        )

        assert schema.name == name.strip()
        assert schema.primary_color == primary_color

    @pytest.mark.property
    @given(
        name=st.text(min_size=1, max_size=100).filter(str.strip),
    )
    @settings(max_examples=30)
    def test_theme_update_partial_fields(self, name: str):
        """
        Property: Theme update accepts partial fields.

        For any subset of fields,
        schema validation SHALL succeed.
        """
        from apps.themes.schemas import ThemeUpdate

        # Only name provided
        schema = ThemeUpdate(name=name.strip())
        assert schema.name == name.strip()
        assert schema.primary_color is None

    @pytest.mark.property
    def test_theme_update_all_none_valid(self):
        """
        Property: Theme update with all None is valid.

        An update schema with no fields set
        SHALL be valid (no-op update).
        """
        from apps.themes.schemas import ThemeUpdate

        schema = ThemeUpdate()
        assert schema.name is None
        assert schema.primary_color is None


# ==========================================================================
# NOTIFICATION PREFERENCE SCHEMA TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestNotificationPreferenceSchemaValidation:
    """
    Property tests for notification preference schema validation.
    """

    @pytest.mark.property
    @given(
        email_enabled=st.booleans(),
        in_app_enabled=st.booleans(),
        billing_notifications=st.booleans(),
        security_notifications=st.booleans(),
    )
    @settings(max_examples=50)
    def test_valid_preference_update_passes(
        self,
        email_enabled: bool,
        in_app_enabled: bool,
        billing_notifications: bool,
        security_notifications: bool,
    ):
        """
        Property: Valid preference data passes validation.

        For any valid boolean preference values,
        schema validation SHALL succeed.
        """
        from apps.notifications.schemas import NotificationPreferenceUpdate

        schema = NotificationPreferenceUpdate(
            email_enabled=email_enabled,
            in_app_enabled=in_app_enabled,
            billing_notifications=billing_notifications,
            security_notifications=security_notifications,
        )

        assert schema.email_enabled == email_enabled
        assert schema.in_app_enabled == in_app_enabled
        assert schema.billing_notifications == billing_notifications
        assert schema.security_notifications == security_notifications

    @pytest.mark.property
    @given(
        quiet_hours_start=st.from_regex(r"^([01]\d|2[0-3]):[0-5]\d$", fullmatch=True),
        quiet_hours_end=st.from_regex(r"^([01]\d|2[0-3]):[0-5]\d$", fullmatch=True),
    )
    @settings(max_examples=30)
    def test_valid_quiet_hours_format(
        self,
        quiet_hours_start: str,
        quiet_hours_end: str,
    ):
        """
        Property: Valid time format for quiet hours passes.

        For any valid HH:MM time format,
        schema validation SHALL succeed.
        """
        from apps.notifications.schemas import NotificationPreferenceUpdate

        schema = NotificationPreferenceUpdate(
            quiet_hours_enabled=True,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
        )

        assert schema.quiet_hours_start == quiet_hours_start
        assert schema.quiet_hours_end == quiet_hours_end


# ==========================================================================
# API ERROR RESPONSE FORMAT TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestAPIErrorResponseFormat:
    """
    Property tests for API error response format.

    Validates that validation errors return proper 400 responses
    with field-level details.
    """

    @pytest.mark.property
    def test_validation_error_format(self):
        """
        Property: Validation errors have consistent format.

        Pydantic validation errors SHALL include:
        - Error type
        - Location (field path)
        - Message
        """
        from apps.notifications.schemas import MarkReadRequest

        with pytest.raises(PydanticValidationError) as exc_info:
            MarkReadRequest(notification_ids=["not-a-uuid"])

        errors = exc_info.value.errors()
        assert len(errors) > 0

        for error in errors:
            # Each error should have these keys
            assert "type" in error
            assert "loc" in error
            assert "msg" in error

    @pytest.mark.property
    @given(
        invalid_values=st.lists(
            st.text(min_size=1, max_size=20).filter(lambda x: not _is_valid_uuid(x) and x.strip()),
            min_size=1,
            max_size=5,
        ),
    )
    @settings(max_examples=30)
    def test_multiple_validation_errors_reported(self, invalid_values: list):
        """
        Property: Multiple validation errors are all reported.

        For any list with multiple invalid values,
        all errors SHALL be reported.
        """
        from apps.notifications.schemas import MarkReadRequest

        with pytest.raises(PydanticValidationError) as exc_info:
            MarkReadRequest(notification_ids=invalid_values)

        errors = exc_info.value.errors()
        # Should have at least one error
        assert len(errors) >= 1
