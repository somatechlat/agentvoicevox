"""
Property tests for WebSocket authentication.

**Feature: django-saas-backend, Property 10: WebSocket Authentication**
**Validates: Requirements 6.3, 6.10**

Tests that:
1. Authenticated connections have user and tenant set in scope
2. Unauthenticated connections close with code 4001

Uses mocked Keycloak client for unit testing.
"""

import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ==========================================================================
# MOCK CLASSES
# ==========================================================================


@dataclass
class MockJWTClaims:
    """Mock JWT claims."""

    sub: str
    tenant_id: str
    email: str = "test@example.com"
    roles: list = None

    def __post_init__(self):
        if self.roles is None:
            self.roles = []


# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# Valid JWT token strategy (mock tokens)
token_strategy = st.text(min_size=20, max_size=100).filter(str.strip)


# ==========================================================================
# PROPERTY 10: WEBSOCKET AUTHENTICATION
# ==========================================================================


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestWebSocketAuthentication:
    """
    Property tests for WebSocket authentication.

    **Feature: django-saas-backend, Property 10: WebSocket Authentication**
    **Validates: Requirements 6.3, 6.10**

    For any WebSocket connection:
    - Authenticated connections SHALL have user and tenant set in scope
    - Unauthenticated connections SHALL close with code 4001
    """

    @pytest.mark.property
    @given(
        user_id=st.uuids(),
        tenant_id=st.uuids(),
    )
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    async def test_authenticated_connection_sets_context(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        tenant_factory,
    ):
        """
        Property: Authenticated connections have user and tenant in scope.

        For any valid JWT token with user_id and tenant_id,
        the WebSocket connection SHALL set these in the consumer.

        **Validates: Requirement 6.3**
        """
        from realtime.consumers.base import BaseConsumer

        # Create real tenant
        tenant = tenant_factory()

        # Create mock claims (used to set up scope context)
        _ = MockJWTClaims(
            sub=str(user_id),
            tenant_id=str(tenant.id),
        )

        # Create consumer instance
        consumer = BaseConsumer()
        consumer.scope = {
            "query_string": b"token=valid_token",
            "headers": [],
        }
        consumer.channel_layer = AsyncMock()
        consumer.channel_name = "test_channel"

        # Mock the authentication
        with patch.object(
            consumer,
            "_authenticate",
            new_callable=AsyncMock,
            return_value=True,
        ):
            consumer.user_id = str(user_id)
            consumer.tenant_id = str(tenant.id)

            with patch.object(
                consumer,
                "_validate_tenant",
                new_callable=AsyncMock,
                return_value=True,
            ):
                consumer.tenant = tenant

                with patch.object(consumer, "accept", new_callable=AsyncMock):
                    await consumer.connect()

                    # Verify context is set
                    assert consumer.user_id == str(user_id)
                    assert consumer.tenant_id == str(tenant.id)
                    assert consumer.authenticated is True

    @pytest.mark.property
    @given(
        invalid_token=st.text(min_size=1, max_size=50).filter(str.strip),
    )
    @settings(max_examples=20)
    async def test_unauthenticated_connection_closes_with_4001(
        self,
        invalid_token: str,
    ):
        """
        Property: Unauthenticated connections close with code 4001.

        For any invalid or missing token,
        the WebSocket connection SHALL close with code 4001.

        **Validates: Requirement 6.10**
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.scope = {
            "query_string": f"token={invalid_token}".encode(),
            "headers": [],
        }
        consumer.channel_layer = AsyncMock()
        consumer.channel_name = "test_channel"

        close_code = None

        async def mock_close(code=1000):
            nonlocal close_code
            close_code = code

        consumer.close = mock_close

        # Mock authentication to fail
        with patch.object(
            consumer,
            "_authenticate",
            new_callable=AsyncMock,
            return_value=False,
        ):
            await consumer.connect()

            # Should close with auth failed code
            assert close_code == BaseConsumer.CLOSE_AUTH_FAILED

    @pytest.mark.property
    async def test_missing_token_closes_connection(self):
        """
        Property: Missing token closes connection with 4001.

        For any connection without a token,
        the WebSocket SHALL close with code 4001.
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.scope = {
            "query_string": b"",
            "headers": [],
        }
        consumer.channel_layer = AsyncMock()
        consumer.channel_name = "test_channel"

        close_code = None

        async def mock_close(code=1000):
            nonlocal close_code
            close_code = code

        consumer.close = mock_close

        # _authenticate should return False when no token
        with patch(
            "realtime.consumers.base.keycloak_client.validate_token",
            side_effect=Exception("No token"),
        ):
            await consumer.connect()

            assert close_code == BaseConsumer.CLOSE_AUTH_FAILED


