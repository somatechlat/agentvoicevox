"""
Tenant Onboarding and Self-Serve Signup API
===========================================

This module provides the public-facing API endpoint for user self-serve
signup. It orchestrates the complex process of creating all the necessary
resources for a new tenant to get started.
"""

from django.db import transaction
from django.utils.text import slugify
from ninja import Router

from apps.api_keys.services import APIKeyService
from apps.core.exceptions import ConflictError, ValidationError
from apps.projects.services import ProjectService
from apps.users.services import UserService
from integrations.keycloak import keycloak_client

from .services import TenantService

router = Router(tags=["Onboarding"])


@router.post("/signup", summary="Create a new Tenant and User account")
@transaction.atomic
async def signup(request, payload: dict):
    """
    Handles the self-serve signup process for a new user and organization.

    This public endpoint orchestrates a multi-step process to provision all
    necessary resources for a new account. The entire operation is wrapped in a
    database transaction, but actions involving external services (like Keycloak)
    are not automatically rolled back.

    **Payload Fields:**
    - `email` (str): The new user's email address.
    - `password` (str): The desired password for the new user.
    - `first_name` (str): The user's first name.
    - `last_name` (str): The user's last name.
    - `organization_name` (str): The name of the new organization/tenant.
    - `use_case` (str, optional): A description of the user's intended use case.

    **Orchestration Steps:**
    1.  Validates that all required fields are present.
    2.  Generates a unique URL-friendly slug for the organization.
    3.  Creates a new `Tenant` instance with a 'starter' tier.
    4.  Creates a corresponding user account in the Keycloak identity provider.
    5.  Sets the new Keycloak user's password.
    6.  Creates a local `User` record linked to the tenant and Keycloak ID.
    7.  Activates the new tenant.
    8.  Provisions a "Default Project" for the new tenant.
    9.  Generates a "Default API Key" scoped to the user and default project.
    10. Returns key details including IDs and the full API key.

    Returns:
        A dictionary containing the new tenant ID, user ID, project ID, the full
        API key, and next steps for the user.
    """
    # 1. Extract and validate payload data
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")
    first_name = payload.get("first_name", "").strip()
    last_name = payload.get("last_name", "").strip()
    organization_name = payload.get("organization_name", "").strip()
    use_case = payload.get("use_case")

    if not all([email, password, first_name, last_name, organization_name]):
        raise ValidationError(
            "Missing required signup fields: email, password, first_name, last_name, organization_name"
        )

    # 2. Create a unique tenant slug
    slug_base = slugify(organization_name) or "tenant"
    slug = slug_base
    idx = 1
    while True:
        try:
            # 3. Create the Tenant instance (within the transaction)
            tenant = TenantService.create_tenant(
                name=organization_name, slug=slug, tier="starter"
            )
            break  # Emerge on success
        except ConflictError:
            # This logic handles the case where a slug already exists by appending a number.
            idx += 1
            slug = f"{slug_base}-{idx}"
        # A broader exception catch is a safety net but could mask other issues.
        except Exception as e:
            # In a production scenario, this should be logged.
            raise e

    # Store optional metadata
    tenant.settings["use_case"] = use_case
    tenant.save(update_fields=["settings", "updated_at"])

    # 4. Create the user in the external identity provider (Keycloak)
    # This is an external call and will not be rolled back by the Django transaction on failure.
    keycloak_id = await keycloak_client.create_user(
        email=email,
        first_name=first_name,
        last_name=last_name,
        tenant_id=str(tenant.id),
        enabled=True,
    )
    # 5. Set the user's password in Keycloak
    await keycloak_client.set_user_password(keycloak_id, password, temporary=False)

    # 6. Create the local User database record
    user = UserService.create_user(
        tenant=tenant,
        email=email,
        role="admin",  # The first user is always an admin
        first_name=first_name,
        last_name=last_name,
        keycloak_id=keycloak_id,
    )

    # 7. Activate the tenant now that the admin user exists
    TenantService.activate_tenant(tenant.id)

    # 8. Provision a default project for the user to start with
    project = ProjectService.create_project(
        tenant=tenant,
        name="Default Project",
        slug="default",
        created_by=user,
    )

    # 9. Generate a default API key for immediate use
    api_key, full_key = APIKeyService.create_key(
        tenant=tenant,
        name="Default API Key",
        created_by=user,
        project_id=project.id,
    )

    # 10. Return the successful response payload
    return {
        "tenant_id": str(tenant.id),
        "user_id": str(user.id),
        "project_id": str(project.id),
        "api_key": full_key,
        "api_key_prefix": api_key.key_prefix,
        "message": "Signup complete",
        "next_steps": [
            "Use the API key to connect your client",
            "Configure personas and voice settings",
            "Start a realtime session",
        ],
    }
