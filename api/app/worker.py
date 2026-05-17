"""Temporal worker — run with: `uv run python -m app.worker`."""

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from .activities.agent import ingest_data, persist_output, run_agent
from .settings import settings
from .telemetry import setup_tracing
from .workflows.audit import AuditTenantWorkflow


async def main() -> None:
    setup_tracing()
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[AuditTenantWorkflow],
        activities=[ingest_data, run_agent, persist_output],
    )
    print(f"[worker] connected to {settings.temporal_address}, queue={settings.temporal_task_queue}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
