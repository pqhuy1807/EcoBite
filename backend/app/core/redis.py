"""Async Redis client & distributed-lock helper (Guardrail #4 support).

Redis is optional infrastructure: when it is unreachable the lock helper
degrades gracefully and the caller must fall back to the database-level
atomic update (e.g. `dish_repo.atomic_decrement_quantity`), which remains
the ultimate correctness backstop against over-selling.
"""

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from inspect import isawaitable

import redis.asyncio as redis_asyncio
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lua release script: delete the key only when the caller still owns it, so a
# lock that expired and was re-acquired by another worker is never removed by
# the previous owner (safe release = compare-and-delete in one atomic step).
_RELEASE_LOCK_LUA = (
    'if redis.call("get", KEYS[1]) == ARGV[1] then '
    'return redis.call("del", KEYS[1]) else return 0 end'
)

# Lazily-created shared client (see `get_redis`).
_redis_client: redis_asyncio.Redis | None = None


def get_redis() -> redis_asyncio.Redis:
    """Return the shared async Redis client, creating it on first use.

    The URL comes from `settings.REDIS_URL` (env-driven, never hardcoded).
    The client is lazy: no connection is made until the first command.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis_asyncio.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT_SECONDS,
        )
    return _redis_client


async def close_redis() -> None:
    """Dispose the shared client (wire this into app shutdown when used)."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


@asynccontextmanager
async def distributed_lock(
    key: str,
    *,
    client: redis_asyncio.Redis | None = None,
    timeout_seconds: int | None = None,
) -> AsyncIterator[bool]:
    """Hold a single-instance Redis distributed lock for the enclosed block.

    Acquisition runs `SET key <random-token> NX EX <ttl>`; release executes the
    compare-and-delete Lua script so only the current owner can remove the key.
    The TTL guarantees eventual release even if the holder crashes.

    Args:
        key: Lock name, e.g. `lock:dish:{dish_id}`.
        client: Optional injected client (tests); defaults to the shared one.
        timeout_seconds: TTL of the lock; defaults to `REDIS_LOCK_TIMEOUT_SECONDS`.

    Yields:
        True when the lock is held. False when another worker holds the key or
        Redis is unreachable — callers must then rely on the database-level
        atomic update as the correctness backstop (degraded, not broken).
    """
    redis_client = client if client is not None else get_redis()
    lock_ttl = (
        timeout_seconds if timeout_seconds is not None else settings.REDIS_LOCK_TIMEOUT_SECONDS
    )
    owner_token = uuid.uuid4().hex

    acquired = False
    try:
        acquired = bool(await redis_client.set(key, owner_token, nx=True, ex=lock_ttl))
    except RedisError as exc:
        # Degraded mode: keep serving with the DB atomic update as the backstop.
        logger.warning("Redis unavailable for lock %s (%s); using DB-only guard", key, exc)

    try:
        yield acquired
    finally:
        if acquired:
            try:
                release = redis_client.eval(_RELEASE_LOCK_LUA, 1, key, owner_token)
                # redis-py types commands as `Awaitable | value` (sync/async dual
                # stubs) — guard with isawaitable so both real mypy and runtime
                # stay happy on the asyncio client, where it is always a coroutine.
                if isawaitable(release):
                    await release
            except RedisError as exc:
                # The TTL will expire the orphaned lock, so this is safe to log.
                logger.warning("Failed to release lock %s (%s); TTL will expire it", key, exc)
