"""
Voice Configuration and Management Services
===========================================

This module contains the business logic for managing voice personas and voice
models. The services defined here are consumed by the API layer (and other parts
of the application) to perform operations in a structured and secure way.

The `VoicePersonaService` handles all logic related to tenant-specific voice
configurations, while the `VoiceModelService` provides an interface for managing the
globally available TTS voice models.
"""

from typing import Optional
from uuid import UUID

from django.db import transaction

from apps.tenants.models import Tenant
from apps.voice.models import VoiceModel, VoicePersona


class VoicePersonaService:
    """
    A service class encapsulating all business logic for managing VoicePersonas.

    This service ensures that all operations are correctly scoped to a tenant
    and handles complex logic, such as setting default personas atomically.
    """

    @staticmethod
    def list_personas(
        tenant: Tenant,
        active_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[VoicePersona], int]:
        """
        Lists voice personas for a specific tenant with pagination.

        This method retrieves a paginated list of personas, ensuring that only
        personas belonging to the provided tenant are returned.

        Args:
            tenant: The Tenant for which to list personas.
            active_only: If True, only returns personas where `is_active` is True.
            page: The page number to retrieve.
            page_size: The number of items to include on a page.

        Returns:
            A tuple containing:
            - A list of VoicePersona model instances.
            - An integer representing the total number of matching personas.
        """
        qs = VoicePersona.objects.filter(tenant=tenant)
        if active_only:
            qs = qs.filter(is_active=True)

        total = qs.count()
        offset = (page - 1) * page_size
        # Order by `is_default` to ensure the default persona appears first.
        personas = list(
            qs.order_by("-is_default", "-created_at")[offset : offset + page_size]
        )

        return personas, total

    @staticmethod
    def get_persona(
        persona_id: UUID, tenant: Optional[Tenant] = None
    ) -> Optional[VoicePersona]:
        """
        Retrieves a single voice persona by its ID.

        If a tenant is provided, the query is restricted to that tenant, ensuring
        data isolation.

        Args:
            persona_id: The UUID of the voice persona to retrieve.
            tenant: (Optional) The tenant to scope the query to.

        Returns:
            A VoicePersona model instance if found, otherwise None.
        """
        try:
            qs = VoicePersona.objects
            if tenant is not None:
                qs = qs.filter(tenant=tenant)
            return qs.get(id=persona_id)
        except VoicePersona.DoesNotExist:
            return None

    @staticmethod
    def get_default_persona(tenant: Tenant) -> Optional[VoicePersona]:
        """
        Gets the default voice persona for a tenant, with fallback logic.

        It first tries to find an active persona explicitly marked as default.
        If none exists, it falls back to the most recently created active persona
        for that tenant.

        Args:
            tenant: The tenant for which to find the default persona.

        Returns:
            The default VoicePersona instance, or None if no active personas exist.
        """
        try:
            # Prioritize the explicitly set, active default persona.
            return VoicePersona.objects.get(
                tenant=tenant, is_default=True, is_active=True
            )
        except VoicePersona.DoesNotExist:
            # Fallback: return the most recent active persona if no explicit default is set.
            return (
                VoicePersona.objects.filter(tenant=tenant, is_active=True)
                .order_by("-created_at")
                .first()
            )

    @staticmethod
    @transaction.atomic
    def create_persona(tenant: Tenant, data: dict) -> VoicePersona:
        """
        Creates a new voice persona for a tenant within a database transaction.

        If the `is_default` flag is set to True in the payload, this method
        atomically ensures that any other persona for the same tenant is
        unmarked as the default.

        Args:
            tenant: The tenant who will own the new persona.
            data: A dictionary of data for the new persona, conforming to
                  the VoicePersona model fields.

        Returns:
            The newly created VoicePersona instance.
        """
        if data.get("is_default"):
            # Ensure only one default persona exists per tenant.
            VoicePersona.objects.filter(tenant=tenant, is_default=True).update(
                is_default=False
            )

        persona = VoicePersona.objects.create(tenant=tenant, **data)
        return persona

    @staticmethod
    @transaction.atomic
    def update_persona(persona: VoicePersona, data: dict) -> VoicePersona:
        """
        Updates an existing voice persona within a database transaction.

        If the `is_default` flag is being set to True, this method atomically
        unsets the flag on any other persona for the same tenant. It performs
        a partial update based on the keys provided in the data dictionary.

        Args:
            persona: The VoicePersona instance to update.
            data: A dictionary containing the fields to update.

        Returns:
            The updated VoicePersona instance.
        """
        # If 'is_default' is being set to True on this persona
        if data.get("is_default") and not persona.is_default:
            # Find the current default (if any) for this tenant and unset it.
            VoicePersona.objects.filter(tenant=persona.tenant, is_default=True).update(
                is_default=False
            )

        # Apply the updates from the data dictionary.
        for key, value in data.items():
            if value is not None:
                setattr(persona, key, value)
        persona.save()
        return persona

    @staticmethod
    def delete_persona(persona: VoicePersona) -> None:
        """
        Deletes a voice persona from the database.

        Args:
            persona: The VoicePersona instance to delete.
        """
        persona.delete()

    @staticmethod
    def get_persona_config(persona: VoicePersona) -> dict:
        """
        Generates a configuration dictionary from a persona instance.

        This method delegates to the `to_config` method on the model, providing
        a service-layer accessor for this functionality. The resulting dictionary
        is intended for use in voice sessions.

        Args:
            persona: The VoicePersona instance.

        Returns:
            A dictionary containing the persona's configuration.
        """
        return persona.to_config()


