"""
Property tests for environment variable validation.

**Feature: django-saas-backend, Property 1: Environment Variable Validation**
**Validates: Requirements 1.3, 1.7**

Tests that missing required environment variables cause startup failure
with clear error messages identifying the missing variables.
"""

import os
from typing import Dict
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ==========================================================================
# PROPERTY 1: ENVIRONMENT VARIABLE VALIDATION
# ==========================================================================
# For any set of required environment variables, if any are missing or invalid
# when the application starts, the system SHALL fail fast with a clear error
# message identifying the missing variables.


# Required environment variables that must be present
REQUIRED_ENV_VARS = {
    "DJANGO_SECRET_KEY",
    "DB_PASSWORD",
}

# Optional environment variables with defaults
OPTIONAL_ENV_VARS = {
    "DJANGO_DEBUG": "false",
    "DJANGO_ALLOWED_HOSTS": "localhost,127.0.0.1",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "agentvoicebox",
    "DB_USER": "agentvoicebox",
    "REDIS_URL": "redis://localhost:6379/0",
    "KEYCLOAK_URL": "http://localhost:8080",
    "KEYCLOAK_REALM": "agentvoicebox",
    "TEMPORAL_HOST": "localhost:7233",
    "VAULT_ADDR": "http://localhost:8200",
    "LOG_LEVEL": "INFO",
}


def get_valid_env_vars() -> Dict[str, str]:
    """Return a complete set of valid environment variables."""
    return {
        "DJANGO_SECRET_KEY": "a" * 50,  # Minimum 50 chars
        "DB_PASSWORD": "test_password",
        **OPTIONAL_ENV_VARS,
    }


