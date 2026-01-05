"""
Async Redis client for workflow workers.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import redis.asyncio as aioredis
from django.conf import settings
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import ConnectionError, RedisError, TimeoutError

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client with connection pooling and reconnection."""

    def __init__(self) -> None:
        """Initializes the RedisClient, setting up internal state."""
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._connected = False
        self._reconnect_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establish connection to Redis with pooling."""
        if self._connected:
            return

        config = settings.REDIS_WORKER

        try:
            self._pool = ConnectionPool.from_url(
                config["URL"],
                max_connections=config["MAX_CONNECTIONS"],
                socket_timeout=config["SOCKET_TIMEOUT"],
                socket_connect_timeout=config["SOCKET_CONNECT_TIMEOUT"],
                retry_on_timeout=config["RETRY_ON_TIMEOUT"],
                health_check_interval=config["HEALTH_CHECK_INTERVAL"],
                decode_responses=True,
            )
            self._client = aioredis.Redis(connection_pool=self._pool)
            await self._client.ping()
            self._connected = True
            logger.info("Redis connection established", extra={"url": config["URL"]})

        except (ConnectionError, TimeoutError) as exc:
            logger.error("Failed to connect to Redis", extra={"error": str(exc)})
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        if self._client:
            await self._client.aclose()
            self._client = None

        if self._pool:
            await self._pool.disconnect()
            self._pool = None

        self._connected = False
        logger.info("Redis connection closed")

    @property
    def client(self) -> aioredis.Redis:
        """Return the underlying Redis client."""
        if not self._client or not self._connected:
            raise RuntimeError("Redis client not connected")
        return self._client

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except RedisError:
            return False

    def start_reconnect(self) -> None:
        """Start reconnect loop in background."""
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._connected = False
        self._reconnect_task = asyncio.create_task(self._reconnect_with_backoff())

    async def _reconnect_with_backoff(self) -> None:
        """Attempt to reconnect to Redis with exponential backoff."""
        backoff = 1.0
        max_backoff = 60.0

        while not self._connected:
            try:
                logger.info("Attempting Redis reconnection", extra={"backoff": backoff})
                await self.connect()
                logger.info("Redis reconnection successful")
                return
            except (ConnectionError, TimeoutError) as exc:
                logger.warning(
                    "Redis reconnection failed, retrying",
                    extra={"error": str(exc), "next_attempt_seconds": backoff},
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)

    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a channel."""
        try:
            return await self.client.publish(channel, message)
        except (ConnectionError, TimeoutError) as exc:
            logger.error("Redis PUBLISH failed", extra={"channel": channel, "error": str(exc)})
            self.start_reconnect()
            raise
