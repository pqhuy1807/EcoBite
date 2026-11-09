"""Business logic for Store Onboarding & Admin KYC Verification."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import KycStatus, Store
from app.repositories import store_repo


def _serialize_store(store: Store) -> dict[str, Any]:
    """Serialize a Store ORM entity into an API dictionary representation."""
    lat, lng = store_repo.parse_point_wkt(store.location)
    return {
        "id": str(store.id),
        "owner_id": str(store.owner_id),
        "name": store.name,
        "description": store.description,
        "address": store.address,
        "latitude": lat,
        "longitude": lng,
        "phone": store.phone,
        "avatar_url": store.avatar_url,
        "kyc_license_url": store.kyc_license_url,
        "kyc_status": store.kyc_status.value,
        "kyc_reject_reason": store.kyc_reject_reason,
        "rating_avg": float(store.rating_avg),
        "rating_count": store.rating_count,
        "total_co2_saved_kg": float(store.total_co2_saved_kg),
        "created_at": store.created_at.isoformat() if store.created_at else None,
    }


class StoreService:
    """Service quản lý Hồ sơ Cửa hàng và Kiểm duyệt KYC (Store Onboarding & KYC)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def onboard_store(
        self,
        partner_id: UUID,
        store_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Tiếp nhận đăng ký thông tin đối tác, tọa độ GPS và chứng nhận ATVSTP."""
        name = str(store_data.get("name") or "").strip()
        address = str(store_data.get("address") or "").strip()
        if not name or not address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên cửa hàng và địa chỉ không được để trống",
            )

        latitude = float(store_data.get("latitude", 10.776889))
        longitude = float(store_data.get("longitude", 106.700806))
        if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tọa độ GPS không hợp lệ",
            )

        store = await store_repo.create_store(
            self.db,
            owner_id=partner_id,
            name=name,
            description=store_data.get("description"),
            address=address,
            phone=store_data.get("phone"),
            avatar_url=store_data.get("avatar_url"),
            kyc_license_url=store_data.get("kyc_license_url"),
            latitude=latitude,
            longitude=longitude,
        )

        return {
            "id": str(store.id),
            "name": store.name,
            "kyc_status": store.kyc_status.value,
            "message": (
                "Hồ sơ đối tác đã gửi thành công và đang chờ Quản trị viên duyệt chứng nhận ATVSTP."
            ),
        }

    async def get_store_by_id(self, store_id: UUID) -> dict[str, Any]:
        """Xem chi tiết thông tin cửa hàng và trạng thái kiểm duyệt."""
        store = await store_repo.get_store_by_id(self.db, store_id)
        if store is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy cửa hàng",
            )
        return _serialize_store(store)

    async def get_pending_stores(self) -> dict[str, Any]:
        """Tra cứu danh sách các quán đang chờ duyệt KYC (PENDING)."""
        stores = await store_repo.get_pending_stores(self.db)
        items = [_serialize_store(s) for s in stores]
        return {
            "total": len(items),
            "items": items,
        }

    async def review_store_kyc(
        self,
        store_id: UUID,
        decision: str,
        reject_reason: str | None = None,
    ) -> dict[str, Any]:
        """Quản trị viên phê duyệt (APPROVED) hoặc từ chối (REJECTED) chứng nhận ATVSTP."""
        if decision not in (KycStatus.APPROVED.value, KycStatus.REJECTED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quyết định kiểm duyệt phải là APPROVED hoặc REJECTED",
            )

        store = await store_repo.get_store_by_id(self.db, store_id)
        if store is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy cửa hàng cần duyệt",
            )

        updated = await store_repo.update_store_status(
            self.db,
            store,
            kyc_status=KycStatus(decision),
            reject_reason=reject_reason,
        )

        return {
            "store_id": str(updated.id),
            "kyc_status": updated.kyc_status.value,
            "reject_reason": updated.kyc_reject_reason,
            "reviewed_at": datetime.now(UTC).isoformat(),
        }
