"""Data Access Layer (Repositories) for EcoBite Platform.

All direct SQLAlchemy 2.0 AsyncSession queries and mutations live in this package,
decoupling database persistence from domain business rules in `app.services`.
"""

from app.repositories import dish_repo, menu_repo, store_repo, user_repo

__all__ = [
    "dish_repo",
    "menu_repo",
    "store_repo",
    "user_repo",
]