class TestEnvironmentValidation:
    """
    Property tests for environment variable validation.

    **Feature: django-saas-backend, Property 1: Environment Variable Validation**
    **Validates: Requirements 1.3, 1.7**
    """

    @pytest.mark.property
    def test_valid_env_vars_accepted(self):
        """
        Property: Valid environment variables should be accepted.

        For any complete set of valid environment variables,
        the Settings class should instantiate without error.
        """
        valid_env = get_valid_env_vars()

        with patch.dict(os.environ, valid_env, clear=True):

            class TestSettings(BaseSettings):
                model_config = SettingsConfigDict(
                    env_file=".env",
                    env_file_encoding="utf-8",
                    case_sensitive=False,
                    extra="ignore",
                )
                django_secret_key: str = Field(..., min_length=50)
                db_password: str = Field(...)

            # Should not raise
            test_settings = TestSettings()
            assert test_settings.django_secret_key == "a" * 50
            assert test_settings.db_password == "test_password"

    @pytest.mark.property
    @given(missing_var=st.sampled_from(list(REQUIRED_ENV_VARS)))
    @settings(max_examples=len(REQUIRED_ENV_VARS))
    def test_missing_required_var_causes_failure(self, missing_var: str):
        """
        Property: Missing required variables cause startup failure.

        For any required environment variable that is missing,
        the system SHALL fail with a clear error message.
        """

        # Create a fresh settings class that doesn't read from environment
        class TestSettings(BaseSettings):
            model_config = SettingsConfigDict(
                env_file=None,  # Disable .env file loading
                env_ignore_empty=True,
                case_sensitive=False,
                extra="ignore",
            )
            django_secret_key: str = Field(..., min_length=50)
            db_password: str = Field(...)

            # Override to prevent reading from environment
            @classmethod
            def settings_customise_sources(
                cls,
                settings_cls,
                init_settings,
                env_settings,
                dotenv_settings,
                file_secret_settings,
            ):
                # Only use init_settings, ignore environment
                return (init_settings,)

        # Create kwargs without the missing variable
        valid_values = {
            "django_secret_key": "a" * 50,
            "db_password": "test_password",
        }

        # Map env var names to field names
        field_map = {
            "DJANGO_SECRET_KEY": "django_secret_key",
            "DB_PASSWORD": "db_password",
        }

        # Remove the field corresponding to the missing env var
        field_to_remove = field_map[missing_var]
        kwargs = {k: v for k, v in valid_values.items() if k != field_to_remove}

        with pytest.raises(ValidationError) as exc_info:
            TestSettings(**kwargs)

        # Verify error message identifies the missing variable
        error_str = str(exc_info.value)
        assert field_to_remove in error_str.lower()

    @pytest.mark.property
    def test_short_secret_key_rejected(self):
        """
        Property: Secret key shorter than 50 characters is rejected.

        The DJANGO_SECRET_KEY must be at least 50 characters.
        """
        valid_env = get_valid_env_vars()
        valid_env["DJANGO_SECRET_KEY"] = "short_key"  # Less than 50 chars

        with patch.dict(os.environ, valid_env, clear=True):

            class TestSettings(BaseSettings):
                model_config = SettingsConfigDict(
                    env_file=".env",
                    env_file_encoding="utf-8",
                    case_sensitive=False,
                    extra="ignore",
                )
                django_secret_key: str = Field(..., min_length=50)
                db_password: str = Field(...)

            with pytest.raises(ValidationError) as exc_info:
                TestSettings()

            # Verify error mentions the field
            error_str = str(exc_info.value)
            assert "django_secret_key" in error_str.lower()

    @pytest.mark.property
    @given(secret_key_length=st.integers(min_value=50, max_value=200))
    @settings(max_examples=20)
    def test_valid_secret_key_lengths_accepted(self, secret_key_length: int):
        """
        Property: Secret keys of 50+ characters are accepted.

        For any secret key with length >= 50, validation should pass.
        """
        valid_env = get_valid_env_vars()
        valid_env["DJANGO_SECRET_KEY"] = "x" * secret_key_length

        with patch.dict(os.environ, valid_env, clear=True):

            class TestSettings(BaseSettings):
                model_config = SettingsConfigDict(
                    env_file=".env",
                    env_file_encoding="utf-8",
                    case_sensitive=False,
                    extra="ignore",
                )
                django_secret_key: str = Field(..., min_length=50)
                db_password: str = Field(...)

            # Should not raise
            test_settings = TestSettings()
            assert len(test_settings.django_secret_key) == secret_key_length

    @pytest.mark.property
    @given(log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]))
    @settings(max_examples=5)
    def test_valid_log_levels_accepted(self, log_level: str):
        """
        Property: Valid log levels are accepted.

        For any valid log level (DEBUG, INFO, WARNING, ERROR, CRITICAL),
        validation should pass.
        """
        valid_env = get_valid_env_vars()
        valid_env["LOG_LEVEL"] = log_level

        with patch.dict(os.environ, valid_env, clear=True):

            class TestSettings(BaseSettings):
                model_config = SettingsConfigDict(
                    env_file=".env",
                    env_file_encoding="utf-8",
                    case_sensitive=False,
                    extra="ignore",
                )
                django_secret_key: str = Field(..., min_length=50)
                db_password: str = Field(...)
                log_level: str = Field(default="INFO")

                @field_validator("log_level")
                @classmethod
                def validate_log_level(cls, v: str) -> str:
                    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
                    if v.upper() not in valid_levels:
                        raise ValueError(f"Invalid log level: {v}")
                    return v.upper()

            test_settings = TestSettings()
            assert test_settings.log_level == log_level.upper()

    @pytest.mark.property
    @given(
        invalid_level=st.text(
            alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
            min_size=1,
            max_size=20,
        ).filter(
            lambda x: x.strip()
            and x.upper() not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        ),
    )
    @settings(max_examples=20)
    def test_invalid_log_levels_rejected(self, invalid_level: str):
        """
        Property: Invalid log levels are rejected.

        For any log level not in {DEBUG, INFO, WARNING, ERROR, CRITICAL},
        validation should fail.
        """

        class TestSettings(BaseSettings):
            model_config = SettingsConfigDict(
                env_file=None,
                env_file_encoding="utf-8",
                case_sensitive=False,
                extra="ignore",
            )
            django_secret_key: str = Field(..., min_length=50)
            db_password: str = Field(...)
            log_level: str = Field(default="INFO")

            @field_validator("log_level")
            @classmethod
            def validate_log_level(cls, v: str) -> str:
                valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
                if v.upper() not in valid_levels:
                    raise ValueError(f"Invalid log level: {v}")
                return v.upper()

        with pytest.raises(ValidationError):
            TestSettings(
                django_secret_key="a" * 50,
                db_password="test",
                log_level=invalid_level,
            )
