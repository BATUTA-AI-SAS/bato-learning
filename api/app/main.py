from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import anthropic_demo, langgraph_demo, temporal_demo
from .telemetry import setup_tracing


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_tracing()
    yield


app = FastAPI(title="bato-learning-api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(anthropic_demo.router, prefix="/labs/anthropic", tags=["anthropic"])
app.include_router(langgraph_demo.router, prefix="/labs/langgraph", tags=["langgraph"])
app.include_router(temporal_demo.router, prefix="/workflows", tags=["temporal"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
