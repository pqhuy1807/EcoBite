"""Business Logic Layer (Services) for EcoBite Platform.

All domain business rules, orchestration, and coordination live in this package,
decoupling HTTP endpoints in `app.api` from persistence in `app.repositories`.
"""

from app.services import (
    auth,
    discovery,
    dish_service,
    order_service,
    payment_service,
    qr_service,
    user,
)
from app.services.payment_service import PaymentService

__all__ = [
    "PaymentService",
    "auth",
    "dish_service",
    "discovery",
    "order_service",
    "payment_service",
    "qr_service",
    "user",
]
