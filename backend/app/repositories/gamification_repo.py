"""Repository for Gamification persistence: GreenPointsLedger, Voucher, and UserVoucher."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gamification import GreenPointsLedger, PointActionType, UserVoucher, Voucher
from app.models.order import Order, OrderStatus
from app.models.user import User


class GamificationRepository:
    """Async data access layer for Green Points, vouchers, and environmental stats."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a User directly from the database with up-to-date balance."""
        stmt = select(User).where(User.id == user_id).execution_options(populate_existing=True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def atomic_deduct_points(
        self,
        user_id: uuid.UUID,
        point_cost: int,
        *,
        commit: bool = False,
    ) -> int | None:
        """Atomically deduct green points to prevent negative balances under concurrency.

        Executes:
            UPDATE users
            SET green_points_balance = green_points_balance - :point_cost
            WHERE id = :user_id AND green_points_balance >= :point_cost
            RETURNING green_points_balance

        Returns the updated balance on success, or None if point_cost <= 0, the user
        does not exist, or the user does not have enough points.
        """
        if point_cost <= 0:
            return None

        stmt = (
            update(User)
            .where(
                User.id == user_id,
                User.green_points_balance >= point_cost,
            )
            .values(green_points_balance=User.green_points_balance - point_cost)
            .returning(User.green_points_balance)
            .execution_options(synchronize_session=False)
        )
        result = await self.db.execute(stmt)
        new_balance = result.scalar_one_or_none()

        if new_balance is None:
            return None

        if commit:
            await self.db.commit()
        else:
            await self.db.flush()

        # Keep any already-loaded User instance in this session synchronized.
        cached_user = await self.db.get(User, user_id)
        if cached_user is not None:
            await self.db.refresh(cached_user)

        return int(new_balance)

    async def get_ledger_by_user(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[GreenPointsLedger]:
        """List green points ledger entries for a user, newest first."""
        stmt = (
            select(GreenPointsLedger)
            .where(GreenPointsLedger.user_id == user_id)
            .order_by(GreenPointsLedger.created_at.desc(), GreenPointsLedger.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_ledger_entry(
        self,
        *,
        user_id: uuid.UUID,
        points_change: int,
        balance_after: int,
        action_type: PointActionType,
        co2_saved_kg: Decimal = Decimal("0.00"),
        order_id: uuid.UUID | None = None,
        note: str | None = None,
        commit: bool = False,
    ) -> GreenPointsLedger:
        """Persist a GreenPointsLedger record."""
        entry = GreenPointsLedger(
            user_id=user_id,
            order_id=order_id,
            points_change=points_change,
            balance_after=balance_after,
            action_type=action_type,
            co2_saved_kg=co2_saved_kg,
            note=note,
        )
        self.db.add(entry)
        if commit:
            await self.db.commit()
            await self.db.refresh(entry)
        else:
            await self.db.flush()
        return entry

    async def get_completed_rescue_stats(self, user_id: uuid.UUID) -> tuple[Decimal, int]:
        """Return (total_co2_saved_kg, total_meals_saved) across COMPLETED orders."""
        stmt = select(
            func.coalesce(func.sum(Order.co2_saved_kg), Decimal("0.00")),
            func.coalesce(func.sum(Order.quantity), 0),
        ).where(
            Order.consumer_id == user_id,
            Order.status == OrderStatus.COMPLETED,
        )
        result = await self.db.execute(stmt)
        total_co2_raw, total_meals_raw = result.one()
        total_co2 = Decimal(str(total_co2_raw)).quantize(Decimal("0.01"))
        return total_co2, int(total_meals_raw)

    async def get_voucher_by_id(self, voucher_id: uuid.UUID) -> Voucher | None:
        """Retrieve a catalog Voucher by primary key."""
        stmt = select(Voucher).where(Voucher.id == voucher_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_available_vouchers(self, *, now: datetime | None = None) -> list[Voucher]:
        """List active, unexpired vouchers ordered by ascending points_required."""
        resolved_now = now if now is not None else datetime.now(UTC)
        stmt = (
            select(Voucher)
            .where(
                Voucher.is_active.is_(True),
                Voucher.expires_at > resolved_now,
            )
            .order_by(Voucher.points_required.asc(), Voucher.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_vouchers(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[UserVoucher]:
        """List vouchers claimed by a user, newest first, with catalog details loaded."""
        stmt = (
            select(UserVoucher)
            .where(UserVoucher.user_id == user_id)
            .options(selectinload(UserVoucher.voucher))
            .order_by(UserVoucher.claimed_at.desc(), UserVoucher.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_user_voucher(
        self,
        user_id: uuid.UUID,
        voucher_id: uuid.UUID,
        *,
        commit: bool = False,
    ) -> UserVoucher:
        """Create a claimed UserVoucher record."""
        user_voucher = UserVoucher(
            user_id=user_id,
            voucher_id=voucher_id,
            is_used=False,
        )
        self.db.add(user_voucher)
        if commit:
            await self.db.commit()
            await self.db.refresh(user_voucher)
        else:
            await self.db.flush()
        return user_voucher
