"""DeepSeek tutor chat client via OpenAI-compatible API.

Uses the official `openai` SDK pointed at DeepSeek's base URL.
Yields StreamChunk deltas followed by a final chunk with usage + cost.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

from openai import AsyncOpenAI

from ..settings import settings

# Per-million-token USD pricing for deepseek-chat (cache-miss prices).
_PRICE_PER_M = {
    "input": 0.27,
    "output": 1.10,
}


@dataclass
class StreamChunk:
    text: str = ""
    done: bool = False
    usage: dict | None = None
    cost_usd: float = 0.0


def _client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


def _estimate_cost(usage: dict) -> float:
    if not usage:
        return 0.0
    cost = (
        usage.get("input_tokens", 0) * _PRICE_PER_M["input"]
        + usage.get("output_tokens", 0) * _PRICE_PER_M["output"]
    )
    return cost / 1_000_000.0


async def stream_chat(
    *,
    system: str,
    messages: list[dict],
    model: str | None = None,
    max_tokens: int | None = None,
) -> AsyncIterator[StreamChunk]:
    """Stream token deltas from DeepSeek, then yield a final chunk with usage."""
    if not settings.deepseek_api_key:
        yield StreamChunk(
            text="(DEEPSEEK_API_KEY no configurado; el chat tutor está desactivado.)",
            done=True,
        )
        return

    client = _client()
    final_usage: dict = {}

    stream = await client.chat.completions.create(
        model=model or settings.deepseek_model,
        max_tokens=max_tokens or settings.deepseek_max_tokens,
        messages=[{"role": "system", "content": system}, *messages],
        stream=True,
        stream_options={"include_usage": True},
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield StreamChunk(text=chunk.choices[0].delta.content)
        if chunk.usage is not None:
            final_usage = {
                "input_tokens": chunk.usage.prompt_tokens,
                "output_tokens": chunk.usage.completion_tokens,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            }

    yield StreamChunk(done=True, usage=final_usage, cost_usd=_estimate_cost(final_usage))
