"""Trigger the AuditTenantWorkflow from the lab UI."""

from temporalio.client import Client
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..settings import settings
from ..workflows.audit import AuditTenantWorkflow

router = APIRouter()


class TriggerRequest(BaseModel):
    tenant_id: str
    period: str


class TriggerResponse(BaseModel):
    workflow_id: str
    run_id: str
    ui_url: str


@router.post("/audit", response_model=TriggerResponse)
async def trigger_audit(req: TriggerRequest) -> TriggerResponse:
    try:
        client = await Client.connect(
            settings.temporal_address, namespace=settings.temporal_namespace
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"temporal unreachable: {exc}") from exc

    workflow_id = f"audit-{req.tenant_id}-{req.period}"
    handle = await client.start_workflow(
        AuditTenantWorkflow.run,
        args=[req.tenant_id, req.period],
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    return TriggerResponse(
        workflow_id=workflow_id,
        run_id=handle.first_execution_run_id or "",
        ui_url=f"http://localhost:8080/namespaces/{settings.temporal_namespace}/workflows/{workflow_id}",
    )
