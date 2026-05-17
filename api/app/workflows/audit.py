"""Reference workflow — mirrors module 07 of the curriculum exactly.

The workflow code itself must be deterministic: no IO, no random, no datetime.now.
All non-determinism lives in activities.
"""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from ..activities.agent import ingest_data, persist_output, run_agent


@workflow.defn
class AuditTenantWorkflow:
    @workflow.run
    async def run(self, tenant_id: str, period: str) -> dict:
        ingest = await workflow.execute_activity(
            ingest_data,
            args=[tenant_id, period],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        agent = await workflow.execute_activity(
            run_agent,
            args=["monthly_audit", tenant_id, ingest["dataset_id"]],
            start_to_close_timeout=timedelta(minutes=30),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=2),
        )

        await workflow.execute_activity(
            persist_output,
            args=[tenant_id, agent, f"audit:{tenant_id}:{period}"],
            start_to_close_timeout=timedelta(minutes=2),
        )

        return {"tenant_id": tenant_id, "period": period, "agent": agent}
