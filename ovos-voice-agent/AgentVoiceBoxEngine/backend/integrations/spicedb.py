"""
SpiceDB integration client.

Provides fine-grained authorization via SpiceDB (Zanzibar-style).
"""
import logging
from dataclasses import dataclass
from typing import List, Optional

import grpc
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class Permission:
    """Permission check result."""

    allowed: bool
    resource_type: str
    resource_id: str
    relation: str
    subject_type: str
    subject_id: str


@dataclass
class Relationship:
    """SpiceDB relationship."""

    resource_type: str
    resource_id: str
    relation: str
    subject_type: str
    subject_id: str


class SpiceDBClient:
    """
    SpiceDB client for authorization.

    Handles:
    - Permission checks
    - Relationship management
    - Subject lookups
    """

    def __init__(self):
        """Initialize SpiceDB client from Django settings."""
        self.endpoint = settings.SPICEDB["ENDPOINT"]
        self.token = settings.SPICEDB["TOKEN"]
        self.insecure = settings.SPICEDB["INSECURE"]

        self._channel: Optional[grpc.Channel] = None
        self._stub = None

    def _get_channel(self) -> grpc.Channel:
        """Get or create gRPC channel."""
        if self._channel is None:
            if self.insecure:
                self._channel = grpc.insecure_channel(self.endpoint)
            else:
                credentials = grpc.ssl_channel_credentials()
                self._channel = grpc.secure_channel(self.endpoint, credentials)
        return self._channel

    def _get_metadata(self) -> List[tuple]:
        """Get gRPC metadata with auth token."""
        return [("authorization", f"Bearer {self.token}")]

    async def check_permission(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
        subject_id: str,
    ) -> Permission:
        """
        Check if a subject has a permission on a resource.

        Args:
            resource_type: Type of resource (e.g., "tenant", "project")
            resource_id: ID of the resource
            relation: Permission to check (e.g., "admin", "view")
            subject_type: Type of subject (e.g., "user")
            subject_id: ID of the subject

        Returns:
            Permission result
        """
        try:
            # Import SpiceDB protobuf types
            from authzed.api.v1 import (
                CheckPermissionRequest,
                CheckPermissionResponse,
                ObjectReference,
                PermissionsServiceStub,
                SubjectReference,
            )

            channel = self._get_channel()
            stub = PermissionsServiceStub(channel)

            request = CheckPermissionRequest(
                resource=ObjectReference(
                    object_type=resource_type,
                    object_id=resource_id,
                ),
                permission=relation,
                subject=SubjectReference(
                    object=ObjectReference(
                        object_type=subject_type,
                        object_id=subject_id,
                    ),
                ),
            )

            response = stub.CheckPermission(
                request,
                metadata=self._get_metadata(),
            )

            allowed = (
                response.permissionship
                == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
            )

            return Permission(
                allowed=allowed,
                resource_type=resource_type,
                resource_id=resource_id,
                relation=relation,
                subject_type=subject_type,
                subject_id=subject_id,
            )

        except grpc.RpcError as e:
            logger.error(f"SpiceDB check_permission error: {e}")
            # Fail closed - deny on error
            return Permission(
                allowed=False,
                resource_type=resource_type,
                resource_id=resource_id,
                relation=relation,
                subject_type=subject_type,
                subject_id=subject_id,
            )

    async def write_relationship(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        """
        Create a relationship in SpiceDB.

        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            relation: Relation to create
            subject_type: Type of subject
            subject_id: ID of the subject

        Returns:
            True if successful
        """
        try:
            from authzed.api.v1 import (
                ObjectReference,
                PermissionsServiceStub,
                Relationship,
                RelationshipUpdate,
                SubjectReference,
                WriteRelationshipsRequest,
            )

            channel = self._get_channel()
            stub = PermissionsServiceStub(channel)

            request = WriteRelationshipsRequest(
                updates=[
                    RelationshipUpdate(
                        operation=RelationshipUpdate.OPERATION_CREATE,
                        relationship=Relationship(
                            resource=ObjectReference(
                                object_type=resource_type,
                                object_id=resource_id,
                            ),
                            relation=relation,
                            subject=SubjectReference(
                                object=ObjectReference(
                                    object_type=subject_type,
                                    object_id=subject_id,
                                ),
                            ),
                        ),
                    ),
                ],
            )

            stub.WriteRelationships(
                request,
                metadata=self._get_metadata(),
            )

            return True

        except grpc.RpcError as e:
            logger.error(f"SpiceDB write_relationship error: {e}")
            return False

    async def delete_relationship(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        """
        Delete a relationship from SpiceDB.

        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            relation: Relation to delete
            subject_type: Type of subject
            subject_id: ID of the subject

        Returns:
            True if successful
        """
        try:
            from authzed.api.v1 import (
                ObjectReference,
                PermissionsServiceStub,
                Relationship,
                RelationshipUpdate,
                SubjectReference,
                WriteRelationshipsRequest,
            )

            channel = self._get_channel()
            stub = PermissionsServiceStub(channel)

            request = WriteRelationshipsRequest(
                updates=[
                    RelationshipUpdate(
                        operation=RelationshipUpdate.OPERATION_DELETE,
                        relationship=Relationship(
                            resource=ObjectReference(
                                object_type=resource_type,
                                object_id=resource_id,
                            ),
                            relation=relation,
                            subject=SubjectReference(
                                object=ObjectReference(
                                    object_type=subject_type,
                                    object_id=subject_id,
                                ),
                            ),
                        ),
                    ),
                ],
            )

            stub.WriteRelationships(
                request,
                metadata=self._get_metadata(),
            )

            return True

        except grpc.RpcError as e:
            logger.error(f"SpiceDB delete_relationship error: {e}")
            return False

    async def lookup_subjects(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
    ) -> List[str]:
        """
        Find all subjects with a relation to a resource.

        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
            relation: Relation to look up
            subject_type: Type of subjects to find

        Returns:
            List of subject IDs
        """
        try:
            from authzed.api.v1 import (
                LookupSubjectsRequest,
                ObjectReference,
                PermissionsServiceStub,
            )

            channel = self._get_channel()
            stub = PermissionsServiceStub(channel)

            request = LookupSubjectsRequest(
                resource=ObjectReference(
                    object_type=resource_type,
                    object_id=resource_id,
                ),
                permission=relation,
                subject_object_type=subject_type,
            )

            subjects = []
            for response in stub.LookupSubjects(
                request,
                metadata=self._get_metadata(),
            ):
                subjects.append(response.subject.subject_object_id)

            return subjects

        except grpc.RpcError as e:
            logger.error(f"SpiceDB lookup_subjects error: {e}")
            return []

    async def lookup_resources(
        self,
        resource_type: str,
        relation: str,
        subject_type: str,
        subject_id: str,
    ) -> List[str]:
        """
        Find all resources a subject has a relation to.

        Args:
            resource_type: Type of resources to find
            relation: Relation to look up
            subject_type: Type of subject
            subject_id: ID of the subject

        Returns:
            List of resource IDs
        """
        try:
            from authzed.api.v1 import (
                LookupResourcesRequest,
                ObjectReference,
                PermissionsServiceStub,
                SubjectReference,
            )

            channel = self._get_channel()
            stub = PermissionsServiceStub(channel)

            request = LookupResourcesRequest(
                resource_object_type=resource_type,
                permission=relation,
                subject=SubjectReference(
                    object=ObjectReference(
                        object_type=subject_type,
                        object_id=subject_id,
                    ),
                ),
            )

            resources = []
            for response in stub.LookupResources(
                request,
                metadata=self._get_metadata(),
            ):
                resources.append(response.resource_object_id)

            return resources

        except grpc.RpcError as e:
            logger.error(f"SpiceDB lookup_resources error: {e}")
            return []

    def close(self) -> None:
        """Close the gRPC channel."""
        if self._channel:
            self._channel.close()
            self._channel = None


# Singleton instance
spicedb_client = SpiceDBClient()
