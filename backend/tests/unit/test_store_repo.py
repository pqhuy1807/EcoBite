"""Unit tests for Store repository: KYC onboarding persistence & geo helpers."""

import uuid

from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.store import KycStatus, Store
from app.models.user import UserRole
from app.repositories import store_repo, user_repo


async def _create_partner(db: AsyncSession, suffix: str):
    return await user_repo.create(
        db,
        email=f"owner-{suffix}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Store Owner",
        role=UserRole.STORE_PARTNER,
    )


async def test_create_store_persists_pending_kyc_with_point_coordinates(
    db_session: AsyncSession,
) -> None:
    """create_store phải lưu quán ở trạng thái PENDING và tọa độ Point(longitude, latitude)."""
    owner = await _create_partner(db_session, "create")
    store = await store_repo.create_store(
        db_session,
        owner_id=owner.id,
        name="Tiệm Bánh Mì Sài Gòn",
        description="Bánh mì tươi trong ngày",
        address="123 Nguyễn Huệ, Quận 1, TP.HCM",
        phone="02838123456",
        avatar_url=None,
        kyc_license_url="https://cdn.ecobite.vn/kyc/license.pdf",
        latitude=10.776889,
        longitude=106.700806,
    )

    assert store.id is not None
    assert store.owner_id == owner.id
    assert store.name == "Tiệm Bánh Mì Sài Gòn"
    assert store.kyc_status == KycStatus.PENDING
    assert store.kyc_license_url == "https://cdn.ecobite.vn/kyc/license.pdf"
    lat, lng = store_repo.parse_point_wkt(store.location)
    assert lat == 10.776889
    assert lng == 106.700806


async def test_get_store_by_id_returns_none_when_missing(db_session: AsyncSession) -> None:
    """UUID không tồn tại phải trả về None thay vì raise."""
    assert await store_repo.get_store_by_id(db_session, uuid.uuid4()) is None


async def test_get_store_by_id_returns_existing_store(db_session: AsyncSession) -> None:
    owner = await _create_partner(db_session, "get")
    created = await store_repo.create_store(
        db_session,
        owner_id=owner.id,
        name="Quán Cơm Tấm",
        description=None,
        address="45 Đinh Tiên Hoàng, Q.1, TP.HCM",
        phone=None,
        avatar_url=None,
        kyc_license_url=None,
        latitude=10.788,
        longitude=106.698,
    )

    found = await store_repo.get_store_by_id(db_session, created.id)
    assert found is not None
    assert found.id == created.id
    assert found.name == "Quán Cơm Tấm"


async def test_get_pending_stores_returns_only_pending_kyc(db_session: AsyncSession) -> None:
    """Duyệt danh sách chờ duyệt: chỉ chứa các quán ở trạng thái PENDING."""
    owner = await _create_partner(db_session, "pending")
    pending_store = await store_repo.create_store(
        db_session,
        owner_id=owner.id,
        name="Quán Chờ Duyệt",
        description=None,
        address="1 Lê Lợi, Q.1",
        phone=None,
        avatar_url=None,
        kyc_license_url=None,
        latitude=10.77,
        longitude=106.69,
    )
    db_session.add_all(
        [
            Store(
                owner_id=owner.id,
                name="Quán Đã Duyệt",
                address="2 Lê Lợi, Q.1",
                location="POINT(106.7 10.77)",
                kyc_status=KycStatus.APPROVED,
            ),
            Store(
                owner_id=owner.id,
                name="Quán Bị Từ Chối",
                address="3 Lê Lợi, Q.1",
                location="POINT(106.71 10.78)",
                kyc_status=KycStatus.REJECTED,
            ),
        ]
    )
    await db_session.commit()

    pending = await store_repo.get_pending_stores(db_session)
    assert pending_store.name in {s.name for s in pending}
    assert all(s.kyc_status == KycStatus.PENDING for s in pending)


async def test_update_store_status_sets_and_clears_reject_reason(db_session: AsyncSession) -> None:
    """APPROVED phải xoá lý do từ chối; REJECTED phải lưu lý do kèm theo."""
    owner = await _create_partner(db_session, "update")
    store = await store_repo.create_store(
        db_session,
        owner_id=owner.id,
        name="Quán Kiểm Duyệt",
        description=None,
        address="10 Đồng Khởi, Q.1",
        phone=None,
        avatar_url=None,
        kyc_license_url="https://cdn.ecobite.vn/kyc/license.pdf",
        latitude=10.7745,
        longitude=106.7038,
    )

    approved = await store_repo.update_store_status(
        db_session,
        store,
        kyc_status=KycStatus.APPROVED,
        reject_reason="Không liên quan",
    )
    assert approved.kyc_status == KycStatus.APPROVED
    assert approved.kyc_reject_reason is None

    rejected = await store_repo.update_store_status(
        db_session,
        store,
        kyc_status=KycStatus.REJECTED,
        reject_reason="Giấy phép ATVSTP đã hết hiệu lực",
    )
    assert rejected.kyc_status == KycStatus.REJECTED
    assert rejected.kyc_reject_reason == "Giấy phép ATVSTP đã hết hiệu lực"


def test_parse_point_wkt_supports_plain_wkt_ewkt_and_wkb() -> None:
    """Hàm parse phải xử lý được WKT thường, EWKT (SRID prefix) và WKB (kết quả PostGIS)."""
    assert store_repo.parse_point_wkt("POINT(105.0 21.0)") == (21.0, 105.0)
    assert store_repo.parse_point_wkt("SRID=4326;POINT(106.700806 10.776)") == (10.776, 106.700806)

    wkb_point = from_shape(Point(105.5, 20.5), srid=4326)
    assert store_repo.parse_point_wkt(wkb_point) == (20.5, 105.5)


def test_haversine_distance_in_dimensional_meters() -> None:
    """Khoảng cách Haversine giữa 2 điểm nổi tiếng ~200m phải nằm trong biên độ hợp lý."""
    distance = store_repo.haversine_distance_meters(
        10.776889, 106.700806,  # Tâm Nguyễn Huệ
        10.7755, 106.7015,  # Điểm cách ~180-220m về phía nam
    )
    assert 100.0 < distance < 300.0
