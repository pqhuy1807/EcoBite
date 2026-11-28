"""Integration tests for Gamification API endpoints (/green-points/me, /vouchers)."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.db import seed as seed_module
from app.models.gamification import Voucher
from app.models.user import User


async def _seed_voucher(
    db_session: AsyncSession,
    *,
    code: str,
    points_required: int = 100,
    discount_amount: Decimal = Decimal("10000.00"),
    is_active: bool = True,
    days_until_expiry: int = 30,
) -> Voucher:
    voucher = Voucher(
        code=code,
        title=f"Voucher {code}",
        description="Ưu đãi đổi bằng Điểm Xanh",
        discount_amount=discount_amount,
        points_required=points_required,
        min_order_amount=Decimal("30000.00"),
        expires_at=datetime.now(UTC) + timedelta(days=days_until_expiry),
        is_active=is_active,
    )
    db_session.add(voucher)
    await db_session.commit()
    await db_session.refresh(voucher)
    return voucher


# ==============================================================================
# 1. GET /api/v1/green-points/me
# ==============================================================================


async def test_get_my_green_points_consumer_200(
    client: AsyncClient,
    db_session: AsyncSession,
    consumer: dict[str, object],
) -> None:
    user = consumer["user"]
    assert isinstance(user, User)
    user.green_points_balance = 320
    await db_session.commit()

    headers = consumer["headers"]
    assert isinstance(headers, dict)

    response = await client.get("/api/v1/green-points/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["balance_points"] == 320
    assert Decimal(body["total_co2_saved_kg"]) == Decimal("0.00")
    assert body["total_meals_saved"] == 0
    assert body["rank_title"] == "Chiến Binh Xanh (Eco Hero)"
    assert body["recent_ledger"] == []


async def test_get_my_green_points_requires_auth_and_consumer_role(
    client: AsyncClient,
    store_partner: dict[str, object],
) -> None:
    unauth = await client.get("/api/v1/green-points/me")
    assert unauth.status_code == 401

    partner_headers = store_partner["headers"]
    assert isinstance(partner_headers, dict)
    forbidden = await client.get("/api/v1/green-points/me", headers=partner_headers)
    assert forbidden.status_code == 403


# ==============================================================================
# 2. GET /api/v1/vouchers & GET /api/v1/vouchers/me
# ==============================================================================


async def test_list_vouchers_public_filters_inactive_and_expired(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await _seed_voucher(db_session, code="ECO25K", points_required=250)
    await _seed_voucher(db_session, code="ECO10K", points_required=100)
    await _seed_voucher(db_session, code="OFFLINE", points_required=50, is_active=False)
    await _seed_voucher(db_session, code="EXPIRED", points_required=50, days_until_expiry=-1)

    response = await client.get("/api/v1/vouchers")

    assert response.status_code == 200
    codes = [item["code"] for item in response.json()]
    assert codes == ["ECO10K", "ECO25K"]


async def test_list_my_vouchers_requires_consumer_role(
    client: AsyncClient,
    store_partner: dict[str, object],
) -> None:
    unauth = await client.get("/api/v1/vouchers/me")
    assert unauth.status_code == 401

    partner_headers = store_partner["headers"]
    assert isinstance(partner_headers, dict)
    forbidden = await client.get("/api/v1/vouchers/me", headers=partner_headers)
    assert forbidden.status_code == 403


# ==============================================================================
# 3. POST /api/v1/vouchers/{voucher_id}/redeem (Full Flow + Edge Cases)
# ==============================================================================


async def test_redeem_voucher_end_to_end_flow(
    client: AsyncClient,
    db_session: AsyncSession,
    consumer: dict[str, object],
) -> None:
    user = consumer["user"]
    assert isinstance(user, User)
    user.green_points_balance = 250
    await db_session.commit()

    voucher = await _seed_voucher(
        db_session,
        code="ECO10K",
        points_required=100,
        discount_amount=Decimal("10000.00"),
    )

    headers = consumer["headers"]
    assert isinstance(headers, dict)

    redeem_res = await client.post(f"/api/v1/vouchers/{voucher.id}/redeem", headers=headers)
    assert redeem_res.status_code == 200
    redeem_body = redeem_res.json()
    assert redeem_body["voucher_code"] == "ECO10K"
    assert Decimal(redeem_body["discount_amount"]) == Decimal("10000.00")
    assert redeem_body["points_deducted"] == 100
    assert redeem_body["remaining_balance"] == 150

    # Verify summary reflects updated balance and VOUCHER_REDEEM ledger entry
    summary_res = await client.get("/api/v1/green-points/me", headers=headers)
    assert summary_res.status_code == 200
    summary_body = summary_res.json()
    assert summary_body["balance_points"] == 150
    assert len(summary_body["recent_ledger"]) == 1
    assert summary_body["recent_ledger"][0]["points_change"] == -100
    assert summary_body["recent_ledger"][0]["balance_after"] == 150
    assert summary_body["recent_ledger"][0]["action_type"] == "VOUCHER_REDEEM"

    # Verify /vouchers/me returns the newly claimed voucher with nested details
    my_vouchers_res = await client.get("/api/v1/vouchers/me", headers=headers)
    assert my_vouchers_res.status_code == 200
    my_vouchers = my_vouchers_res.json()
    assert len(my_vouchers) == 1
    assert my_vouchers[0]["id"] == redeem_body["user_voucher_id"]
    assert my_vouchers[0]["is_used"] is False
    assert my_vouchers[0]["voucher"]["code"] == "ECO10K"


async def test_redeem_voucher_error_statuses(
    client: AsyncClient,
    db_session: AsyncSession,
    consumer: dict[str, object],
    store_partner: dict[str, object],
) -> None:
    user = consumer["user"]
    assert isinstance(user, User)
    user.green_points_balance = 50
    await db_session.commit()

    expensive = await _seed_voucher(db_session, code="ECO50K", points_required=500)
    expired = await _seed_voucher(
        db_session,
        code="OLD10K",
        points_required=10,
        days_until_expiry=-2,
    )
    expensive_id = expensive.id
    expired_id = expired.id

    consumer_headers = consumer["headers"]
    partner_headers = store_partner["headers"]
    assert isinstance(consumer_headers, dict)
    assert isinstance(partner_headers, dict)

    # 409 when insufficient points
    res_409 = await client.post(
        f"/api/v1/vouchers/{expensive_id}/redeem",
        headers=consumer_headers,
    )
    assert res_409.status_code == 409

    # 400 when expired
    res_400 = await client.post(
        f"/api/v1/vouchers/{expired_id}/redeem",
        headers=consumer_headers,
    )
    assert res_400.status_code == 400

    # 404 when voucher does not exist
    res_404 = await client.post(
        f"/api/v1/vouchers/{uuid.uuid4()}/redeem",
        headers=consumer_headers,
    )
    assert res_404.status_code == 404

    # 403 when non-consumer attempts redemption
    res_403 = await client.post(
        f"/api/v1/vouchers/{expensive_id}/redeem",
        headers=partner_headers,
    )
    assert res_403.status_code == 403


# ==============================================================================
# 4. Seed Data Consistency Check (EC4-09)
# ==============================================================================


async def test_seed_data_populates_consistent_gamification_records(
    db_engine: AsyncEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Running seed_data() must seed 4 active vouchers, pending stores, and consistent stats."""
    test_session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    monkeypatch.setattr(seed_module, "AsyncSessionLocal", test_session_factory)

    await seed_module.seed_data()

    async with test_session_factory() as session:
        from sqlalchemy import select

        from app.models.store import KycStatus, Store
        from app.services.gamification_service import GamificationService

        vouchers = await GamificationService(session).list_available_vouchers()
        assert len(vouchers) == 4
        assert {v.code for v in vouchers} == {"ECOBITE10K", "GREENHERO20K", "ECO25K", "ECO50K"}

        pending_stores = (
            (await session.execute(select(Store).where(Store.kyc_status == KycStatus.PENDING)))
            .scalars()
            .all()
        )
        assert len(pending_stores) >= 1

        an = (
            await session.execute(select(User).where(User.email == "consumer.an@ecobite.vn"))
        ).scalar_one()
        an_summary = await GamificationService(session).get_my_green_points(an.id)
        assert an_summary.balance_points == 180
        assert an_summary.total_meals_saved == 2
        assert an_summary.total_co2_saved_kg == Decimal("5.00")
        assert an_summary.recent_ledger[0].balance_after == 180

        huy = (
            await session.execute(select(User).where(User.email == "consumer.huy@ecobite.vn"))
        ).scalar_one()
        huy_summary = await GamificationService(session).get_my_green_points(huy.id)
        assert huy_summary.balance_points == 350
        assert huy_summary.total_meals_saved == 7
        assert huy_summary.total_co2_saved_kg == Decimal("17.50")
        assert huy_summary.rank_title == "Chiến Binh Xanh (Eco Hero)"

        # Verify expanded F1-F8 demo seed records (menu catalog, pending VNPay, COD QR, reviews)
        from app.models.interaction import Review
        from app.models.menu_item import MenuItem
        from app.models.order import Order, OrderStatus, PaymentMethod, PaymentStatus

        bui_store = (
            await session.execute(
                select(Store).where(Store.name == "Cơm Tấm Bụi Sài Gòn - Hai Bà Trưng")
            )
        ).scalar_one()
        bui_menu_items = (
            (await session.execute(select(MenuItem).where(MenuItem.store_id == bui_store.id)))
            .scalars()
            .all()
        )
        assert len(bui_menu_items) >= 5

        an_pending_vnpay = (
            (
                await session.execute(
                    select(Order).where(
                        Order.consumer_id == an.id,
                        Order.payment_method == PaymentMethod.VNPAY,
                        Order.payment_status == PaymentStatus.PENDING,
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(an_pending_vnpay) == 1

        bich = (
            await session.execute(select(User).where(User.email == "consumer.bich@ecobite.vn"))
        ).scalar_one()
        bich_orders = (
            (await session.execute(select(Order).where(Order.consumer_id == bich.id)))
            .scalars()
            .all()
        )
        assert any(
            o.payment_method == PaymentMethod.COD and o.status == OrderStatus.CONFIRMED
            for o in bich_orders
        )
        assert any(o.status == OrderStatus.COMPLETED for o in bich_orders)

        reviews = (await session.execute(select(Review))).scalars().all()
        assert len(reviews) >= 3
