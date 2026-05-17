"""Chat persistence: sessions per (user, module) + messages."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import ChatMessage, ChatSession


async def get_or_create_session(
    session: AsyncSession, *, user_id: int, module_id: int
) -> ChatSession:
    res = await session.execute(
        select(ChatSession).where(
            ChatSession.user_id == user_id, ChatSession.module_id == module_id
        )
    )
    chat = res.scalar_one_or_none()
    if chat is None:
        chat = ChatSession(user_id=user_id, module_id=module_id)
        session.add(chat)
        await session.commit()
        await session.refresh(chat)
    return chat


async def get_session_with_messages(
    session: AsyncSession, session_id: int
) -> ChatSession | None:
    res = await session.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id)
        .options(selectinload(ChatSession.messages))
    )
    return res.scalar_one_or_none()


async def append_message(
    session: AsyncSession,
    *,
    session_id: int,
    role: str,
    content_md: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    tokens_cache_read: int = 0,
    tokens_cache_write: int = 0,
    cost_usd: float = 0.0,
) -> ChatMessage:
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content_md=content_md,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        tokens_cache_read=tokens_cache_read,
        tokens_cache_write=tokens_cache_write,
        cost_usd=cost_usd,
    )
    session.add(msg)
    await session.commit()
    return msg
