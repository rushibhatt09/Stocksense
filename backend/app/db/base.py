"""Single import point for Alembic: pulls in every model so Base.metadata is complete."""

from app.db.base_class import Base  # noqa: F401
from app.models.inventory import Category, Location, Product, Warehouse  # noqa: F401
from app.models.operations import Document, DocumentLine, StockMove  # noqa: F401
from app.models.user import OtpToken, User  # noqa: F401
