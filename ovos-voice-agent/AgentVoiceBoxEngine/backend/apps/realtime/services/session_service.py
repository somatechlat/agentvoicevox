"""
Realtime session service.

Manages session lifecycle and configuration.
"""

import logging
from datetime import timedelta
from typing import Optional
from uuid import UUID

from django.utils import timezone

from apps.api_keys.models import APIKey
from apps.realtime.models import Conversation, RealtimeSession
from apps.realtime.schemas import SessionConfig

logger = logging.getLogger(__name__)


class RealtimeSessionService:
    """
    Manages realtime session lifecycle and configuration.
    """

    DEFAULT_SESSION_TTL = 3600  # 1 hour

    async def create_session(
        self,
        tenant_id: UUID,
        config: Optional[SessionConfig] = None,
        api_key: Optional[APIKey] = None,
        project_id: Optional[UUID] = None,
        client_ip: Optional[str] = None,
    ) -> RealtimeSession:
        """
        Create a new realtime session.

        Args:
            tenant_id: Tenant UUID
            config: Session configuration
            api_key: API key used to create session
            project_id: Associated project ID
            client_ip: Client IP address

        Returns:
            Created RealtimeSession
        """
        # Build session data from config
        session_data = {
            "tenant_id": tenant_id,
            "status": RealtimeSession.Status.ACTIVE,
            "expires_at": timezone.now() + timedelta(seconds=self.DEFAULT_SESSION_TTL),
        }

        if api_key:
            session_data["api_key"] = api_key

        if project_id:
            session_data["project_id"] = project_id

        if client_ip:
            session_data["client_ip"] = client_ip

        # Apply configuration
        if config:
            session_data.update(
                {
                    "modalities": config.modalities,
                    "instructions": config.instructions or "",
                    "voice": config.voice,
                    "input_audio_format": config.input_audio_format,
                    "output_audio_format": config.output_audio_format,
                    "input_audio_transcription": (
                        config.input_audio_transcription.model_dump()
                        if config.input_audio_transcription
                        else None
                    ),
                    "turn_detection": (
                        config.turn_detection.model_dump() if config.turn_detection else None
                    ),
                    "tools": [t.model_dump() for t in config.tools] if config.tools else [],
                    "tool_choice": config.tool_choice,
                    "temperature": config.temperature,
                    "max_response_output_tokens": config.max_response_output_tokens,
                    "input_audio_noise_reduction": (
                        config.input_audio_noise_reduction.model_dump()
                        if config.input_audio_noise_reduction
                        else None
                    ),
                }
            )

        # Create session
        session = await RealtimeSession.objects.acreate(**session_data)

        # Create default conversation
        await Conversation.objects.acreate(session=session)

        logger.info(f"Created realtime session {session.id} for tenant {tenant_id}")

        return session

    async def get_session(
        self,
        session_id: str,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[RealtimeSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session ID
            tenant_id: Optional tenant ID for validation

        Returns:
            RealtimeSession if found
        """
        filters = {"id": session_id}
        if tenant_id:
            filters["tenant_id"] = tenant_id

        return await RealtimeSession.objects.filter(**filters).afirst()

    async def update_session(
        self,
        session_id: str,
        config: SessionConfig,
        tenant_id: Optional[UUID] = None,
    ) -> Optional[RealtimeSession]:
        """
        Update session configuration.

        Note: Voice cannot be changed after first use per OpenAI spec.

        Args:
            session_id: Session ID
            config: New configuration
            tenant_id: Optional tenant ID for validation

        Returns:
            Updated RealtimeSession
        """
        session = await self.get_session(session_id, tenant_id)
        if not session:
            return None

        # Update allowed fields
        session.modalities = config.modalities
        if config.instructions is not None:
            session.instructions = config.instructions
        # Note: voice is NOT updated after creation per OpenAI spec
        session.input_audio_format = config.input_audio_format
        session.output_audio_format = config.output_audio_format

        if config.input_audio_transcription:
            session.input_audio_transcription = config.input_audio_transcription.model_dump()

        if config.turn_detection:
            session.turn_detection = config.turn_detection.model_dump()
        elif config.turn_detection is None:
            session.turn_detection = None

        if config.tools is not None:
            session.tools = [t.model_dump() for t in config.tools]

        session.tool_choice = config.tool_choice
        session.temperature = config.temperature
        session.max_response_output_tokens = config.max_response_output_tokens

        if config.input_audio_noise_reduction:
            session.input_audio_noise_reduction = config.input_audio_noise_reduction.model_dump()
        elif config.input_audio_noise_reduction is None:
            session.input_audio_noise_reduction = None

        await session.asave()

        logger.info(f"Updated realtime session {session_id}")

        return session

    async def terminate_session(
        self,
        session_id: str,
        tenant_id: Optional[UUID] = None,
        status: str = RealtimeSession.Status.COMPLETED,
    ) -> bool:
        """
        Terminate a session.

        Args:
            session_id: Session ID
            tenant_id: Optional tenant ID for validation
            status: Final status

        Returns:
            True if terminated
        """
        filters = {"id": session_id}
        if tenant_id:
            filters["tenant_id"] = tenant_id

        updated = await RealtimeSession.objects.filter(**filters).aupdate(
            status=status,
            updated_at=timezone.now(),
        )

        if updated:
            logger.info(f"Terminated realtime session {session_id} with status {status}")

        return updated > 0

    async def list_sessions(
        self,
        tenant_id: UUID,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RealtimeSession]:
        """
        List sessions for a tenant.

        Args:
            tenant_id: Tenant UUID
            status: Optional status filter
            limit: Max results
            offset: Pagination offset

        Returns:
            List of sessions
        """
        filters = {"tenant_id": tenant_id}
        if status:
            filters["status"] = status

        sessions = RealtimeSession.objects.filter(**filters).order_by("-created_at")
        return [s async for s in sessions[offset : offset + limit]]

    async def get_active_conversation(
        self,
        session_id: str,
    ) -> Optional[Conversation]:
        """
        Get the active conversation for a session.

        Args:
            session_id: Session ID

        Returns:
            Active Conversation
        """
        return (
            await Conversation.objects.filter(
                session_id=session_id,
            )
            .order_by("-created_at")
            .afirst()
        )

    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions updated
        """
        updated = await RealtimeSession.objects.filter(
            status=RealtimeSession.Status.ACTIVE,
            expires_at__lt=timezone.now(),
        ).aupdate(
            status=RealtimeSession.Status.EXPIRED,
            updated_at=timezone.now(),
        )

        if updated:
            logger.info(f"Expired {updated} realtime sessions")

        return updated


# Singleton instance
realtime_session_service = RealtimeSessionService()
