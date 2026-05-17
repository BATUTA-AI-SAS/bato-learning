"""Activities — non-deterministic side-effects live here.

Mocked for now; the curriculum's module 07 lab swaps these for real implementations
that call Anthropic / LangGraph / Postgres / etc.
"""

import asyncio
import uuid

from temporalio import activity


@activity.defn
async def ingest_data(tenant_id: str, period: str) -> dict:
    activity.heartbeat({"stage": "ingest"})
    await asyncio.sleep(0.5)
    return {"tenant_id": tenant_id, "period": period, "dataset_id": str(uuid.uuid4())}


@activity.defn
async def run_agent(skill_id: str, tenant_id: str, dataset_id: str) -> dict:
    """Mock that simulates the agent loop. Replace with a real LangGraph invocation."""

    async def heartbeats() -> None:
        while True:
            activity.heartbeat({"status": "thinking"})
            await asyncio.sleep(15)

    task = asyncio.create_task(heartbeats())
    try:
        await asyncio.sleep(1.0)  # pretend the LLM is doing work
        return {
            "skill_id": skill_id,
            "tenant_id": tenant_id,
            "dataset_id": dataset_id,
            "summary": "12 invoices, EUR 48,210; no anomalies.",
            "findings": [],
        }
    finally:
        task.cancel()


@activity.defn
async def persist_output(tenant_id: str, agent_result: dict, idempotency_key: str) -> None:
    activity.heartbeat({"stage": "persist", "key": idempotency_key})
    await asyncio.sleep(0.2)