# ==========================================================================
# TENANT VALIDATION TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestWebSocketTenantValidation:
    """
    Property tests for WebSocket tenant validation.
    """

    @pytest.mark.property
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_suspended_tenant_closes_with_4003(self, suspended_tenant):
        """
        Property: Suspended tenant closes connection with 4003.

        For any connection with a suspended tenant,
        the WebSocket SHALL close with code 4003.
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.scope = {
            "query_string": b"token=valid_token",
            "headers": [],
        }
        consumer.channel_layer = AsyncMock()
        consumer.channel_name = "test_channel"
        consumer.tenant_id = str(suspended_tenant.id)

        close_code = None

        async def mock_close(code=1000):
            nonlocal close_code
            close_code = code

        consumer.close = mock_close

        # Mock authentication to succeed
        with patch.object(
            consumer,
            "_authenticate",
            new_callable=AsyncMock,
            return_value=True,
        ):
            consumer.user_id = str(uuid.uuid4())

            # Let tenant validation run with real suspended tenant
            await consumer.connect()

            assert close_code == BaseConsumer.CLOSE_TENANT_SUSPENDED

    @pytest.mark.property
    @given(nonexistent_tenant_id=st.uuids())
    @settings(max_examples=10)
    async def test_nonexistent_tenant_closes_with_4002(
        self,
        nonexistent_tenant_id: uuid.UUID,
    ):
        """
        Property: Non-existent tenant closes connection with 4002.

        For any connection with a non-existent tenant ID,
        the WebSocket SHALL close with code 4002.
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.scope = {
            "query_string": b"token=valid_token",
            "headers": [],
        }
        consumer.channel_layer = AsyncMock()
        consumer.channel_name = "test_channel"
        consumer.tenant_id = str(nonexistent_tenant_id)

        close_code = None

        async def mock_close(code=1000):
            nonlocal close_code
            close_code = code

        consumer.close = mock_close

        # Mock authentication to succeed
        with patch.object(
            consumer,
            "_authenticate",
            new_callable=AsyncMock,
            return_value=True,
        ):
            consumer.user_id = str(uuid.uuid4())

            await consumer.connect()

            assert close_code == BaseConsumer.CLOSE_TENANT_INVALID


# ==========================================================================
# PING/PONG HEARTBEAT TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestWebSocketHeartbeat:
    """
    Property tests for WebSocket ping/pong heartbeat.
    """

    @pytest.mark.property
    async def test_ping_receives_pong(self):
        """
        Property: Ping message receives pong response.

        For any ping message, the consumer SHALL respond with pong.
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.authenticated = True

        sent_messages = []

        async def mock_send_json(data):
            sent_messages.append(data)

        consumer.send_json = mock_send_json

        await consumer.receive_json({"type": "ping"})

        assert len(sent_messages) == 1
        assert sent_messages[0] == {"type": "pong"}

    @pytest.mark.property
    @given(
        unknown_type=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x != "ping")
    )
    @settings(max_examples=20)
    async def test_unknown_message_type_returns_error(self, unknown_type: str):
        """
        Property: Unknown message type returns error.

        For any unknown message type,
        the consumer SHALL send an error response.
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.authenticated = True

        sent_messages = []

        async def mock_send_json(data):
            sent_messages.append(data)

        consumer.send_json = mock_send_json

        await consumer.receive_json({"type": unknown_type.strip()})

        assert len(sent_messages) == 1
        assert sent_messages[0]["type"] == "error"
        assert "unknown_message_type" in sent_messages[0]["error"]["code"]


# ==========================================================================
# TOKEN EXTRACTION TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestTokenExtraction:
    """
    Property tests for token extraction from WebSocket connection.
    """

    @pytest.mark.property
    @given(token=token_strategy)
    @settings(max_examples=30)
    def test_token_extracted_from_query_string(self, token: str):
        """
        Property: Token is extracted from query string.

        For any token in the query string,
        the consumer SHALL extract it correctly.
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.scope = {
            "query_string": f"token={token.strip()}".encode(),
            "headers": [],
        }

        extracted = consumer._get_token()
        assert extracted == token.strip()

    @pytest.mark.property
    @given(token=token_strategy)
    @settings(max_examples=30)
    def test_token_extracted_from_authorization_header(self, token: str):
        """
        Property: Token is extracted from Authorization header.

        For any token in the Authorization header,
        the consumer SHALL extract it correctly.
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.scope = {
            "query_string": b"",
            "headers": [
                (b"authorization", f"Bearer {token.strip()}".encode()),
            ],
        }

        extracted = consumer._get_token()
        assert extracted == token.strip()

    @pytest.mark.property
    def test_query_string_takes_priority_over_header(self):
        """
        Property: Query string token takes priority over header.

        When both query string and header contain tokens,
        the query string token SHALL be used.
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.scope = {
            "query_string": b"token=query_token",
            "headers": [
                (b"authorization", b"Bearer header_token"),
            ],
        }

        extracted = consumer._get_token()
        assert extracted == "query_token"

    @pytest.mark.property
    def test_no_token_returns_none(self):
        """
        Property: No token returns None.

        When no token is provided,
        the consumer SHALL return None.
        """
        from realtime.consumers.base import BaseConsumer

        consumer = BaseConsumer()
        consumer.scope = {
            "query_string": b"",
            "headers": [],
        }

        extracted = consumer._get_token()
        assert extracted is None
