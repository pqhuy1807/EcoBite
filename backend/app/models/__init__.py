"""ORM models aggregated for Alembic autogenerate and `Base.metadata`.

Every table in the EcoBite platform is registered here.
"""

from app.db.base import Base
from app.models.dish import Dish, DishStatus
from app.models.gamification import (
    GreenPointsLedger,
    PointActionType,
    UserVoucher,
    Voucher,
)
from app.models.interaction import Notification, NotificationType, Review
from app.models.menu_item import DietaryType, ItemCategory, MenuItem
from app.models.order import (
    Order,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    PaymentTransaction,
    QRToken,
)
from app.models.store import KycStatus, Store
from app.models.user import DietaryPreference, User, UserPreference, UserRole

__all__ = [
    "Base",
    "User",
    "UserRole",
    "UserPreference",
    "DietaryPreference",
    "Store",
    "KycStatus",
    "MenuItem",
    "ItemCategory",
    "DietaryType",
    "Dish",
    "DishStatus",
    "Order",
    "OrderStatus",
    "PaymentMethod",
    "PaymentStatus",
    "QRToken",
    "PaymentTransaction",
    "GreenPointsLedger",
    "PointActionType",
    "Voucher",
    "UserVoucher",
    "Review",
    "Notification",
    "NotificationType",
]
