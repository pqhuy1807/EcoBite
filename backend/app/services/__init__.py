"""Business Logic Layer (Services) for EcoBite Platform.

All domain business rules, orchestration, and coordination live in this package,
decoupling HTTP endpoints in `app.api` from persistence in `app.repositories`.
"""

from app.services import (
    allergen_filter_service,
    auth,
    discovery,
    dish_service,
    gamification_service,
    order_service,
    payment_service,
    qr_service,
    quick_post_service,
    user,
)
from app.services.allergen_filter_service import AllergenHardFilterService
from app.services.gamification_service import GamificationService
from app.services.payment_service import PaymentService
from app.services.quick_post_service import QuickPostService

__all__ = [
    "AllergenHardFilterService",
    "GamificationService",
    "PaymentService",
    "QuickPostService",
    "allergen_filter_service",
    "auth",
    "dish_service",
    "discovery",
    "gamification_service",
    "order_service",
    "payment_service",
    "qr_service",
    "quick_post_service",
    "user",
]