class VoiceModelService:
    """
    A service class for managing globally available VoiceModels.

    These operations are generally not tenant-scoped, as voice models are
    considered a system-wide resource. Administrative actions (create, update,
    delete) are implicitly restricted to admin users at the API layer.
    """

    @staticmethod
    def list_models(
        provider: Optional[str] = None,
        language: Optional[str] = None,
        active_only: bool = True,
    ) -> tuple[list[VoiceModel], int]:
        """
        Lists available voice models, with optional filtering.

        Args:
            provider: (Optional) Filter models by the provider name (e.g., 'elevenlabs').
            language: (Optional) Filter models by language code (e.g., 'en-US').
            active_only: If True, only returns models where `is_active` is True.

        Returns:
            A tuple containing:
            - A list of VoiceModel instances.
            - An integer representing the total number of matching models.
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
        """
        Retrieves a single voice model by its ID.

        Args:
            model_id: The unique ID of the voice model.

        Returns:
            A VoiceModel instance if found, otherwise None.
        """
        try:
            return VoiceModel.objects.get(id=model_id)
        except VoiceModel.DoesNotExist:
            return None

    @staticmethod
    def get_providers() -> list[str]:
        """
        Gets a list of unique voice providers from active models.

        Returns:
            A list of strings, where each string is a unique provider name.
        """
        return list(
            VoiceModel.objects.filter(is_active=True)
            .values_list("provider", flat=True)
            .distinct()
        )

    @staticmethod
    def get_languages() -> list[str]:
        """
        Gets a list of unique languages from active voice models.

        Returns:
            A list of strings, where each string is a unique language code.
        """
        return list(
            VoiceModel.objects.filter(is_active=True)
            .values_list("language", flat=True)
            .distinct()
        )

    @staticmethod
    def create_model(data: dict) -> VoiceModel:
        """
        Creates a new voice model. (Admin-only operation).

        Args:
            data: A dictionary of data for the new model.

        Returns:
            The newly created VoiceModel instance.
        """
        return VoiceModel.objects.create(**data)

    @staticmethod
    def update_model(model: VoiceModel, data: dict) -> VoiceModel:
        """
        Updates an existing voice model. (Admin-only operation).

        Performs a partial update based on the keys provided in the data dictionary.

        Args:
            model: The VoiceModel instance to update.
            data: A dictionary containing the fields to update.

        Returns:
            The updated VoiceModel instance.
        """
        for key, value in data.items():
            if value is not None:
                setattr(model, key, value)
        model.save()
        return model

    @staticmethod
    def delete_model(model: VoiceModel) -> None:
        """
        Deletes a voice model. (Admin-only operation).

        Args:
            model: The VoiceModel instance to delete.
        """
        model.delete()
