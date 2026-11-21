"""Business logic for Green Points summary, eco ranking, and atomic voucher redemption."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import distributed_lock
from app.models.gamification import PointActionType, UserVoucher, Voucher
from app.repositories.gamification_repo import GamificationRepository
from app.schemas.gamification import (
    GreenPointsLedgerResponse,
    GreenPointsSummaryResponse,
    VoucherRedeemResponse,
)

# Rule-based Eco Rank thresholds (points or equivalent CO2 score: 1 meal = 2.5 kg CO2 = 50 pts).
RANK_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (1000, "Đại Sứ Xanh (Eco Ambassador)"),
    (300, "Chiến Binh Xanh (Eco Hero)"),
    (100, "Người Giải Cứu (Food Rescuer)"),
    (0, "Mầm Xanh (Eco Seedling)"),
)
CO2_KG_TO_SCORE_FACTOR = Decimal("20")


def _as_utc(value: datetime) -> datetime:
    """Normalize datetimes across SQLite (naive UTC) and PostgreSQL (tz-aware)."""
    return value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)


class GamificationService:
    """Orchestrates Green Points balance, environmental impact, and voucher redemption."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = GamificationRepository(db)

    @staticmethod
    def compute_rank_title(
        balance_points: int,
        total_co2_saved_kg: Decimal = Decimal("0.00"),
    ) -> str:
        """Compute deterministic rule-based Eco Rank from points balance and rescued CO2."""
        co2_score = int(max(total_co2_saved_kg, Decimal("0")) * CO2_KG_TO_SCORE_FACTOR)
        effective_score = max(balance_points, co2_score, 0)
        for threshold, title in RANK_THRESHOLDS:
            if effective_score >= threshold:
                return title
        return RANK_THRESHOLDS[-1][1]

    async def get_my_green_points(
        self,
        user_id: uuid.UUID,
        *,
        ledger_limit: int = 20,
    ) -> GreenPointsSummaryResponse:
        """Return user's Green Points balance, CO2 impact, meal count, rank, and recent ledger."""
        user = await self.repo.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng",
            )

        total_co2_saved_kg, total_meals_saved = await self.repo.get_completed_rescue_stats(user_id)
        recent_entries = await self.repo.get_ledger_by_user(user_id, limit=ledger_limit)
        rank_title = self.compute_rank_title(user.green_points_balance, total_co2_saved_kg)

        return GreenPointsSummaryResponse(
            balance_points=user.green_points_balance,
            total_co2_saved_kg=total_co2_saved_kg,
            total_meals_saved=total_meals_saved,
            rank_title=rank_title,
            recent_ledger=[
                GreenPointsLedgerResponse.model_validate(entry) for entry in recent_entries
            ],
        )

    async def list_available_vouchers(self, *, now: datetime | None = None) -> list[Voucher]:
        """List all active and unexpired vouchers available for redemption."""
        resolved_now = _as_utc(now) if now is not None else datetime.now(UTC)
        return await self.repo.list_available_vouchers(now=resolved_now)

    async def list_my_vouchers(
        self,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[UserVoucher]:
        """List vouchers already claimed by a consumer."""
        return await self.repo.get_user_vouchers(user_id, offset=skip, limit=limit)

    async def redeem_voucher(
        self,
        user_id: uuid.UUID,
        voucher_id: uuid.UUID,
        *,
        now: datetime | None = None,
    ) -> VoucherRedeemResponse:
        """Atomically redeem a voucher: validate, deduct points, write ledger, issue voucher."""
        resolved_now = _as_utc(now) if now is not None else datetime.now(UTC)

        async with distributed_lock(f"lock:green_points:user:{user_id}"):
            voucher = await self.repo.get_voucher_by_id(voucher_id)
            if voucher is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy voucher",
                )
            if not voucher.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Voucher hiện không còn hoạt động",
                )
            if _as_utc(voucher.expires_at) <= resolved_now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Voucher đã hết hạn sử dụng",
                )

            try:
                new_balance = await self.repo.atomic_deduct_points(
                    user_id,
                    voucher.points_required,
                    commit=False,
                )
                if new_balance is None:
                    existing_user = await self.repo.get_user_by_id(user_id)
                    if existing_user is None:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Không tìm thấy người dùng",
                        )
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Không đủ Điểm Xanh để đổi voucher này",
                    )

                await self.repo.create_ledger_entry(
                    user_id=user_id,
                    points_change=-voucher.points_required,
                    balance_after=new_balance,
                    action_type=PointActionType.VOUCHER_REDEEM,
                    co2_saved_kg=Decimal("0.00"),
                    note=f"Đổi voucher {voucher.code} (-{voucher.points_required} Điểm Xanh)",
                    commit=False,
                )
                user_voucher = await self.repo.create_user_voucher(
                    user_id=user_id,
                    voucher_id=voucher.id,
                    commit=False,
                )
                await self.db.commit()
                await self.db.refresh(user_voucher)
            except HTTPException:
                raise
            except Exception:
                await self.db.rollback()
                raise

            return VoucherRedeemResponse(
                user_voucher_id=user_voucher.id,
                voucher_id=voucher.id,
                voucher_code=voucher.code,
                title=voucher.title,
                discount_amount=voucher.discount_amount,
                points_deducted=voucher.points_required,
                remaining_balance=new_balance,
                claimed_at=user_voucher.claimed_at,
            )
