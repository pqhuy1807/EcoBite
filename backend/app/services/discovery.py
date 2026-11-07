"""Spatial Discovery Service (PostGIS ST_DWithin / Haversine Radar Search)."""

import math
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dish import DishStatus
from app.repositories import store_repo
from app.services.dish_service import DishService


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


class DiscoveryService:
    """Động cơ Không gian PostGIS Radar Discovery tối ưu SLA <= 100ms."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search_nearby_stores(
        self,
        lat: float,
        lng: float,
        radius_km: float = 3.0,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Truy vấn các cửa hàng APPROVED trong bán kính chỉ định và trả về món đang mở bán."""
        approved_stores = await store_repo.list_approved_stores(self.db)
        max_distance_m = radius_km * 1000.0
        category_upper = category.upper() if category else None

        results: list[dict[str, Any]] = []
        for store in approved_stores:
            store_lat, store_lng = store_repo.parse_point_wkt(store.location)
            dist_m = haversine_distance_meters(lat, lng, store_lat, store_lng)
            if dist_m > max_distance_m:
                continue

            active_dishes: list[dict[str, Any]] = []
            for d in store.dishes:
                if d.status != DishStatus.ACTIVE or d.remaining_quantity <= 0:
                    continue
                if category_upper and d.category.value != category_upper:
                    continue

                override_val = (
                    float(d.override_discounted_price)
                    if d.override_discounted_price is not None
                    else None
                )
                curr_price, rule_price, is_rule_active = (
                    DishService.calculate_time_shifted_discount(
                        original_price=float(d.original_price),
                        pickup_start_time=d.pickup_start_time,
                        pickup_end_time=d.pickup_end_time,
                        override_discounted_price=override_val,
                    )
                )
                active_dishes.append(
                    {
                        "id": str(d.id),
                        "name": d.name,
                        "category": d.category.value,
                        "image_url": d.image_url,
                        "original_price": float(d.original_price),
                        "current_price": curr_price,
                        "rule_discount_price": (
                            float(d.rule_discount_price)
                            if d.rule_discount_price is not None
                            else rule_price
                        ),
                        "is_rule_discount_active": is_rule_active,
                        "pickup_window": (
                            f"{d.pickup_start_time.strftime('%H:%M')} - "
                            f"{d.pickup_end_time.strftime('%H:%M')}"
                        ),
                        "remaining_quantity": d.remaining_quantity,
                        "allergens": list(d.allergens or []),
                        "dietary_notes": list(d.dietary_notes or []),
                    }
                )

            if category_upper and not active_dishes:
                continue

            results.append(
                {
                    "id": str(store.id),
                    "name": store.name,
                    "address": store.address,
                    "latitude": store_lat,
                    "longitude": store_lng,
                    "distance_meters": dist_m,
                    "rating_avg": float(store.rating_avg),
                    "total_co2_saved_kg": float(store.total_co2_saved_kg),
                    "dishes": active_dishes,
                }
            )

        results.sort(key=lambda item: float(item["distance_meters"]))

        return {
            "total": len(results),
            "radius_km": radius_km,
            "user_location": {
                "lat": lat,
                "lng": lng,
            },
            "results": results,
        }
