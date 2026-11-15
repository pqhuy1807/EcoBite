"""Business logic for food rescue orders: stock locking, green impact, cancellation.

Complies strictly with:
- Guardrail #4: Redis distributed lock and atomic SQL inventory updates.
- Guardrail #5: Rule-based time-shifted pricing only.
"""

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import distributed_lock
from app.models.dish import Dish, DishStatus
from app.models.order import Order, OrderStatus
from app.models.user import User, UserRole
from app.repositories import dish_repo
from app.repositories.order_repo import OrderRepository
from app.repositories.qr_token_repo import QRTokenRepository
from app.schemas.order import (
    OrderCreate,
    OrderDetailResponse,
    OrderResponse,
    QRPayloadResponse,
    QRVerificationResponse,
)
from app.services.dish_service import DishService
from app.services.qr_service import QRService

logger = logging.getLogger(__name__)

try:
    VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
except ZoneInfoNotFoundError:
    from datetime import timedelta, timezone
    VIETNAM_TZ = timezone(timedelta(hours=7))

DISH_LOCK_KEY_TEMPLATE = "lock:dish:{dish_id}"

ORDER_CODE_MAX_ATTEMPTS = 3

GREEN_POINTS_PER_CO2_KG = 10

CANCELLABLE_STATUSES: tuple[OrderStatus, ...] = (
    OrderStatus.CONFIRMED,
    OrderStatus.READY_FOR_PICKUP,
)


def _ensure_utc(value: datetime) -> datetime:
    """Treat naive database datetimes as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _ensure_vietnam_input_utc(value: datetime) -> datetime:
    """Interpret naive input datetimes as Vietnam local time, then convert to UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=VIETNAM_TZ)
    return value.astimezone(UTC)


def _to_vietnam_local(value: datetime) -> datetime:
    """Convert a datetime to naive Vietnam local time for TIME comparisons."""
    if value.tzinfo is None:
        return value
    return value.astimezone(VIETNAM_TZ).replace(tzinfo=None)


