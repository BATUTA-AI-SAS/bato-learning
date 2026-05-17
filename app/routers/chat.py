"""Tutor chat. SSE stream of token deltas plus a final usage event."""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..db import SessionDep
from ..models import Module
from ..repos import chat as chat_repo
from ..repos import modules as modules_repo
from ..repos import progress as progress_repo
from ..services.deepseek_client import stream_chat
from ..services.context_builder import build_payload
from ..services.tutor_filter import FilterState, filter_chunk, flush

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatBody(BaseModel):
    module_id: int
    message: str
    editor_code: str | None = None


def _sse(event: str, payload: dict) -> bytes:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n".encode()


@router.post("")
async def post_chat(body: ChatBody, session: SessionDep):
    mod = await session.get(Module, body.module_id)
    if mod is None:
        raise HTTPException(status_code=404, detail="módulo no encontrado")
    # ensure full module (body_md) is loaded
    mod_full = await modules_repo.get_by_slug(session, mod.slug)
    if mod_full is None:
        raise HTTPException(status_code=404, detail="módulo no encontrado")

    user = await progress_repo.get_or_create_user(session)
    chat_session = await chat_repo.get_or_create_session(
        session, user_id=user.id, module_id=mod_full.id
    )
    chat_session = await chat_repo.get_session_with_messages(session, chat_session.id)
    assert chat_session is not None

    # persist user turn first so the next call sees it
    await chat_repo.append_message(
        session, session_id=chat_session.id, role="user", content_md=body.message
    )

    system_str, messages = await build_payload(
        session,
        module=mod_full,
        user_id=user.id,
        history=chat_session.messages,
        new_user_text=body.message,
        editor_code=body.editor_code,
    )

    async def gen():
        text_acc = ""
        final_usage = None
        final_cost = 0.0
        fstate = FilterState()
        async for chunk in stream_chat(system=system_str, messages=messages):
            if chunk.text:
                filtered = filter_chunk(chunk.text, fstate)
                if filtered:
                    text_acc += filtered
                    yield _sse("delta", {"text": filtered})
            if chunk.done:
                # Flush any dangling open block or pending text.
                tail = flush(fstate)
                if tail:
                    text_acc += tail
                    yield _sse("delta", {"text": tail})
                final_usage = chunk.usage or {}
                final_cost = chunk.cost_usd
                yield _sse(
                    "done",
                    {"usage": final_usage, "cost_usd": round(final_cost, 6)},
                )
        # persist assistant turn after stream completes — filtered text only
        await chat_repo.append_message(
            session,
            session_id=chat_session.id,
            role="assistant",
            content_md=text_acc,
            tokens_in=(final_usage or {}).get("input_tokens", 0),
            tokens_out=(final_usage or {}).get("output_tokens", 0),
            tokens_cache_read=(final_usage or {}).get("cache_read_input_tokens", 0),
            tokens_cache_write=(final_usage or {}).get("cache_creation_input_tokens", 0),
            cost_usd=final_cost,
        )

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/{module_id}/history")
async def history(module_id: int, session: SessionDep):
    user = await progress_repo.get_or_create_user(session)
    cs = await chat_repo.get_or_create_session(
        session, user_id=user.id, module_id=module_id
    )
    full = await chat_repo.get_session_with_messages(session, cs.id)
    if full is None:
        return {"messages": []}
    return {
        "messages": [
            {"role": m.role, "content": m.content_md, "ts": m.created_at.isoformat()}
            for m in full.messages
            if m.role in ("user", "assistant")
        ]
    }
