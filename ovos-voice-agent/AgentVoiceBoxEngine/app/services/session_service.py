"""Session management service backed by SQLAlchemy."""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, Optional

from ..models.session import ConversationItem, SessionModel
from ..observability.metrics import active_sessions, session_starts
from ..utils.database import session_scope

logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def create_session(
        self,
        session_id: str,
        project_id: Optional[str],
        session_payload: Dict[str, Any],
        expires_at: Optional[dt.datetime],
        persona: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> SessionModel:
        """Create a new voice session.

        Args:
            session_id: Unique session identifier
            project_id: Project ID for grouping
            session_payload: Session configuration
            expires_at: Session expiration time
            persona: Persona configuration
            tenant_id: Tenant ID for multi-tenant isolation (REQUIRED for isolation)

        Returns:
            Created SessionModel
        """
        import uuid as uuid_module

        session_starts.inc()
        with session_scope(self._session_factory) as session:
            model = SessionModel(
                id=session_id,
                tenant_id=uuid_module.UUID(tenant_id) if tenant_id else None,
                project_id=project_id,
                persona=persona or {},
                session_config=session_payload,
                model=session_payload.get("model"),
                instructions=session_payload.get("instructions"),
                output_modalities=session_payload.get("output_modalities"),
                tools=session_payload.get("tools"),
                tool_choice=session_payload.get("tool_choice"),
                audio_config=session_payload.get("audio"),
                max_output_tokens=(
                    str(session_payload.get("max_output_tokens"))
                    if session_payload.get("max_output_tokens") is not None
                    else None
                ),
                expires_at=expires_at,
                status="active",
                created_at=dt.datetime.utcnow(),
            )
            session.add(model)
            session.commit()
        active_sessions.inc()
        logger.info(
            "Session created",
            extra={"session_id": session_id, "tenant_id": tenant_id},
        )
        return model

    def close_session(self, session_id: str) -> None:
        with session_scope(self._session_factory) as session:
            model = session.get(SessionModel, session_id)
            if not model:
                logger.warning(
                    "Attempted to close missing session", extra={"session_id": session_id}
                )
                return
            model.status = "closed"
            model.closed_at = dt.datetime.utcnow()
            session.add(model)
            session.commit()
        active_sessions.dec()
        logger.info("Session closed", extra={"session_id": session_id})

    def append_conversation_item(
        self,
        session_id: str,
        item: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> ConversationItem:
        """Append a conversation item to a session.

        Args:
            session_id: Session ID
            item: Conversation item data
            tenant_id: Tenant ID for multi-tenant isolation

        Returns:
            Created ConversationItem
        """
        import uuid as uuid_module

        with session_scope(self._session_factory) as session:
            record = ConversationItem(
                session_id=session_id,
                tenant_id=uuid_module.UUID(tenant_id) if tenant_id else None,
                role=item.get("role"),
                content=item,
                created_at=dt.datetime.utcnow(),
            )
            session.add(record)
            session.commit()
            return record

    def get_session(self, session_id: str) -> Optional[SessionModel]:
        with session_scope(self._session_factory) as session:
            return session.get(SessionModel, session_id)

    def list_sessions(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SessionModel]:
        """List sessions for a tenant with filtering.

        Args:
            tenant_id: Tenant ID for isolation (REQUIRED)
            status: Filter by status (active, closed)
            project_id: Filter by project
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of sessions belonging to the tenant
        """
        import uuid as uuid_module

        with session_scope(self._session_factory) as session:
            query = session.query(SessionModel).filter(
                SessionModel.tenant_id == uuid_module.UUID(tenant_id)
            )

            if status:
                query = query.filter(SessionModel.status == status)
            if project_id:
                query = query.filter(SessionModel.project_id == project_id)

            query = query.order_by(SessionModel.created_at.desc())
            query = query.limit(limit).offset(offset)

            return query.all()

    def get_session_for_tenant(
        self,
        session_id: str,
        tenant_id: str,
    ) -> Optional[SessionModel]:
        """Get a session with tenant verification.

        Args:
            session_id: Session ID
            tenant_id: Tenant ID for isolation (REQUIRED)

        Returns:
            Session if found and belongs to tenant, None otherwise
        """
        import uuid as uuid_module

        with session_scope(self._session_factory) as session:
            return (
                session.query(SessionModel)
                .filter(SessionModel.id == session_id)
                .filter(SessionModel.tenant_id == uuid_module.UUID(tenant_id))
                .first()
            )

    def close_session_for_tenant(
        self,
        session_id: str,
        tenant_id: str,
    ) -> bool:
        """Close a session with tenant verification.

        Args:
            session_id: Session ID
            tenant_id: Tenant ID for isolation (REQUIRED)

        Returns:
            True if session was closed, False if not found
        """
        import uuid as uuid_module

        with session_scope(self._session_factory) as session:
            model = (
                session.query(SessionModel)
                .filter(SessionModel.id == session_id)
                .filter(SessionModel.tenant_id == uuid_module.UUID(tenant_id))
                .first()
            )

            if not model:
                logger.warning(
                    "Session not found for tenant",
                    extra={"session_id": session_id, "tenant_id": tenant_id},
                )
                return False

            model.status = "closed"
            model.closed_at = dt.datetime.utcnow()
            session.add(model)
            session.commit()

        active_sessions.dec()
        logger.info(
            "Session closed",
            extra={"session_id": session_id, "tenant_id": tenant_id},
        )
        return True

    def update_session(
        self,
        session_id: str,
        *,
        session_updates: Optional[Dict[str, Any]] = None,
        persona: Optional[Dict[str, Any]] = None,
        status: Optional[str] = None,
    ) -> Optional[SessionModel]:
        with session_scope(self._session_factory) as session:
            model = session.get(SessionModel, session_id)
            if not model:
                logger.warning(
                    "Attempted to update missing session", extra={"session_id": session_id}
                )
                return None

            if session_updates:
                merged = dict(model.session_config or {})
                merged.update(session_updates)
                model.session_config = merged

                if "model" in session_updates:
                    model.model = session_updates["model"]
                if "instructions" in session_updates:
                    model.instructions = session_updates["instructions"]
                if "output_modalities" in session_updates:
                    model.output_modalities = session_updates["output_modalities"]
                if "tools" in session_updates:
                    model.tools = session_updates["tools"]
                if "tool_choice" in session_updates:
                    model.tool_choice = session_updates["tool_choice"]
                if "audio" in session_updates:
                    model.audio_config = session_updates["audio"]
                if "max_output_tokens" in session_updates:
                    max_value = session_updates["max_output_tokens"]
                    if isinstance(max_value, str) and max_value.lower() == "inf":
                        model.max_output_tokens = "inf"
                    elif max_value is None:
                        model.max_output_tokens = None
                    else:
                        model.max_output_tokens = str(max_value)

            if persona is not None:
                model.persona = persona

            if status is not None:
                model.status = status

            session.add(model)
            session.commit()
            session.refresh(model)
            logger.info("Session updated", extra={"session_id": session_id})
            return model


__all__ = ["SessionService"]
