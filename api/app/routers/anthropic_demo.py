"""Minimal tool-loop demo against the Anthropic SDK.

The endpoint here intentionally mirrors the loop shown in module 00 of the curriculum,
so a learner can hit it from the site and inspect the trace in Phoenix.
"""

from typing import Any

from anthropic import Anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..settings import settings

router = APIRouter()


class RunRequest(BaseModel):
    prompt: str
    max_iters: int = 6


class Step(BaseModel):
    kind: str
    payload: dict[str, Any]


class RunResponse(BaseModel):
    final_text: str
    steps: list[Step]
    usage: dict[str, int]


TOOLS = [
    {
        "name": "sql_query",
        "description": "Run a read-only SQL-like query against a mock warehouse.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    }
]


def _mock_tool(name: str, args: dict[str, Any]) -> str:
    if name == "sql_query":
        return "mocked result: 12 invoices, total 48210.00 EUR"
    return f"unknown tool {name}"


@router.post("/loop", response_model=RunResponse)
def run_loop(req: RunRequest) -> RunResponse:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not set")

    client = Anthropic(api_key=settings.anthropic_api_key)
    messages: list[dict[str, Any]] = [{"role": "user", "content": req.prompt}]
    steps: list[Step] = [Step(kind="user", payload={"text": req.prompt})]
    totals = {"input_tokens": 0, "output_tokens": 0}

    for _ in range(req.max_iters):
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        totals["input_tokens"] += resp.usage.input_tokens
        totals["output_tokens"] += resp.usage.output_tokens

        if resp.stop_reason == "end_turn":
            text = "".join(b.text for b in resp.content if b.type == "text")
            steps.append(Step(kind="final", payload={"text": text}))
            return RunResponse(final_text=text, steps=steps, usage=totals)

        messages.append({"role": "assistant", "content": resp.content})
        tool_results: list[dict[str, Any]] = []
        for block in resp.content:
            if block.type == "tool_use":
                steps.append(
                    Step(
                        kind="tool_use",
                        payload={"name": block.name, "input": block.input, "id": block.id},
                    )
                )
                result = _mock_tool(block.name, block.input)
                steps.append(
                    Step(
                        kind="tool_result",
                        payload={"name": block.name, "result": result, "id": block.id},
                    )
                )
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )
        messages.append({"role": "user", "content": tool_results})

    raise HTTPException(status_code=500, detail="max iterations reached")
