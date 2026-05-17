"""Same loop, expressed as a LangGraph StateGraph — for side-by-side comparison."""

from typing import Annotated, Any, TypedDict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..settings import settings

router = APIRouter()


class RunRequest(BaseModel):
    prompt: str


class RunResponse(BaseModel):
    final_text: str
    iterations: int


@router.post("/loop", response_model=RunResponse)
def run_loop(req: RunRequest) -> RunResponse:
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=400, detail="ANTHROPIC_API_KEY not set")

    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage
    from langchain_core.tools import tool
    from langgraph.graph import END, START, StateGraph
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt import ToolNode, tools_condition

    @tool
    def sql_query(query: str) -> str:
        """Run a read-only SQL-like query against a mock warehouse."""
        return "mocked result: 12 invoices, total 48210.00 EUR"

    class State(TypedDict):
        messages: Annotated[list, add_messages]

    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=settings.anthropic_api_key,
    ).bind_tools([sql_query])

    def model_node(state: State) -> dict[str, Any]:
        return {"messages": [llm.invoke(state["messages"])]}

    g = StateGraph(State)
    g.add_node("model", model_node)
    g.add_node("tools", ToolNode([sql_query]))
    g.add_edge(START, "model")
    g.add_conditional_edges("model", tools_condition)
    g.add_edge("tools", "model")
    app_graph = g.compile()

    result = app_graph.invoke({"messages": [HumanMessage(content=req.prompt)]})
    final = result["messages"][-1].content
    if isinstance(final, list):
        final = "".join(part.get("text", "") for part in final if isinstance(part, dict))
    return RunResponse(final_text=final, iterations=len(result["messages"]))
