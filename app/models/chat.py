"""Chat tutor: one session per (user, module). Messages with token + cost telemetry."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ..db import Base


class ChatSession(Base):
    __tablename__ = "chat_session"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("module.id", ondelete="CASCADE"), index=True
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.id"
    )


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_session.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | system
    content_md: Mapped[str] = mapped_column(Text)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    tokens_cache_read: Mapped[int] = mapped_column(Integer, default=0)
    tokens_cache_write: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")
