"""Integration tests and concurrency benchmark for food-rescue order placement.

Verifies Guardrail #4: Anti-overselling through database-level atomic conditional
decrement (and Redis distributed lock where available).

Benchmark Scenario:
- 1 Surplus Dish with remaining_quantity = 2.
- 50 concurrent requests attempting to purchase 1 item each.
- Expected outcome:
  - Total requests: 50
  - HTTP 201 Created: Exactly 2
  - HTTP 409 Conflict: Exactly 48
  - Final remaining_quantity: 0
  - Dish status: SOLD_OUT
  - Total orders in database: Exactly 2
  - No overselling, no negative inventory, no orphan stock leaks.
"""

import asyncio
import time
import uuid
from collections.abc import AsyncIterator
from datetime import time as datetime_time
from decimal import Decimal
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.dish import Dish, DishStatus
from app.models.menu_item import DietaryType, ItemCategory, MenuItem
from app.models.order import Order
from app.models.store import KycStatus, Store
from app.models.user import User, UserRole


async def _setup_concurrency_fixture(
    db_session: AsyncSession,
    *,
    initial_stock: int = 2,
    consumer_count: int = 50,
) -> tuple[Dish, list[User]]:
    """Seed merchant, store, menu item, dish with limited stock, and 50 consumers."""
    merchant = User(
        email=f"merchant_{uuid.uuid4().hex[:8]}@ecobite.vn",
        hashed_password="not-used-by-tests",
        full_name="Merchant Concurrency",
        role=UserRole.STORE_PARTNER,
    )
    db_session.add(merchant)
    await db_session.flush()

    store = Store(
        owner_id=merchant.id,
        name="Quán Cơm Tấm Chống Tranh Chấp Tồn Kho",
        address="123 Đinh Tiên Hoàng, Quận 1",
        location="POINT(106.6990 10.7850)",
        kyc_status=KycStatus.APPROVED,
    )
    db_session.add(store)
    await db_session.flush()

    menu_item = MenuItem(
        store_id=store.id,
        name="Cơm Tấm Sườn Bì Chả Đặc Biệt",
        image_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
        original_price=Decimal("60000.00"),
        category=ItemCategory.RICE,
        dietary_type=DietaryType.NON_VEGAN,
    )
    db_session.add(menu_item)
    await db_session.flush()

    dish = Dish(
        store_id=store.id,
        menu_item_id=menu_item.id,
        name="Cơm Tấm Sườn Bì (Suất Cuối Giờ Giảm 70%)",
        category=ItemCategory.RICE,
        image_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
        original_price=Decimal("60000.00"),
        rescue_price=Decimal("18000.00"),
        override_discounted_price=Decimal("18000.00"),
        pickup_start_time=datetime_time(0, 0),
        pickup_end_time=datetime_time(23, 59),
        total_quantity=initial_stock,
        remaining_quantity=initial_stock,
        status=DishStatus.ACTIVE,
        estimated_co2_kg_per_dish=Decimal("2.50"),
    )
    db_session.add(dish)

    consumers = [
        User(
            email=f"consumer_concurrency_{i}_{uuid.uuid4().hex[:6]}@ecobite.vn",
            hashed_password="not-used-by-tests",
            full_name=f"Consumer {i}",
            role=UserRole.CONSUMER,
        )
        for i in range(consumer_count)
    ]
    db_session.add_all(consumers)
    await db_session.commit()
    await db_session.refresh(dish)

    return dish, consumers


