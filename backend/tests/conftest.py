"""Shared pytest fixtures: SQLite in-memory database, mocked session, HTTP client."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Importing the model modules registers every ORM class on `Base.metadata`
# so create_all() can build the full test schema.
import app.models as _models  # noqa: F401
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """Fresh in-memory database per test; StaticPool keeps the same connection shared."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """An active session bound to the test database, wrapped by get_db override."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Swap the production session for the test one inside app dependencies."""

    async def _override() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def client(override_get_db) -> AsyncIterator[AsyncClient]:
    """HTTP client talking directly to the FastAPI ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as async_client:
        yield async_client


@pytest.fixture
async def store_partner(db_session: AsyncSession) -> dict[str, object]:
    """Persist an approved merchant account and provide its authenticated API headers."""
    user = User(
        email="merchant@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Merchant",
        role=UserRole.STORE_PARTNER,
    )
    db_session.add(user)
    await db_session.flush()
    store = Store(
        owner_id=user.id,
        name="Test Store",
        address="123 Test Street",
        location="POINT(106.7 10.77)",
        kyc_status=KycStatus.APPROVED,
    )
    db_session.add(store)
    await db_session.commit()
    return {
        "user": user,
        "store": store,
        "headers": {"Authorization": f"Bearer {create_access_token(user.id)}"},
    }


@pytest.fixture
async def other_store_partner(db_session: AsyncSession) -> dict[str, object]:
    """Persist a second merchant to exercise cross-store authorization."""
    user = User(
        email="other-merchant@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Other Merchant",
        role=UserRole.STORE_PARTNER,
    )
    db_session.add(user)
    await db_session.flush()
    store = Store(
        owner_id=user.id,
        name="Other Store",
        address="456 Test Street",
        location="POINT(106.8 10.8)",
        kyc_status=KycStatus.APPROVED,
    )
    db_session.add(store)
    await db_session.commit()
    return {
        "user": user,
        "store": store,
        "headers": {"Authorization": f"Bearer {create_access_token(user.id)}"},
    }
