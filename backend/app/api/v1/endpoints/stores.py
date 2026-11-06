from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/stores/onboard", status_code=status.HTTP_201_CREATED)
def onboard_store(store_in: dict) -> Any:
    """
    Tiếp nhận đăng ký thông tin đối tác, tọa độ GPS và đường dẫn chứng nhận ATVSTP (KYC).
    Trạng thái khởi tạo: PENDING.
    """
    if not store_in.get("name") or not store_in.get("address"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên cửa hàng và địa chỉ không được để trống"
        )
    return {
        "id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
        "name": store_in.get("name"),
        "kyc_status": "PENDING",
        "message": "Hồ sơ đối tác đã gửi thành công và đang chờ Quản trị viên duyệt chứng nhận ATVSTP."
    }

@router.get("/stores/{store_id}")
def get_store_detail(store_id: UUID) -> Any:
    """
    Xem chi tiết thông tin cửa hàng và trạng thái kiểm duyệt.
    """
    return {
        "id": str(store_id),
        "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
        "kyc_status": "APPROVED",
        "address": "123 Đường Nguyễn Huệ, Phường Bến Nghé, Quận 1, TP.HCM",
        "latitude": 10.776889,
        "longitude": 106.700806,
        "phone": "02838123456",
        "kyc_license_url": "https://cdn.ecobite.vn/kyc/atvstp_license1.pdf"
    }

@router.get("/admin/stores/pending")
def get_pending_stores() -> Any:
    """
    Dành riêng cho ADMIN tra cứu danh sách các quán chờ duyệt KYC.
    """
    return {
        "total": 1,
        "items": [
            {
                "id": "e4f8d2a1-3c4b-5a6d-7e8f-9a0b1c2d3e4f",
                "name": "Tiệm Bánh Mì & Cơm Trưa Sài Gòn",
                "kyc_status": "PENDING",
                "created_at": "2026-11-02T10:00:00Z"
            }
        ]
    }

@router.patch("/admin/stores/{store_id}/review")
def review_store_kyc(store_id: UUID, review_in: dict) -> Any:
    """
    Quyết định phê duyệt (APPROVED) hoặc từ chối (REJECTED kèm lý do) chứng nhận ATVSTP của quán.
    """
    decision = review_in.get("decision")
    if decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quyết định kiểm duyệt phải là APPROVED hoặc REJECTED"
        )
    return {
        "store_id": str(store_id),
        "kyc_status": decision,
        "reject_reason": review_in.get("reject_reason") if decision == "REJECTED" else None,
        "reviewed_at": "2026-11-02T10:30:00Z"
    }