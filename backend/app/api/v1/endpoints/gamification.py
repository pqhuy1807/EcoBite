"""Gamification endpoints: Green Points summary, voucher catalog, and voucher redemption."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DBSession, require_roles
from app.models.user import User, UserRole
from app.schemas.gamification import (
    GreenPointsSummaryResponse,
    UserVoucherResponse,
    VoucherRedeemResponse,
    VoucherResponse,
)
from app.services.gamification_service import GamificationService

router = APIRouter()

SkipQuery = Annotated[int, Query(ge=0, description="Số bản ghi bỏ qua để phân trang")]
LimitQuery = Annotated[
    int,
    Query(ge=1, le=100, description="Số bản ghi tối đa mỗi trang (1-100)"),
]


@router.get("/green-points/me", response_model=GreenPointsSummaryResponse)
async def get_my_green_points(
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.CONSUMER)),
    ],
    limit: LimitQuery = 20,
) -> GreenPointsSummaryResponse:
    """Tra cứu số dư Điểm Xanh, tổng lượng CO2 đã cứu, danh hiệu và lịch sử gần nhất."""
    return await GamificationService(db).get_my_green_points(
        current_user.id,
        ledger_limit=limit,
    )


@router.get("/vouchers", response_model=list[VoucherResponse])
async def list_available_vouchers(db: DBSession) -> list[VoucherResponse]:
    """Liệt kê danh sách voucher đang hoạt động và còn hạn đổi bằng Điểm Xanh."""
    vouchers = await GamificationService(db).list_available_vouchers()
    return [VoucherResponse.model_validate(voucher) for voucher in vouchers]


# Static /vouchers/me route MUST stay ahead of parameterized /vouchers/{voucher_id}/... routes.
@router.get("/vouchers/me", response_model=list[UserVoucherResponse])
async def list_my_vouchers(
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.CONSUMER)),
    ],
    skip: SkipQuery = 0,
    limit: LimitQuery = 20,
) -> list[UserVoucherResponse]:
    """Liệt kê các voucher mà người dùng hiện tại đã đổi bằng Điểm Xanh."""
    user_vouchers = await GamificationService(db).list_my_vouchers(
        current_user.id,
        skip=skip,
        limit=limit,
    )
    return [UserVoucherResponse.model_validate(uv) for uv in user_vouchers]


@router.post(
    "/vouchers/{voucher_id}/redeem",
    status_code=status.HTTP_200_OK,
    response_model=VoucherRedeemResponse,
)
async def redeem_voucher(
    voucher_id: uuid.UUID,
    db: DBSession,
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.CONSUMER)),
    ],
) -> VoucherRedeemResponse:
    """Đổi Điểm Xanh lấy voucher: trừ điểm nguyên tử, ghi sổ cái và cấp voucher."""
    return await GamificationService(db).redeem_voucher(current_user.id, voucher_id)
