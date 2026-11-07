from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class StoreService:
    """Service quản lý Hồ sơ Cửa hàng và Kiểm duyệt KYC (Store Onboarding & KYC)."""

    def __init__(self, db: Session):
        self.db = db

    def onboard_store(self, partner_id: UUID, store_data: dict) -> dict:
        """Tiếp nhận đăng ký thông tin đối tác, tọa độ GPS và chứng nhận ATVSTP.

        Trạng thái khởi tạo: PENDING.
        """
        if not store_data.get("name") or not store_data.get("address"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên cửa hàng và địa chỉ không được để trống",
            )

        return {
            "id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
            "name": store_data.get("name"),
            "kyc_status": "PENDING",
            "message": (
                "Hồ sơ đối tác đã gửi thành công và đang chờ Quản trị viên duyệt chứng nhận ATVSTP."
            ),
        }

    def get_store_by_id(self, store_id: UUID) -> dict | None:
        """Xem chi tiết thông tin cửa hàng và trạng thái kiểm duyệt."""
        return {
            "id": str(store_id),
            "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
            "kyc_status": "APPROVED",
            "address": "123 Đường Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM",
            "latitude": 10.776889,
            "longitude": 106.700806,
        }

    def review_store_kyc(
        self, store_id: UUID, decision: str, reject_reason: str | None = None
    ) -> dict:
        """Quản trị viên phê duyệt (APPROVED) hoặc từ chối (REJECTED) chứng nhận ATVSTP của quán."""
        if decision not in ["APPROVED", "REJECTED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quyết định kiểm duyệt phải là APPROVED hoặc REJECTED",
            )

        return {
            "store_id": str(store_id),
            "kyc_status": decision,
            "reject_reason": reject_reason if decision == "REJECTED" else None,
            "reviewed_at": "2026-11-02T10:30:00Z",
        }
