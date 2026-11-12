"""Consumer food-rescue order endpoints: placement and cancellation."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import DBSession, require_roles
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderResponse
from app.services.order_service import OrderService

router = APIRouter()


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
