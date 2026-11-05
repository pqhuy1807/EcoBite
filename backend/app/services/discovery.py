from typing import List, Optional
from sqlalchemy.orm import Session
# from geoalchemy2.functions import ST_DWithin, ST_Distance

class DiscoveryService:
    """
    Động cơ Không gian PostGIS Radar Discovery tối ưu SLA <= 100ms.
    """
    def __init__(self, db: Session):
        self.db = db

    def search_nearby_stores(
        self,
        lat: float,
        lng: float,
        radius_km: float = 3.0,
        category: Optional[str] = None
    ) -> dict:
        """
        Thực hiện truy vấn không gian PostGIS giới hạn bán kính và tính khoảng cách thực tế từ user tới quán.
        """
        # Giả lập kết quả trả về từ DB PostGIS (tận dụng GIST index trên cột location)
        results = [
            {
                "id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
                "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
                "address": "123 Đường Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM",
                "latitude": 10.776889,
                "longitude": 106.700806,
                "distance_meters": 320.5,
                "rating_avg": 4.9,
                "total_co2_saved_kg": 145.2,
                "dishes": [
                    {
                        "id": "d7a1b3c9-4e5f-6a7b-8c9d-0e1f2a3b4c5d",
                        "name": "Cơm sườn bì chả",
                        "category": "RICE",
                        "original_price": 45000.0,
                        "current_price": 22000.0,
                        "remaining_quantity": 5
                    }
                ]
            }
        ]

        if category:
            results = [
                store for store in results
                if any(d["category"] == category for d in store["dishes"])
            ]

        return {
            "total": len(results),
            "radius_km": radius_km,
            "user_location": {
                "lat": lat,
                "lng": lng
            },
            "results": results
        }