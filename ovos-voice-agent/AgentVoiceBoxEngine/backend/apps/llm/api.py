"""
LLM Configuration and Testing API Endpoints
===========================================

This module provides API endpoints for managing Large Language Model (LLM)
configurations and for testing LLM provider integrations. These endpoints
allow tenants to set up their preferred LLM models and API keys, which are
securely stored in HashiCorp Vault.
"""

from ninja import Router

from apps.core.exceptions import (
    FeatureNotImplementedError,
    ValidationError,
)
from apps.core.permissions.decorators import require_granular_role
from apps.tenants.services import TenantSettingsService
from apps.workflows.activities.llm import LLMActivities, LLMRequest, Message

from .schemas import LLMConfigOut, LLMConfigUpdate, LLMTestRequest, LLMTestResponse
from .services import LLMConfigService

# Router for LLM configuration and testing endpoints.
router = Router(tags=["LLM Integrations"])


@require_granular_role(["tenant_admin", "saas_admin"])
@router.get("/config", response=LLMConfigOut, summary="Get LLM Configuration")
def get_llm_config(request):
    """
    Retrieves the current LLM configuration for the authenticated tenant.

    This includes both default settings stored in `TenantSettings` and any
    sensitive API keys/base URLs retrieved from Vault.

    **Permissions:** Requires TENANT_ADMIN or SaaS_ADMIN role.
    """
    settings = LLMConfigService.get_tenant_settings(request.tenant.id)
    secrets = LLMConfigService.read_secrets(request.tenant.id)

    return LLMConfigOut(
        provider=settings.default_llm_provider,
        model=settings.default_llm_model,
        temperature=settings.default_llm_temperature,
        max_tokens=settings.default_llm_max_tokens,
        openai_api_key=secrets.get(
            "openai_api_key", ""
        ),  # Return empty string if not found.
        groq_api_key=secrets.get(
            "groq_api_key", ""
        ),  # Return empty string if not found.
        ollama_base_url=secrets.get(
            "ollama_base_url", ""
        ),  # Return empty string if not found.
    )


@require_granular_role(["tenant_admin", "saas_admin"])
@router.patch("/config", response=LLMConfigOut, summary="Update LLM Configuration")
def update_llm_config(request, payload: LLMConfigUpdate):
    """
    Updates the LLM configuration for the authenticated tenant.

    This endpoint handles updates to both general LLM settings (like provider,
    model, temperature, max_tokens) which are stored in `TenantSettings`,
    and sensitive credentials (like API keys, base URLs) which are securely
    stored in Vault. A `None` value for an API key in the payload will remove
    that key from Vault.

    **Permissions:** Requires TENANT_ADMIN role.
    """

    # Update general LLM settings in TenantSettings.
    settings = TenantSettingsService.update_voice_defaults(
        tenant_id=request.tenant.id,
        default_llm_provider=payload.provider,
        default_llm_model=payload.model,
        default_llm_temperature=payload.temperature,
        default_llm_max_tokens=payload.max_tokens,
    )

    # Handle sensitive API keys and base URLs (stored in Vault).
    # Check if any secret-related fields are present in the payload.
    if (
        payload.openai_api_key is not None
        or payload.groq_api_key is not None
        or payload.ollama_base_url is not None
    ):
        existing_secrets = LLMConfigService.read_secrets(request.tenant.id)
        updated_secrets = LLMConfigService.merge_secrets(
            existing_secrets,
            {
                "openai_api_key": payload.openai_api_key,
                "groq_api_key": payload.groq_api_key,
                "ollama_base_url": payload.ollama_base_url,
            },
        )
        LLMConfigService.write_secrets(request.tenant.id, updated_secrets)
        retrieved_secrets_for_response = updated_secrets
    else:
        # If no secret fields were in payload, re-read existing secrets for response.
        retrieved_secrets_for_response = LLMConfigService.read_secrets(
            request.tenant.id
        )

    return LLMConfigOut(
        provider=settings.default_llm_provider,
        model=settings.default_llm_model,
        temperature=settings.default_llm_temperature,
        max_tokens=settings.default_llm_max_tokens,
        openai_api_key=retrieved_secrets_for_response.get("openai_api_key", ""),
        groq_api_key=retrieved_secrets_for_response.get("groq_api_key", ""),
        ollama_base_url=retrieved_secrets_for_response.get("ollama_base_url", ""),
    )


@require_granular_role(["agent_admin", "tenant_admin", "saas_admin"])
@router.post("/test", response=LLMTestResponse, summary="Test LLM Configuration")
async def test_llm(request, payload: LLMTestRequest):
    """
    Tests the current LLM configuration for the authenticated tenant by sending
    a prompt and receiving a response.

    This endpoint uses the configured LLM provider and credentials to ensure
    the integration is working correctly.

    **Permissions:** Requires AGENT_ADMIN or TENANT_ADMIN role.
    """
    if not payload.prompt.strip():
        raise ValidationError("Prompt is required")

    settings = LLMConfigService.get_tenant_settings(request.tenant.id)
    secrets = LLMConfigService.read_secrets(request.tenant.id)

    # Ensure the configured provider is supported by the testing workflow.
    if settings.default_llm_provider not in {"groq", "openai", "ollama"}:
        raise FeatureNotImplementedError("Unsupported LLM provider for testing.")

    # Construct the LLM request payload for the workflow activity.
    llm_request = LLMRequest(
        tenant_id=str(request.tenant.id),
        session_id="llm-test",  # A special session ID for testing purposes.
        messages=[Message(role="user", content=payload.prompt)],
        model=settings.default_llm_model,
        provider=settings.default_llm_provider,
        max_tokens=settings.default_llm_max_tokens,
        temperature=settings.default_llm_temperature,
        api_keys={
            "groq": secrets.get("groq_api_key", ""),
            "openai": secrets.get("openai_api_key", ""),
        },
        ollama_base_url=secrets.get("ollama_base_url", ""),
    )

    # Execute the LLM generation workflow activity.
    result = await LLMActivities().generate_response(llm_request)
    return LLMTestResponse(response=result.content)