class OrderService:
    """Coordinate rescue orders from placement through to cancellation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.orders = OrderRepository(db)
        self.qr_tokens = QRTokenRepository(db)

    async def create_rescue_order(
        self,
        consumer_id: uuid.UUID,
        payload: OrderCreate,
        *,
        now: datetime | None = None,
    ) -> Order:
        """Create a rescue order with atomic inventory and order persistence."""

        current_time = (
            _to_vietnam_local(now)
            if now is not None
            else datetime.now(VIETNAM_TZ).replace(tzinfo=None)
        )

        # 1. Retrieve dish and validate its availability.
        dish = await dish_repo.get_by_id(self.db, payload.dish_id)

        if dish is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dish not found",
            )

        self._validate_dish_sellable(dish, current_time)

        # 2. Calculate rule-based discounted price.
        unit_price, _, _ = DishService.calculate_time_shifted_discount(
            original_price=dish.original_price,
            pickup_start_time=dish.pickup_start_time,
            pickup_end_time=dish.pickup_end_time,
            override_discounted_price=dish.override_discounted_price,
            rule_discount_start_time=dish.rule_discount_start_time,
            current_time=current_time,
        )

        # Capture immutable values before any transaction rollback.
        dish_id = dish.id
        store_id = dish.store_id
        estimated_co2_per_dish = dish.estimated_co2_kg_per_dish
        pickup_end_time = dish.pickup_end_time

        # 3. Keep the distributed lock until stock and order are committed.
        async with distributed_lock(DISH_LOCK_KEY_TEMPLATE.format(dish_id=dish_id)):
            for attempt in range(1, ORDER_CODE_MAX_ATTEMPTS + 1):
                updated_dish: Dish | None = None
                try:
                    updated_dish = await dish_repo.atomic_decrement_quantity(
                        self.db,
                        dish_id,
                        payload.quantity,
                        commit=False,
                    )

                    if updated_dish is None:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Món ăn đã hết suất hoặc số lượng còn lại không đủ",
                        )

                    # 4. Calculate environmental impact and Green Points.
                    co2_saved_kg = (Decimal(payload.quantity) * estimated_co2_per_dish).quantize(
                        Decimal("0.01")
                    )

                    green_points_earned = int(co2_saved_kg * GREEN_POINTS_PER_CO2_KG)

                    # 5. Create the order and commit both changes together.
                    order = await self._persist_order(
                        consumer_id=consumer_id,
                        dish_id=dish_id,
                        store_id=store_id,
                        pickup_end_time=pickup_end_time,
                        payload=payload,
                        unit_price=unit_price,
                        co2_saved_kg=co2_saved_kg,
                        green_points_earned=green_points_earned,
                        current_time=current_time,
                    )

                    await self.db.commit()
                    await self.db.refresh(order)
                    loaded_order = await self.orders.get_by_id(order.id)
                    return loaded_order or order

                except IntegrityError as exc:
                    if updated_dish is not None:
                        await self.db.rollback()
                        await self.db.refresh(updated_dish)
                    logger.warning(
                        "Order code collision on attempt %d/%d",
                        attempt,
                        ORDER_CODE_MAX_ATTEMPTS,
                    )
                    if attempt == ORDER_CODE_MAX_ATTEMPTS:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail="Không sinh được mã đơn hàng duy nhất, vui lòng thử lại",
                        ) from exc
                except HTTPException:
                    if updated_dish is not None:
                        await self.db.rollback()
                        await self.db.refresh(updated_dish)
                    raise
                except Exception:
                    if updated_dish is not None:
                        await self.db.rollback()
                        await self.db.refresh(updated_dish)
                    logger.exception("Failed to create rescue order")
                    raise

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Không sinh được mã đơn hàng duy nhất, vui lòng thử lại",
        )

    async def cancel_order(
        self,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        now: datetime | None = None,
    ) -> Order:
        """Cancel an order and restore its inventory in one transaction."""

        order = await self.orders.get_by_id(order_id)

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # 1. Check cancellation permissions.
        is_consumer_owner = order.consumer_id == user_id
        is_store_owner = order.store.owner_id == user_id

        if not (is_consumer_owner or is_store_owner):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền hủy đơn hàng này",
            )

        # Capture values before transaction changes.
        dish_id = order.dish_id
        order_quantity = order.quantity
        order_status_value = order.status.value

        # 2. Check pickup deadline when a timestamp is supplied.
        if now is not None:
            current_time_utc = _ensure_vietnam_input_utc(now)
            pickup_deadline_utc = _ensure_utc(order.pickup_deadline)

            if current_time_utc > pickup_deadline_utc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Đã quá hạn chót lấy món, đơn hàng không thể hủy",
                )

        # 3. Serialize stock restoration with order creation.
        async with distributed_lock(DISH_LOCK_KEY_TEMPLATE.format(dish_id=dish_id)):
            cancelled: Order | None = None
            try:
                # Change order status without committing.
                cancelled = await self.orders.cancel_if_allowed(
                    order_id,
                    CANCELLABLE_STATUSES,
                    commit=False,
                )

                if cancelled is None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Đơn hàng ở trạng thái {order_status_value} không thể hủy",
                    )

                # Restore stock without committing.
                restored = await dish_repo.atomic_increment_quantity(
                    self.db,
                    dish_id,
                    order_quantity,
                    commit=False,
                )

                if restored is None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Không thể hoàn lại số lượng món ăn",
                    )

                # Commit cancellation and stock restoration together.
                await self.db.commit()
                await self.db.refresh(cancelled)
                loaded_order = await self.orders.get_by_id(order_id)
                return loaded_order or cancelled
            except HTTPException:
                if cancelled is not None:
                    await self.db.rollback()
                    await self.db.refresh(order)
                raise
            except Exception:
                if cancelled is not None:
                    await self.db.rollback()
                    await self.db.refresh(order)
                logger.exception("Failed to cancel order %s", order_id)
                raise

    async def get_my_orders(
        self,
        consumer_id: uuid.UUID,
        *,
        order_status: OrderStatus | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:
        """Return paginated order history placed by consumer."""
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
        """Return paginated orders belonging to a store."""
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
        """Fetch order details with role-based access and QR visibility checks."""

        order = await self.orders.get_by_id(order_id)

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        if not self._can_view_order(order, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xem đơn hàng này",
            )

        current_time = _ensure_vietnam_input_utc(now) if now is not None else datetime.now(UTC)

        detail = OrderDetailResponse.model_validate(order)

        if not self._is_valid_qr_token_for_order(order, current_time):
            detail.qr_token = None

        return detail

    async def issue_or_get_qr_payload(
        self,
        order_id: uuid.UUID,
        current_user: User,
        *,
        now: datetime | None = None,
    ) -> QRPayloadResponse:
        """Issue or retrieve the canonical signed pickup QR payload for an active order."""
        order = await self.orders.get_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        if order.consumer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xem mã QR của đơn hàng này",
            )

        if order.status not in CANCELLABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Đơn hàng ở trạng thái {order.status.value} không thể tạo mã QR",
            )

        current_time = _ensure_vietnam_input_utc(now) if now is not None else datetime.now(UTC)
        pickup_deadline_utc = _ensure_utc(order.pickup_deadline)
        if current_time > pickup_deadline_utc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Đã quá hạn chót lấy món, mã QR không còn hiệu lực",
            )

        qr_service = QRService(self.db)
        existing_token = await self.qr_tokens.get_by_order_id(order.id)
        if existing_token is not None:
            if existing_token.is_used:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Mã QR đã được sử dụng trước đó!",
                )
            expires_at_utc = _ensure_utc(existing_token.expires_at)
            if expires_at_utc < current_time:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Mã QR đã hết hạn sử dụng",
                )
            expires_at_raw = expires_at_utc.isoformat().replace("+00:00", "Z")
            qr_payload = qr_service.build_qr_payload_string(
                order_id=order.id,
                user_id=order.consumer_id,
                nonce=existing_token.nonce,
                expires_at_raw=expires_at_raw,
                signature=existing_token.token_hash,
            )
            return QRPayloadResponse(
                order_id=order.id,
                order_code=order.order_code,
                qr_payload=qr_payload,
                nonce=existing_token.nonce,
                expires_at=expires_at_utc,
                is_used=existing_token.is_used,
            )

        qr_payload = await qr_service.generate_order_qr_token(
            order_id=order.id,
            user_id=order.consumer_id,
            pickup_deadline=pickup_deadline_utc,
            commit=True,
        )
        created_token = await self.qr_tokens.get_by_order_id(order.id)
        if created_token is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Không thể khởi tạo mã QR cho đơn hàng",
            )
        return QRPayloadResponse(
            order_id=order.id,
            order_code=order.order_code,
            qr_payload=qr_payload,
            nonce=created_token.nonce,
            expires_at=_ensure_utc(created_token.expires_at),
            is_used=created_token.is_used,
        )

    async def verify_and_complete_order(
        self,
        qr_payload: str,
        current_user: User,
        *,
        now: datetime | None = None,
    ) -> QRVerificationResponse:
        """Verify a pickup QR token and complete the corresponding order."""

        current_time = _ensure_vietnam_input_utc(now) if now is not None else datetime.now(UTC)

        qr_service = QRService(self.db)

        # 1. Verify QR signature and expiration.
        qr_token = await qr_service.verify_qr_token(
            qr_payload,
            now=current_time,
        )

        # 2. Retrieve the associated order.
        order = await self.orders.get_by_id(qr_token.order_id)

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )

        # 3. Verify consumer ID in the QR payload.
        parsed = qr_service.parse_qr_payload(qr_payload)

        if order.consumer_id != parsed.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã QR không khớp với dữ liệu đơn hàng",
            )

        # 4. Verify store ownership.
        if current_user.role != UserRole.STORE_PARTNER or order.store.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xác thực đơn hàng của cửa hàng này",
            )

        # 5. Validate order status.
        if order.status == OrderStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Đơn hàng đã được hoàn tất trước đó",
            )

        if order.status not in CANCELLABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(f"Đơn hàng ở trạng thái {order.status.value} " "không thể nhận món"),
            )

        order_id = order.id
        token_id = qr_token.id
        current_status_value = order.status.value

        # 6. Mark token as used and complete order in one transaction.
        async with distributed_lock(
            f"lock:order:redeem:{order_id}",
            timeout_seconds=5,
        ):
            try:
                marked_token = await self.qr_tokens.mark_token_as_used(
                    token_id,
                    used_at=current_time,
                    commit=False,
                )

                if marked_token is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Mã QR đã được sử dụng trước đó!",
                    )

                completed_order = await self.orders.complete_if_allowed(
                    order_id,
                    CANCELLABLE_STATUSES,
                    completed_at=current_time,
                    commit=False,
                )

                if completed_order is None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Đơn hàng ở trạng thái {current_status_value} không thể nhận món",
                    )

                await self.db.commit()
                await self.db.refresh(completed_order)

            except Exception:
                await self.db.rollback()
                raise

        return QRVerificationResponse(
            success=True,
            order_id=completed_order.id,
            order_code=completed_order.order_code,
            status=completed_order.status,
            points_awarded=completed_order.green_points_earned,
            co2_saved_kg=completed_order.co2_saved_kg,
            message=(
                "Xác thực chữ ký hợp lệ! Đã giao món ăn thành công " "và cộng điểm xanh cho khách."
            ),
            order=OrderResponse.model_validate(completed_order),
        )

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
    def _is_valid_qr_token_for_order(
        order: Order,
        current_time: datetime,
    ) -> bool:
        """Check whether QR metadata can be exposed to the client."""

        qr_token = order.qr_token

        if qr_token is None or qr_token.is_used:
            return False

        if order.status not in CANCELLABLE_STATUSES:
            return False

        return _ensure_utc(qr_token.expires_at) >= current_time

    @staticmethod
    def _validate_dish_sellable(
        dish: Dish,
        now: datetime,
    ) -> None:
        """Reject dishes that are inactive or outside their pickup window."""

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
        dish_id: uuid.UUID,
        store_id: uuid.UUID,
        pickup_end_time,
        payload: OrderCreate,
        unit_price: Decimal,
        co2_saved_kg: Decimal,
        green_points_earned: int,
        current_time: datetime,
    ) -> Order:
        """Create an order record inside the caller's active transaction."""

        pickup_deadline_local = datetime.combine(
            current_time.date(),
            pickup_end_time,
        ).replace(tzinfo=VIETNAM_TZ)

        pickup_deadline_utc = pickup_deadline_local.astimezone(UTC)

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
                "pickup_deadline": pickup_deadline_utc,
            },
            commit=False,
        )

    @staticmethod
    def _generate_order_code(now: datetime) -> str:
        """Generate an order code in EB-YYYYMMDD-XXXXXXXX format."""

        return f"EB-{now:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"
