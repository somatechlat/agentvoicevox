"""
Voice configuration services.

Business logic for voice personas and models.
"""
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet

from apps.tenants.models import Tenant
from apps.voice.models import VoicePersona, VoiceModel


class VoicePersonaService:
    """Service for managing voice personas."""

    @staticmethod
    def list_personas(
        tenant: Tenant,
        active_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[VoicePersona], int]:
        """
        List voice personas for a tenant.

        Returns tuple of (personas, total_count).
        """
        qs = VoicePersona.objects.filter(tenant=tenant)
        if active_only:
            qs = qs.filter(is_active=True)

        total = qs.count()
        offset = (page - 1) * page_size
        personas = list(qs.order_by("-is_default", "-created_at")[offset : offset + page_size])

        return personas, total

    @staticmethod
    def get_persona(persona_id: UUID) -> Optional[VoicePersona]:
        """Get a voice persona by ID."""
        try:
            return VoicePersona.objects.get(id=persona_id)
        except VoicePersona.DoesNotExist:
            return None

    @staticmethod
    def get_default_persona(tenant: Tenant) -> Optional[VoicePersona]:
        """Get the default voice persona for a tenant."""
        try:
            return VoicePersona.objects.get(tenant=tenant, is_default=True, is_active=True)
        except VoicePersona.DoesNotExist:
            return VoicePersona.objects.filter(tenant=tenant, is_active=True).first()

    @staticmethod
    @transaction.atomic
    def create_persona(tenant: Tenant, data: dict) -> VoicePersona:
        """Create a new voice persona."""
        if data.get("is_default"):
            VoicePersona.objects.filter(tenant=tenant, is_default=True).update(
                is_default=False
            )

        persona = VoicePersona.objects.create(tenant=tenant, **data)
        return persona

    @staticmethod
    @transaction.atomic
    def update_persona(persona: VoicePersona, data: dict) -> VoicePersona:
        """Update a voice persona."""
        if data.get("is_default") and not persona.is_default:
            VoicePersona.objects.filter(
                tenant=persona.tenant, is_default=True
            ).update(is_default=False)

        for key, value in data.items():
            if value is not None:
                setattr(persona, key, value)
        persona.save()
        return persona

    @staticmethod
    def delete_persona(persona: VoicePersona) -> None:
        """Delete a voice persona."""
        persona.delete()

    @staticmethod
    def get_persona_config(persona: VoicePersona) -> dict:
        """Get persona configuration for session use."""
        return persona.to_config()


class VoiceModelService:
    """Service for managing voice models."""

    @staticmethod
    def list_models(
        provider: Optional[str] = None,
        language: Optional[str] = None,
        active_only: bool = True,
    ) -> tuple[list[VoiceModel], int]:
        """
        List available voice models.

        Returns tuple of (models, total_count).
        """
        qs = VoiceModel.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        if provider:
            qs = qs.filter(provider=provider)
        if language:
            qs = qs.filter(language=language)

        total = qs.count()
        models = list(qs.order_by("provider", "name"))

        return models, total

    @staticmethod
    def get_model(model_id: str) -> Optional[VoiceModel]:
        """Get a voice model by ID."""
        try:
            return VoiceModel.objects.get(id=model_id)
        except VoiceModel.DoesNotExist:
            return None

    @staticmethod
    def get_providers() -> list[str]:
        """Get list of available voice providers."""
        return list(
            VoiceModel.objects.filter(is_active=True)
            .values_list("provider", flat=True)
            .distinct()
        )

    @staticmethod
    def get_languages() -> list[str]:
        """Get list of available voice languages."""
        return list(
            VoiceModel.objects.filter(is_active=True)
            .values_list("language", flat=True)
            .distinct()
        )

    @staticmethod
    def create_model(data: dict) -> VoiceModel:
        """Create a new voice model (admin only)."""
        return VoiceModel.objects.create(**data)

    @staticmethod
    def update_model(model: VoiceModel, data: dict) -> VoiceModel:
        """Update a voice model (admin only)."""
        for key, value in data.items():
            if value is not None:
                setattr(model, key, value)
        model.save()
        return model

    @staticmethod
    def delete_model(model: VoiceModel) -> None:
        """Delete a voice model (admin only)."""
        model.delete()
