"""Unit tests for StoreService: onboarding + KYC review business rules."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import KycStatus
from app.models.user import UserRole
from app.repositories import store_repo, user_repo
from app.services.store_service import StoreService

ONBOARD_PAYLOAD = {
    "name": "Tiệm Bánh Mì Sài Gòn",
    "description": "Bánh mì tươi trong ngày",
    "address": "123 Nguyễn Huệ, Quận 1, TP.HCM",
    "latitude": 10.776889,
    "longitude": 106.700806,
    "phone": "02838123456",
    "kyc_license_url": "https://cdn.ecobite.vn/kyc/license.pdf",
}


async def _create_partner(db: AsyncSession):
    return await user_repo.create(
        db,
        email=f"svc-{uuid.uuid4().hex[:8]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Store Owner",
        role=UserRole.STORE_PARTNER,
    )


async def test_onboard_store_returns_pending_registration(db_session: AsyncSession) -> None:
    """Đăng ký KYC mới phải trả về trạng thái PENDING kèm thông điệp chờ duyệt."""
    partner = await _create_partner(db_session)
    result = await StoreService(db_session).onboard_store(partner.id, dict(ONBOARD_PAYLOAD))

    assert uuid.UUID(result["id"]) is not None
    assert result["name"] == "Tiệm Bánh Mì Sài Gòn"
    assert result["kyc_status"] == KycStatus.PENDING.value
    assert "message" in result

    persisted = await store_repo.get_store_by_id(db_session, uuid.UUID(result["id"]))
    assert persisted is not None
    assert persisted.kyc_status == KycStatus.PENDING


async def test_onboard_store_requires_name_and_address(db_session: AsyncSession) -> None:
    """Tên hoặc địa chỉ trống phải bị chặn bằng 400."""
    service = StoreService(db_session)
    partner = await _create_partner(db_session)

    with pytest.raises(HTTPException) as missing_name:
        await service.onboard_store(partner.id, {**ONBOARD_PAYLOAD, "name": "   "})
    assert missing_name.value.status_code == 400

    with pytest.raises(HTTPException) as missing_address:
        await service.onboard_store(partner.id, {**ONBOARD_PAYLOAD, "address": ""})
    assert missing_address.value.status_code == 400


async def test_onboard_store_rejects_out_of_range_coordinates(db_session: AsyncSession) -> None:
    """Toạ độ kinh/vĩ tuyến ngoài biên WGS84 phải bị chặn bằng 400."""
    service = StoreService(db_session)
    partner = await _create_partner(db_session)

    with pytest.raises(HTTPException) as bad_lat:
        await service.onboard_store(partner.id, {**ONBOARD_PAYLOAD, "latitude": 91.0})
    assert bad_lat.value.status_code == 400

    with pytest.raises(HTTPException) as bad_lng:
        await service.onboard_store(partner.id, {**ONBOARD_PAYLOAD, "longitude": 190.0})
    assert bad_lng.value.status_code == 400


async def test_get_store_by_id_returns_serialized_store(db_session: AsyncSession) -> None:
    """Chi tiết quán phải chứa tọa độ đã giải mã và trạng thái KYC."""
    partner = await _create_partner(db_session)
    store = await store_repo.create_store(
        db_session,
        owner_id=partner.id,
        name="Quán Chi Tiết",
        description=None,
        address="88 Lê Thánh Tôn, Q.1",
        phone=None,
        avatar_url=None,
        kyc_license_url=None,
        latitude=10.78,
        longitude=106.70,
    )

    detail = await StoreService(db_session).get_store_by_id(store.id)
    assert detail["id"] == str(store.id)
    assert detail["latitude"] == 10.78
    assert detail["longitude"] == 106.70
    assert detail["kyc_status"] == KycStatus.PENDING.value


async def test_get_store_by_id_raises_404_when_missing(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as error:
        await StoreService(db_session).get_store_by_id(uuid.uuid4())
    assert error.value.status_code == 404


async def test_get_pending_stores_returns_items_and_total(db_session: AsyncSession) -> None:
    partner = await _create_partner(db_session)
    await store_repo.create_store(
        db_session,
        owner_id=partner.id,
        name="Quán Chờ Duyệt Service",
        description=None,
        address="7 Pasteur, Q.1",
        phone=None,
        avatar_url=None,
        kyc_license_url=None,
        latitude=10.7845,
        longitude=106.6961,
    )

    pending = await StoreService(db_session).get_pending_stores()
    assert pending["total"] >= 1
    assert any(item["name"] == "Quán Chờ Duyệt Service" for item in pending["items"])


async def test_review_store_kyc_approves_and_persists(db_session: AsyncSession) -> None:
    """APPROVED phải cập nhật trạng thái trong DB."""
    partner = await _create_partner(db_session)
    store = await store_repo.create_store(
        db_session,
        owner_id=partner.id,
        name="Quán Nhận Duyệt",
        description=None,
        address="1 Hai Bà Trưng, Q.1",
        phone=None,
        avatar_url=None,
        kyc_license_url=None,
        latitude=10.779,
        longitude=106.7005,
    )

    result = await StoreService(db_session).review_store_kyc(
        store.id, decision="APPROVED", reject_reason=None
    )
    assert result["store_id"] == str(store.id)
    assert result["kyc_status"] == KycStatus.APPROVED.value
    assert result["reject_reason"] is None
    assert "reviewed_at" in result

    persisted = await store_repo.get_store_by_id(db_session, store.id)
    assert persisted is not None
    assert persisted.kyc_status == KycStatus.APPROVED


async def test_review_store_kyc_rejected_keeps_reason(db_session: AsyncSession) -> None:
    partner = await _create_partner(db_session)
    store = await store_repo.create_store(
        db_session,
        owner_id=partner.id,
        name="Quán Bị Từ Chối Service",
        description=None,
        address="2 Hai Bà Trưng, Q.1",
        phone=None,
        avatar_url=None,
        kyc_license_url=None,
        latitude=10.779,
        longitude=106.7005,
    )

    result = await StoreService(db_session).review_store_kyc(
        store.id,
        decision="REJECTED",
        reject_reason="Giấy phép ATVSTP hết hiệu lực",
    )
    assert result["kyc_status"] == KycStatus.REJECTED.value
    assert result["reject_reason"] == "Giấy phép ATVSTP hết hiệu lực"


async def test_review_store_kyc_rejects_invalid_decision(db_session: AsyncSession) -> None:
    """Ngoài APPROVED / REJECTED phải chặn bằng 400."""
    partner = await _create_partner(db_session)
    store = await store_repo.create_store(
        db_session,
        owner_id=partner.id,
        name="Quán Định Trạng Sai",
        description=None,
        address="3 Hai Bà Trưng, Q.1",
        phone=None,
        avatar_url=None,
        kyc_license_url=None,
        latitude=10.779,
        longitude=106.7005,
    )

    with pytest.raises(HTTPException) as error:
        await StoreService(db_session).review_store_kyc(
            store.id, decision="PENDING", reject_reason=None
        )
    assert error.value.status_code == 400


async def test_review_store_kyc_raises_404_for_missing_store(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as error:
        await StoreService(db_session).review_store_kyc(
            uuid.uuid4(), decision="APPROVED", reject_reason=None
        )
    assert error.value.status_code == 404
