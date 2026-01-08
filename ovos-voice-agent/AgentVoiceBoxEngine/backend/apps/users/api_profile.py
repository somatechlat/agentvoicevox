"""
User Profile Management API Endpoints
=====================================

This module provides API endpoints for authenticated users to manage their
own profiles. It handles operations like updating profile information and
changing passwords, coordinating changes between the local database and the
Keycloak identity provider.
"""

from ninja import Router

from apps.core.exceptions import ValidationError
from integrations.keycloak import keycloak_client

from .services import UserService

# Router for user profile endpoints, tagged for OpenAPI documentation.
router = Router(tags=["Profile"])


@router.patch("/profile", summary="Update Current User's Name and Email")
async def update_profile(request, payload: dict):
    """
    Updates the current user's profile information in both the local database and Keycloak.

    This endpoint takes a 'name' and/or 'email' in the payload. It parses the
    full name into first and last names and updates both the local `User` model
    and the user's profile in Keycloak.

    **Payload Fields (JSON):**
    - `name` (str, optional): The user's full name.
    - `email` (str, optional): The user's new email address.

    *Note: This endpoint currently accepts a raw dictionary payload, lacking
    formal schema validation for inputs like email.*

    Returns:
        A dictionary with the updated user's ID, full name, and email.
    """
    user = request.user
    if not user:
        raise ValidationError("User not authenticated")

    name = payload.get("name") or ""
    email = payload.get("email")

    first_name = user.first_name
    last_name = user.last_name
    # This logic parses a full name string into first and last names.
    # It assumes the first word is the first name and the rest is the last name.
    if name:
        parts = name.strip().split(" ")
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    # Update local database record (first and last name).
    updated_user = UserService.update_user(
        user_id=user.id,
        first_name=first_name,
        last_name=last_name,
    )

    # Separately update email if provided.
    if email:
        updated_user.email = email
        updated_user.save(update_fields=["email", "updated_at"])

    # Sync profile changes to the external identity provider.
    if user.keycloak_id:
        await keycloak_client.update_user_profile(
            user_id=user.keycloak_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

    return {
        "id": str(updated_user.id),
        "name": f"{updated_user.first_name} {updated_user.last_name}".strip(),
        "email": updated_user.email,
    }


@router.post("/password", summary="Change Current User's Password")
async def change_password(request, payload: dict):
    """
    Allows the authenticated user to change their own password.

    This endpoint performs a critical security check by first verifying the user's
    current password against Keycloak before setting the new password.

    **Payload Fields (JSON):**
    - `currentPassword` (str): The user's existing password.
    - `newPassword` (str): The desired new password.

    *Note: This endpoint currently accepts a raw dictionary payload, lacking
    formal schema validation.*

    Returns:
        A success message on successful password change.

    Raises:
        ValidationError: If passwords are not provided, the user is not linked
                         to Keycloak, or the current password is incorrect.
    """
    user = request.user
    if not user:
        raise ValidationError("User not authenticated")

    current_password = payload.get("currentPassword")
    new_password = payload.get("newPassword")

    if not current_password or not new_password:
        raise ValidationError("Both current and new passwords are required.")

    if not user.keycloak_id:
        raise ValidationError("This account is not configured for password changes.")

    # 1. Verify the user's current password with Keycloak.
    is_valid = await keycloak_client.verify_user_password(user.email, current_password)
    if not is_valid:
        raise ValidationError("The current password you entered is incorrect.")

    # 2. If valid, set the new password in Keycloak.
    await keycloak_client.set_user_password(
        user.keycloak_id, new_password, temporary=False
    )
    return {"message": "Your password has been updated successfully."}
