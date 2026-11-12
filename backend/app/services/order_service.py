"""Business logic for food rescue orders: stock locking, green impact, cancellation.

Complies strictly with:
- Guardrail #4: Redis distributed lock (`lock:dish:{dish_id}`) wrapped around the
  atomic SQL decrement so inventory stays consistent under high concurrency.
- Guardrail #5: Rule-based time-shifted pricing only — never AI-guessed prices.
"""

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import distributed_lock
from app.models.dish import Dish, DishStatus
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.repositories import dish_repo
from app.repositories.order_repo import OrderRepository
from app.schemas.order import OrderCreate, OrderDetailResponse
from app.services.dish_service import DishService

logger = logging.getLogger(__name__)

# Redis lock namespace protecting the stock-decrement critical section of a dish,
# as prescribed by AGENTS.md Guardrail #4 (`lock:dish:{dish_id}`).
DISH_LOCK_KEY_TEMPLATE = "lock:dish:{dish_id}"

# Max attempts to mint a unique `EB-YYYYMMDD-XXXXXXXX` code (order_code is UNIQUE).
ORDER_CODE_MAX_ATTEMPTS = 3


def _ensure_utc(value: datetime) -> datetime:
    """Chuẩn hóa về UTC: SQLite trả datetime naive, Postgres trả tz-aware."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


# Green Points conversion rate: 1 kg CO2e saved == 10 Green Points.
GREEN_POINTS_PER_CO2_KG = 10

# A placed order can still be cancelled until the meal is handed over or expires.
CANCELLABLE_STATUSES: tuple[OrderStatus, ...] = (
    OrderStatus.CONFIRMED,
    OrderStatus.READY_FOR_PICKUP,
)


class OrderService:
    """Coordinate rescue orders from placement through to cancellation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.orders = OrderRepository(db)

    async def create_rescue_order(
        self,
        consumer_id: uuid.UUID,
        payload: OrderCreate,
        *,
        now: datetime | None = None,
    ) -> Order:
        """Đặt đơn giải cứu suất ăn: kiểm tra nghiệp vụ → khóa Redis → trừ kho nguyên tử.

        Quy trình:
        1. Nạp món và kiểm tra `ACTIVE` + khung giờ đón món
           (`pickup_start_time <= now <= pickup_end_time`).
        2. Định giá Rule-based theo luật thời gian (Guardrail #5, không AI phỏng đoán).
        3. Chốt khóa phân tán Redis `lock:dish:{dish_id}` rồi gọi
           `dish_repo.atomic_decrement_quantity` — affected rows == 0 nghĩa là
           hết suất / không đủ số lượng → HTTP 409 (chống over-selling khi tải cao).
           Lưu ý: khóa phân tán giúp giảm tranh chấp; tính đúng đắn cuối cùng do
           chính câu UPDATE nguyên tử trong DB đảm bảo (kể cả khi Redis chết).
        4. Đo lường tác động xanh: `co2_saved_kg = quantity × estimated_co2_kg_per_dish`
           (mặc định 2.5 kg/suất) và `green_points = co2_saved_kg × 10`.
        5. Sinh mã `EB-YYYYMMDD-<8 ký tự hash>` (có retry khi trùng UNIQUE) và lưu đơn.

        Args:
            consumer_id: ID người tiêu dùng đặt đơn.
            payload: Dữ liệu đặt đơn (dish_id, quantity, payment_method).
            now: Mốc thời gian dùng cho kiểm tra khung giờ & định giá; `None` để
                dùng đồng hồ thực (chấp nhận inject khi test cho tính tất định).

        Returns:
            Đơn hàng `Order` đã lưu với trạng thái CONFIRMED.

        Raises:
            HTTPException: 404 không tìm thấy món; 400 ngoài khung giờ đón món;
                409 món không ACTIVE, hết suất/không đủ số lượng, hoặc trùng mã
                đơn sau 3 lần sinh lại.
        """
        current_time = now if now is not None else datetime.now()

        # --- 1. Nạp món ăn và kiểm tra nghiệp vụ mở bán -----------------------
        dish = await dish_repo.get_by_id(self.db, payload.dish_id)
        if dish is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dish not found")
        self._validate_dish_sellable(dish, current_time)

        # --- 2. Định giá Rule-based theo thời điểm (Guardrail #5) --------------
        unit_price, _, _ = DishService.calculate_time_shifted_discount(
            original_price=dish.original_price,
            pickup_start_time=dish.pickup_start_time,
            pickup_end_time=dish.pickup_end_time,
            override_discounted_price=dish.override_discounted_price,
            rule_discount_start_time=dish.rule_discount_start_time,
            current_time=current_time,
        )

        # --- 3. Redis Distributed Lock + trừ kho nguyên tử (Guardrail #4) ------
        async with distributed_lock(DISH_LOCK_KEY_TEMPLATE.format(dish_id=dish.id)):
            updated_dish = await dish_repo.atomic_decrement_quantity(
                self.db, dish.id, payload.quantity
            )
            if updated_dish is None:
                # Guardrail #4: affected rows == 0 → hết suất hoặc không đủ số lượng.
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Món ăn đã hết suất hoặc số lượng còn lại không đủ",
                )

        # --- 4. Đo lường Tác động Môi trường & Điểm Xanh -----------------------
        co2_saved_kg = (Decimal(payload.quantity) * dish.estimated_co2_kg_per_dish).quantize(
            Decimal("0.01")
        )
        green_points_earned = int(co2_saved_kg * GREEN_POINTS_PER_CO2_KG)

        # --- 5. Lưu đơn hàng và trả về -----------------------------------------
        return await self._persist_order(
            consumer_id=consumer_id,
            dish=dish,
            payload=payload,
            unit_price=unit_price,
            co2_saved_kg=co2_saved_kg,
            green_points_earned=green_points_earned,
            current_time=current_time,
        )

    async def cancel_order(
        self,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        now: datetime | None = None,
    ) -> Order:
        """Hủy đơn: kiểm tra quyền → chặn quá hạn → chuyển CANCELLED nguyên tử → hoàn kho.

        Ai được phép hủy:
        - Chủ đơn (`order.consumer_id == user_id`), hoặc
        - Chủ cửa hàng bán món ăn (`store.owner_id == user_id`) — đối tác có quyền
          hủy đơn đang chờ xử lý của khách tại quán mình.

        Hạn chót lấy món: khi caller truyền `now` (HTTP layer luôn truyền), đơn đã
        quá `pickup_deadline` sẽ bị chặn 409 và không hoàn kho. Khi `now` là None
        (mặc định, phục vụ unit test nội bộ cho tính tất định), bước kiểm tra hạn
        chót được bỏ qua để giữ hành vi cũ.

        Chỉ đơn ở trạng thái có thể hủy (CONFIRMED / READY_FOR_PICKUP) được phép
        chuyển trạng thái. Phần hoàn kho chạy sau khi chiến thắng chuyển trạng
        thái nguyên tử, nên hai request hủy cùng lúc tuyệt đối không hoàn kho hai
        lần (chống double-refund).

        Args:
            order_id: ID đơn hàng cần hủy.
            user_id: ID người dùng thực hiện (chủ đơn hoặc chủ cửa hàng).
            now: Mốc thời gian hiện tại để đối chiếu `pickup_deadline`; `None`
                bỏ qua kiểm tra hạn chót.

        Returns:
            Đơn hàng đã ở trạng thái CANCELLED.

        Raises:
            HTTPException: 404 không tìm thấy đơn; 403 không phải chủ đơn/chủ quán;
                409 đã quá hạn lấy món hoặc đơn đã kết thúc
                (COMPLETED / EXPIRED / CANCELLED).
        """
        order = await self.orders.get_by_id(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        is_consumer_owner = order.consumer_id == user_id
        is_store_owner = order.store.owner_id == user_id
        if not (is_consumer_owner or is_store_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền hủy đơn hàng này",
            )

        # Quá hạn chót lấy món thì không còn được hủy (đơn sẽ tự EXPIRED).
        if now is not None and _ensure_utc(now) > _ensure_utc(order.pickup_deadline):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Đã quá hạn chót lấy món, đơn hàng không thể hủy",
            )

        # Chuyển trạng thái nguyên tử: chỉ một request "thắng" được phép đi tiếp.
        cancelled = await self.orders.cancel_if_allowed(order.id, CANCELLABLE_STATUSES)
        if cancelled is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Đơn hàng ở trạng thái {order.status.value} không thể hủy",
            )

        # Hoàn số lượng suất đã đặt về kho (UPDATE ... remaining_quantity + :qty).
        restored = await dish_repo.atomic_increment_quantity(self.db, order.dish_id, order.quantity)
        if restored is None:
            # Dish bị xóa đồng thời (FK CASCADE kéo theo đơn) — đã hủy trước đó.
            logger.warning("Could not restore stock for dish %s on cancel", order.dish_id)
        return cancelled

    async def get_my_orders(
        self,
        consumer_id: uuid.UUID,
        *,
        order_status: OrderStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:
        """Return paginated order history placed by `consumer_id`."""
        return await self.orders.list_by_consumer(
            consumer_id,
            order_status=order_status,
            skip=skip,
            limit=limit,
        )

    async def get_store_orders(
        self,
        store_id: uuid.UUID,
        *,
        order_status: OrderStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:
        """Return paginated orders belonging to `store_id`."""
        return await self.orders.list_by_store(
            store_id,
            order_status=order_status,
            skip=skip,
            limit=limit,
        )

    async def get_order_detail(
        self,
        order_id: uuid.UUID,
        current_user: User,
        *,
        now: datetime | None = None,
    ) -> OrderDetailResponse:
        """Fetch an order with RBAC check and expose QR metadata only while valid.

        Access rules:
        - ADMIN: may inspect any order.
        - CONSUMER: may inspect only their own orders.
        - STORE_PARTNER: may inspect only orders belonging to their store.
        """
        order = await self.orders.get_by_id(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        if not self._can_view_order(order, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xem đơn hàng này",
            )

        current_time = _ensure_utc(now) if now is not None else datetime.now(UTC)
        detail = OrderDetailResponse.model_validate(order)
        if not self._is_valid_qr_token_for_order(order, current_time):
            detail.qr_token = None
        return detail

    @staticmethod
    def _can_view_order(order: Order, user: User) -> bool:
        """Enforce Consumer, Store Partner and Admin order access permissions."""
        if user.role == UserRole.ADMIN:
            return True
        if user.role == UserRole.CONSUMER:
            return order.consumer_id == user.id
        if user.role == UserRole.STORE_PARTNER:
            return order.store.owner_id == user.id
        return False

    @staticmethod
    def _is_valid_qr_token_for_order(order: Order, current_time: datetime) -> bool:
        """Expose QR metadata only for pre-pickup orders with an unused, unexpired token."""
        qr_token = order.qr_token
        if qr_token is None or qr_token.is_used:
            return False
        if order.status not in CANCELLABLE_STATUSES:
            return False
        return _ensure_utc(qr_token.expires_at) >= current_time

    @staticmethod
    def _validate_dish_sellable(dish: Dish, now: datetime) -> None:
        """Chặn đặt món khi món không ACTIVE hoặc đã ngoài khung giờ đón món."""
        if dish.status != DishStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Món ăn hiện không còn mở bán",
            )
        if not (dish.pickup_start_time <= now.time() <= dish.pickup_end_time):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hiện không nằm trong khung giờ đón món của quán",
            )

    async def _persist_order(
        self,
        *,
        consumer_id: uuid.UUID,
        dish: Dish,
        payload: OrderCreate,
        unit_price: Decimal,
        co2_saved_kg: Decimal,
        green_points_earned: int,
        current_time: datetime,
    ) -> Order:
        """Insert the order, retrying a few times when the random code collides.

        Immutable dish fields are captured before the loop: a rollback (needed
        when `order_code` collides) expires every instance in the session, and
        touching an expired ORM attribute from sync code would blow up with
        `MissingGreenlet`. The pickup deadline is the end of today's pickup
        window on the dish.
        """
        dish_id = dish.id
        store_id = dish.store_id
        pickup_deadline = datetime.combine(current_time.date(), dish.pickup_end_time, tzinfo=UTC)
        for attempt in range(1, ORDER_CODE_MAX_ATTEMPTS + 1):
            try:
                return await self.orders.create_order(
                    {
                        "order_code": self._generate_order_code(current_time),
                        "consumer_id": consumer_id,
                        "store_id": store_id,
                        "dish_id": dish_id,
                        "quantity": payload.quantity,
                        "unit_price": unit_price,
                        "total_amount": unit_price * payload.quantity,
                        "payment_method": payload.payment_method,
                        "co2_saved_kg": co2_saved_kg,
                        "green_points_earned": green_points_earned,
                        "pickup_deadline": pickup_deadline,
                    }
                )
            except IntegrityError:
                # order_code is UNIQUE — regenerate and retry (statistically rare).
                await self.db.rollback()
                logger.warning(
                    "Order code collision on attempt %d/%d", attempt, ORDER_CODE_MAX_ATTEMPTS
                )
                # Rollback expires every instance in the identity map; reload the
                # dish so the caller never trips over a sync lazy-load later.
                reloaded_dish = await self.db.get(Dish, dish_id)
                if reloaded_dish is not None:
                    await self.db.refresh(reloaded_dish)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Không sinh được mã đơn hàng duy nhất, vui lòng thử lại",
        )

    @staticmethod
    def _generate_order_code(now: datetime) -> str:
        """Mã đơn hiển thị `EB-YYYYMMDD-<8 ký tự hash>` (vd: EB-20260330-A1B2C3D4)."""
        return f"EB-{now:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"
