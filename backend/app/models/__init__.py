"""ORM models aggregated for Alembic autogenerate and `Base.metadata`.

Add one import line per new model module here.
"""

from app.db.base import Base
from app.models.user import User, UserRole

__all__ = ["Base", "User", "UserRole"]
