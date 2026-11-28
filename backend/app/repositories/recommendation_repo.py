"""Repository for recommendation candidate selection (Layer 1).

Implements the SQL hard safety invariant (AGENTS.md Guardrail #7):
candidate dishes are filtered at the data layer so that no dish containing
an excluded allergen can leak into the recommendation engine.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from geoalchemy2 import Geography
from geoalchemy2.functions import ST_Distance, ST_DWithin
from sqlalchemy import and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dish import Dish, DishStatus
from app.models.store import Store
from app.repositories.store_repo import haversine_distance_meters, parse_point_wkt
from app.services.allergen_filter_service import AllergenHardFilterService

VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


async def list_candidate_dishes(
    db: AsyncSession,
    *,
    lat: float,
    lng: float,
    radius_km: float,
    excluded_allergens: list[str],
    limit: int,
) -> list[tuple[Dish, float, Store]]:
    """Layer 1 — SQL candidate selection with hard safety filters.

    Filters applied directly in SQL:
      * ``Dish.status == ACTIVE``
      * ``remaining_quantity > 0`` (anti-over-selling)
      * ``pickup_end_time >= now`` (Asia/Ho_Chi_Minh / UTC+7, consistent with DB)
      * Store within ``radius_km`` via PostGIS ``ST_DWithin`` on PostgreSQL,
        with a spherical Haversine fallback on SQLite for in-memory tests.

    After the SQL query returns, the Allergen Hard Filter
    (``AllergenHardFilterService``) is applied deterministically to the
    result set — this is the project's established Guardrail #7 pattern and
    guarantees 0 % of dishes containing an excluded allergen leak through.
    """
    max_distance_m = radius_km * 1000.0
    bind = db.bind or getattr(db, "_bind", None)
    dialect_name = bind.dialect.name if bind is not None else ""

    now = datetime.now(VIETNAM_TZ).time()

    base_where = and_(
        Dish.status == DishStatus.ACTIVE,
        Dish.remaining_quantity > 0,
        Dish.pickup_end_time >= now,
    )

    if dialect_name == "postgresql":
        user_geo = cast(func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326), Geography)
        store_geo = cast(Store.location, Geography)
        base_where = and_(base_where, ST_DWithin(store_geo, user_geo, max_distance_m))
        dist_expr = ST_Distance(store_geo, user_geo).label("distance_meters")
        stmt = (
            select(Dish, dist_expr, Store)
            .join(Store, Dish.store_id == Store.id)
            .where(base_where)
            .options(selectinload(Dish.store))
            .order_by(dist_expr)
        )
        result = await db.execute(stmt)
        rows = [(row[0], float(row[1]), row[2]) for row in result.all()]
    else:
        # SQLite fallback for in-memory test suites (no PostGIS available).
        stmt = (
            select(Dish, Store)
            .join(Store, Dish.store_id == Store.id)
            .where(base_where)
            .options(selectinload(Dish.store))
        )
        result = await db.execute(stmt)
        rows = []
        for dish, store in result.all():
            store_lat, store_lng = parse_point_wkt(store.location)
            dist = haversine_distance_meters(lat, lng, store_lat, store_lng)
            if dist <= max_distance_m:
                rows.append((dish, dist, store))
        rows.sort(key=lambda item: item[1])

    # Layer 1 hard allergen safety invariant (applied to SQL result set).
    rows = _apply_allergen_hard_filter(rows, excluded_allergens)

    return rows[:limit]


def _apply_allergen_hard_filter(
    rows: list[tuple[Dish, float, Store]],
    excluded_allergens: list[str],
) -> list[tuple[Dish, float, Store]]:
    """Drop any dish whose allergens intersect the user's exclusions.

    Runs the deterministic, case/accent-insensitive ``AllergenHardFilterService``
    over each candidate so the hard invariant holds regardless of SQL dialect.
    """
    if not excluded_allergens:
        return rows
    kept: list[tuple[Dish, float, Store]] = []
    for dish, dist_m, store in rows:
        dish_allergens = dish.allergens or []
        passes = AllergenHardFilterService.filter_dishes_by_allergens(
            [{"allergens": dish_allergens}],
            excluded_allergens,
        )
        if passes:
            kept.append((dish, dist_m, store))
    return kept
