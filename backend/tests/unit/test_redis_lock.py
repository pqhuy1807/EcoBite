"""Unit tests for the Redis distributed-lock helper (app.core.redis)."""

from collections.abc import AsyncIterator

import pytest
from redis.exceptions import RedisError

from app.core.redis import close_redis, distributed_lock, get_redis


class FakeRedis:
    """Minimal async Redis stub covering the surface used by `distributed_lock`."""

    def __init__(self, *, available: bool = True) -> None:
        self.store: dict[str, str] = {}
        self.available = available
        self.release_calls: list[str] = []

    async def set(
        self, name: str, value: str, nx: bool = False, ex: int | None = None
    ) -> bool | None:
        """Mirror `SET key value NX EX ttl` semantics."""
        if not self.available:
            raise RedisError("connection refused")
        if nx and name in self.store:
            return None
        self.store[name] = value
        return True

    async def eval(self, script: str, numkeys: int, *args: str) -> int:
        """Mirror the compare-and-delete Lua script used for safe release."""
        key, token = args[0], args[1]
        if self.store.get(key) == token:
            self.release_calls.append(key)
            del self.store[key]
            return 1
        return 0


@pytest.fixture(autouse=True)
async def _reset_redis_singleton() -> AsyncIterator[None]:
    """Mỗi test dùng client singleton sạch và dọn dẹp sau khi test kết thúc."""
    await close_redis()
    yield
    await close_redis()


async def test_lock_acquires_and_releases_ownership() -> None:
    """Giữ khóa thành công phải ghi token và xóa đúng khóa của chủ sở hữu."""
    fake = FakeRedis()
    async with distributed_lock("lock:dish:1", client=fake, timeout_seconds=5) as acquired:
        assert acquired is True
        assert fake.store["lock:dish:1"]
    assert "lock:dish:1" not in fake.store
    assert fake.release_calls == ["lock:dish:1"]


async def test_lock_yields_false_when_key_already_held() -> None:
    """Khóa đang bị worker khác giữ phải trả False và không tự ý xóa khóa."""
    fake = FakeRedis()
    fake.store["lock:dish:1"] = "another-owner"
    async with distributed_lock("lock:dish:1", client=fake) as acquired:
        assert acquired is False
    assert fake.release_calls == []


async def test_lock_degrades_gracefully_when_redis_unreachable() -> None:
    """Redis chết phải degrade an toàn (yield False) thay vì làm sập request."""
    fake = FakeRedis(available=False)
    async with distributed_lock("lock:dish:1", client=fake) as acquired:
        assert acquired is False


class BrokenEvalRedis(FakeRedis):
    """Fake client whose release step always fails (simulating network reset)."""

    async def eval(self, script: str, numkeys: int, *args: str) -> int:
        raise RedisError("network reset")


async def test_lock_swallows_release_failures() -> None:
    """Lỗi khi nhả khóa không được lan ra ngoài; TTL sẽ tự hết hạn khóa."""
    fake = BrokenEvalRedis()
    async with distributed_lock("lock:dish:1", client=fake) as acquired:
        assert acquired is True
    assert fake.store["lock:dish:1"]  # khóa vẫn còn, chờ TTL tự xóa


async def test_get_redis_is_lazy_singleton() -> None:
    """Client Redis phải được tạo lười và dùng chung (singleton)."""
    first = get_redis()
    assert get_redis() is first
