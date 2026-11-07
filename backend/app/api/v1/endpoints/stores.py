"""Store Onboarding, KYC Verification, and PostGIS Spatial Discovery endpoints."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DBSession, require_roles
from app.models.user import User, UserRole
from app.services.discovery import DiscoveryService
from app.services.store_service import StoreService

router = APIRouter()


@router.post("/stores/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_store(
    store_in: dict[str, Any],
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.STORE_PARTNER, UserRole.ADMIN)),
    ],
) -> dict[str, Any]:
    """Tiếp nhận đăng ký thông tin đối tác, tọa độ GPS và đường dẫn chứng nhận ATVSTP (KYC)."""
    service = StoreService(db)
    return await service.onboard_store(current_user.id, store_in)


@router.get("/stores/nearby")
async def search_nearby_stores(
    db: DBSession,
    lat: Annotated[float, Query(ge=-90.0, le=90.0, description="Vĩ độ người dùng")],
    lng: Annotated[float, Query(ge=-180.0, le=180.0, description="Kinh độ người dùng")],
    radius_km: Annotated[
        float,
        Query(gt=0.0, le=50.0, description="Bán kính tìm kiếm (km)"),
    ] = 3.0,
    category: Annotated[str | None, Query(description="Lọc theo danh mục món ăn")] = None,
) -> dict[str, Any]:
    """Tìm kiếm quán lân cận bằng tọa độ GPS và bán kính (PostGIS Radar Discovery)."""
    service = DiscoveryService(db)
    return await service.search_nearby_stores(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        category=category,
    )


@router.get("/stores/{store_id}")
async def get_store_detail(
    store_id: UUID,
    db: DBSession,
) -> dict[str, Any]:
    """Xem chi tiết thông tin cửa hàng và trạng thái kiểm duyệt."""
    service = StoreService(db)
    return await service.get_store_by_id(store_id)


@router.get(
    "/admin/stores/pending",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def get_pending_stores(db: DBSession) -> dict[str, Any]:
    """Dành riêng cho ADMIN tra cứu danh sách các quán chờ duyệt KYC."""
    service = StoreService(db)
    return await service.get_pending_stores()


@router.patch(
    "/admin/stores/{store_id}/review",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
async def review_store_kyc(
    store_id: UUID,
    review_in: dict[str, Any],
    db: DBSession,
) -> dict[str, Any]:
    """Quyết định phê duyệt (APPROVED) hoặc từ chối (REJECTED) chứng nhận ATVSTP của quán."""
    service = StoreService(db)
    decision = str(review_in.get("decision") or review_in.get("kyc_status") or "").upper()
    reject_reason = review_in.get("reject_reason") or review_in.get("kyc_reject_reason")
    return await service.review_store_kyc(
        store_id=store_id,
        decision=decision,
        reject_reason=reject_reason,
    )
