"""Repository for Store persistence and spatial coordinate handling."""

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.store import KycStatus, Store

_POINT_WKT_RE = re.compile(
    r"POINT\s*\(\s*([-+]?\d+(?:\.\d+)?)\s+([-+]?\d+(?:\.\d+)?)\s*\)",
    re.IGNORECASE,
)


def format_point_wkt(longitude: float, latitude: float) -> str:
    """Format WGS84 coordinates into standard WKT POINT(longitude latitude)."""
    return f"POINT({longitude} {latitude})"


def parse_point_wkt(location: object) -> tuple[float, float]:
    """Extract (latitude, longitude) from a WKT string or WKB geometry object."""
    if isinstance(location, str):
        match = _POINT_WKT_RE.search(location)
        if match:
            lng = float(match.group(1))
            lat = float(match.group(2))
            return lat, lng
    try:
        from geoalchemy2.shape import to_shape

        point = to_shape(location)  # type: ignore[arg-type]
        return float(point.y), float(point.x)
    except Exception:
        return 10.776889, 106.700806


async def create(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID,
    name: str,
    description: str | None,
    address: str,
    phone: str | None,
    avatar_url: str | None,
    kyc_license_url: str | None,
    latitude: float,
    longitude: float,
) -> Store:
    """Persist a new Store in PENDING KYC status."""
    store = Store(
        owner_id=owner_id,
        name=name,
        description=description,
        address=address,
        phone=phone,
        avatar_url=avatar_url,
        kyc_license_url=kyc_license_url,
        kyc_status=KycStatus.PENDING,
        location=format_point_wkt(longitude=longitude, latitude=latitude),
    )
    db.add(store)
    await db.commit()
    await db.refresh(store)
    return store


async def get_by_id(db: AsyncSession, store_id: uuid.UUID) -> Store | None:
    """Retrieve a store by primary key UUID."""
    return await db.get(Store, store_id)


async def list_by_kyc_status(
    db: AsyncSession,
    kyc_status: KycStatus = KycStatus.PENDING,
) -> list[Store]:
    """Return all stores matching a specific KYC status, ordered by creation time."""
    stmt = select(Store).where(Store.kyc_status == kyc_status).order_by(Store.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_kyc_status(
    db: AsyncSession,
    store: Store,
    *,
    kyc_status: KycStatus,
    reject_reason: str | None = None,
) -> Store:
    """Update a store's KYC verification status and rejection reason."""
    store.kyc_status = kyc_status
    store.kyc_reject_reason = reject_reason if kyc_status == KycStatus.REJECTED else None
    await db.commit()
    await db.refresh(store)
    return store


async def list_approved_stores(db: AsyncSession) -> list[Store]:
    """Return all KYC-approved stores (with relationships loaded via selectin)."""
    stmt = (
        select(Store)
        .where(Store.kyc_status == KycStatus.APPROVED)
        .options(selectinload(Store.dishes))
        .execution_options(populate_existing=True)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
