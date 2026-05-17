"""User model — singleton for local use, multi-user when auth is active."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func, text

from ..db import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Legacy field kept for back-compat with old rows; display_name replaces it.
    name: Mapped[str] = mapped_column(String(64), default="tú")
    display_name: Mapped[str] = mapped_column(String(64), default="tú")
    email: Mapped[str | None] = mapped_column(String(120), unique=True, index=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("1"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