@pytest.mark.asyncio
async def test_order_placement_concurrency_benchmark(tmp_path: Path) -> None:
    """Benchmark 50 concurrent buyers competing for 2 surplus dishes.

    Validates:
    - 50 concurrent HTTP POST requests to `/api/v1/orders`.
    - Exactly 2 requests succeed with HTTP 201 Created.
    - Exactly 48 requests receive HTTP 409 Conflict.
    - Zero overselling: remaining_quantity ends at 0.
    - Exactly 2 orders are persisted in the database.
    - Dish transitions to SOLD_OUT status.
    - Detailed latency benchmark metrics are recorded (total, avg, p50, p95).
    """
    total_requests = 50
    initial_stock = 2

    db_file = tmp_path / "concurrency_benchmark.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        poolclass=NullPool,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # 1. Chuẩn bị dữ liệu: 1 món ăn có tồn kho = 2, 50 consumers riêng biệt
    async with session_factory() as setup_db:
        dish, consumers = await _setup_concurrency_fixture(
            setup_db,
            initial_stock=initial_stock,
            consumer_count=total_requests,
        )
        dish_id = str(dish.id)

    # 2. Cấu hình session độc lập cho từng request (mô phỏng đúng môi trường production)
    async def _concurrent_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    orig_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _concurrent_get_db

    auth_headers = [{"Authorization": f"Bearer {create_access_token(c.id)}"} for c in consumers]

    try:
        # 3. Thực thi 50 request mua hàng đồng thời qua AsyncClient ASGI
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            latencies: list[float] = []

            async def _send_order_request(idx: int) -> tuple[int, float]:
                req_start = time.perf_counter()
                resp = await client.post(
                    "/api/v1/orders",
                    json={
                        "dish_id": dish_id,
                        "quantity": 1,
                        "payment_method": "COD",
                    },
                    headers=auth_headers[idx],
                )
                req_latency = (time.perf_counter() - req_start) * 1000
                return resp.status_code, req_latency

            benchmark_start = time.perf_counter()
            results = await asyncio.gather(*[_send_order_request(i) for i in range(total_requests)])
            total_execution_time_ms = (time.perf_counter() - benchmark_start) * 1000

    finally:
        if orig_override is not None:
            app.dependency_overrides[get_db] = orig_override
        else:
            app.dependency_overrides.pop(get_db, None)

    # 4. Phân tích kết quả benchmark
    status_codes = [r[0] for r in results]
    latencies = [r[1] for r in results]
    latencies_sorted = sorted(latencies)

    success_count = status_codes.count(201)
    conflict_count = status_codes.count(409)
    other_codes = [c for c in status_codes if c not in (201, 409)]

    avg_latency_ms = sum(latencies) / len(latencies)
    p50_latency_ms = latencies_sorted[int(len(latencies_sorted) * 0.50)]
    p95_latency_ms = latencies_sorted[int(len(latencies_sorted) * 0.95)]

    # 5. Kiểm tra tính toàn vẹn dữ liệu trong Database (Audit)
    try:
        async with session_factory() as audit_db:
            final_dish = await audit_db.get(Dish, dish.id)
            assert final_dish is not None

            orders_in_db = (
                await audit_db.execute(select(func.count(Order.id)).where(Order.dish_id == dish.id))
            ).scalar_one()
    finally:
        await engine.dispose()

    # In kết quả benchmark ra console để quan sát trực tiếp
    print("\n" + "=" * 70)
    print("           ECOBITE CONCURRENCY BENCHMARK REPORT (PHẦN 4)")
    print("=" * 70)
    print(f" Total Requests Sent    : {total_requests}")
    print(f" Initial Stock          : {initial_stock}")
    print(f" HTTP 201 Created       : {success_count} (Expected: {initial_stock})")
    expected_conflicts = total_requests - initial_stock
    print(f" HTTP 409 Conflict      : {conflict_count} (Expected: {expected_conflicts})")
    print(f" Other Status Codes     : {other_codes} (Expected: [])")
    print(f" Final Stock Remaining  : {final_dish.remaining_quantity} (Expected: 0)")
    print(f" Dish Final Status      : {final_dish.status.value} (Expected: SOLD_OUT)")
    print(f" Total Orders in DB     : {orders_in_db} (Expected: {initial_stock})")
    print("-" * 70)
    print(" LATENCY & PERFORMANCE METRICS:")
    print(f" - Total Execution Time : {total_execution_time_ms:.2f} ms")
    print(f" - Average Latency      : {avg_latency_ms:.2f} ms")
    print(f" - p50 Latency (Median) : {p50_latency_ms:.2f} ms")
    print(f" - p95 Latency          : {p95_latency_ms:.2f} ms")
    print("=" * 70 + "\n")

    # 6. Assertions theo đúng yêu cầu đề bài
    assert other_codes == [], f"Unexpected status codes: {other_codes}"
    assert success_count == initial_stock, (
        f"Expected exactly {initial_stock} successful orders, got {success_count}"
    )
    assert conflict_count == (total_requests - initial_stock), (
        f"Expected exactly {total_requests - initial_stock} 409 conflicts, got {conflict_count}"
    )
    assert final_dish.remaining_quantity == 0, (
        f"Remaining quantity must be 0, got {final_dish.remaining_quantity}"
    )
    assert final_dish.status == DishStatus.SOLD_OUT, (
        f"Dish status must be SOLD_OUT, got {final_dish.status}"
    )
    assert orders_in_db == initial_stock, (
        f"Orders in database must be exactly {initial_stock}, got {orders_in_db}"
    )
