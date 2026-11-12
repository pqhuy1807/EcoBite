"""Food-rescue order endpoints: placement, history, detail lookup and cancellation."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DBSession, StoreOwner, require_roles
from app.models.order import OrderStatus
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderDetailResponse, OrderResponse
from app.services.order_service import OrderService

router = APIRouter()

OrderStatusQuery = Annotated[
    OrderStatus | None,
    Query(alias="status", description="Lọc theo trạng thái đơn hàng"),
]
SkipQuery = Annotated[int, Query(ge=0, description="Số bản ghi bỏ qua để phân trang")]
LimitQuery = Annotated[
    int,
    Query(ge=1, le=100, description="Số bản ghi tối đa mỗi trang (1-100)"),
]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
async def place_rescue_order(
    payload: OrderCreate,
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.CONSUMER)),
    ],
) -> OrderResponse:
    """Đặt đơn giải cứu: trừ kho nguyên tử và tính tác động xanh (Guardrail #4 & #5)."""
    order = await OrderService(db).create_rescue_order(current_user.id, payload)
    return OrderResponse.model_validate(order)


# Static /me and /store/{store_id} routes MUST stay ahead of /{order_id}
# so FastAPI matches them before attempting UUID conversion on /{order_id}.
@router.get("/me", response_model=list[OrderResponse])
async def list_my_orders(
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.CONSUMER)),
    ],
    order_status: OrderStatusQuery = None,
    skip: SkipQuery = 0,
    limit: LimitQuery = 20,
) -> list[OrderResponse]:
    """Lấy lịch sử đơn giải cứu của người dùng hiện tại (phân trang, lọc theo status)."""
    orders = await OrderService(db).get_my_orders(
        current_user.id,
        order_status=order_status,
        skip=skip,
        limit=limit,
    )
    return [OrderResponse.model_validate(order) for order in orders]


@router.get("/store/{store_id}", response_model=list[OrderResponse])
async def list_store_orders(
    store_id: uuid.UUID,
    db: DBSession,
    _: StoreOwner,
    order_status: OrderStatusQuery = None,
    skip: SkipQuery = 0,
    limit: LimitQuery = 20,
) -> list[OrderResponse]:
    """Lấy danh sách đơn hàng của cửa hàng (chỉ chủ quán sở hữu cửa hàng)."""
    orders = await OrderService(db).get_store_orders(
        store_id,
        order_status=order_status,
        skip=skip,
        limit=limit,
    )
    return [OrderResponse.model_validate(order) for order in orders]


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order_detail(
    order_id: uuid.UUID,
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.CONSUMER, UserRole.STORE_PARTNER, UserRole.ADMIN)),
    ],
) -> OrderDetailResponse:
    """Xem chi tiết một đơn hàng và thông tin QR hợp lệ (kiểm tra quyền sở hữu/admin)."""
    return await OrderService(db).get_order_detail(order_id, current_user)


@router.patch("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_rescue_order(
    order_id: uuid.UUID,
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.CONSUMER, UserRole.STORE_PARTNER)),
    ],
) -> OrderResponse:
    """Hủy đơn trước hạn chót lấy món: hoàn kho nguyên tử, chống hoàn kép (Guardrail #4)."""
    order = await OrderService(db).cancel_order(order_id, current_user.id, now=datetime.now())
    return OrderResponse.model_validate(order)
