"""Repository for Store persistence and spatial coordinate handling."""

import math
import re
import uuid

from geoalchemy2 import Geography
from geoalchemy2.functions import ST_Distance, ST_DWithin
from sqlalchemy import cast, func, select
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


def haversine_distance_meters(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
) -> float:
    """Compute exact spherical geodesic distance in meters between two WGS84 points."""
    earth_radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(earth_radius_m * c, 1)


async def create_store(
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


async def get_store_by_id(db: AsyncSession, store_id: uuid.UUID) -> Store | None:
    """Retrieve a store by primary key UUID, or None when missing."""
    return await db.get(Store, store_id)


async def get_store_by_owner_id(db: AsyncSession, owner_id: uuid.UUID) -> Store | None:
    """Retrieve a store owned by owner_id, or None when missing."""
    stmt = select(Store).where(Store.owner_id == owner_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_pending_stores(db: AsyncSession) -> list[Store]:
    """Return all stores waiting for KYC review (PENDING), newest first."""
    stmt = (
        select(Store).where(Store.kyc_status == KycStatus.PENDING).order_by(Store.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_store_status(
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


async def list_stores(db: AsyncSession) -> list[Store]:
    """Return all stores regardless of KYC status (with dishes eagerly loaded)."""
    stmt = (
        select(Store).options(selectinload(Store.dishes)).execution_options(populate_existing=True)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_nearby_stores(
    db: AsyncSession,
    lat: float,
    lng: float,
    radius_km: float = 3.0,
) -> list[tuple[Store, float]]:
    """List stores within radius_km, returning pairs of (Store, distance_meters).

    Uses PostGIS ST_DWithin and ST_Distance on PostgreSQL (Guardrail #2) for sub-100ms spatial
    queries leveraging the spatial GIST index.
    Falls back gracefully to spherical Haversine computation on SQLite (for test suites).
    """
    max_distance_m = radius_km * 1000.0
    bind = db.bind or getattr(db, "_bind", None)
    dialect_name = bind.dialect.name if bind is not None else ""

    if dialect_name == "postgresql":
        user_geo = cast(
            func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326),
            Geography,
        )
        store_geo = cast(Store.location, Geography)
        dist_expr = ST_Distance(store_geo, user_geo).label("distance_meters")

        stmt = (
            select(Store, dist_expr)
            .where(
                ST_DWithin(store_geo, user_geo, max_distance_m),
            )
            .options(selectinload(Store.dishes))
            .order_by(dist_expr)
            .execution_options(populate_existing=True)
        )
        result = await db.execute(stmt)
        return [(row[0], float(row[1])) for row in result.all()]

    # SQLite fallback for in-memory integration testing
    stores = await list_stores(db)
    nearby_list: list[tuple[Store, float]] = []
    for store in stores:
        store_lat, store_lng = parse_point_wkt(store.location)
        dist = haversine_distance_meters(lat, lng, store_lat, store_lng)
        if dist <= max_distance_m:
            nearby_list.append((store, dist))
    nearby_list.sort(key=lambda item: item[1])
    return nearby_list
