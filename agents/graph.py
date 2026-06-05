from langgraph.graph import StateGraph, END
from agents.state import GraphState
from agents.parser import parser_node
from agents.router import intent_router_node
from agents.solver import solver_node
from agents.verifier import verifier_node
from agents.explainer import explainer_node


DEFAULT_MAX_RETRIES = 1


def parser_router(state: GraphState):
    """
    Route after parser.

    If the parser needs clarification, stop the graph so the UI can ask the user.
    Otherwise, continue to the intent router.
    """
    if state.get("needs_clarification"):
        return "needs_clarification"

    return "router"


def verifier_router(state: GraphState):
    """
    Route after verification.

    Rules:
    1. If verified, go to explainer.
    2. If verifier produced a corrected final answer, go to explainer.
    3. If the system is inconsistent, go to explainer.
    4. Retry solver only if retry_needed=True and retry limit has not been exceeded.
    5. Otherwise, stop retrying and go to explainer.
    """

    if state.get("is_verified"):
        return "explainer"

    if state.get("final_answer_override"):
        return "explainer"

    if state.get("verifier_verdict") == "inconsistent_system":
        return "explainer"

    retry_needed = state.get("retry_needed") is True
    retry_count = int(state.get("retry_count") or 0)
    max_retries = int(state.get("max_retries") or DEFAULT_MAX_RETRIES)

    # The verifier increments retry_count before routing.
    # So retry_count <= max_retries means this retry is still allowed.
    if retry_needed and retry_count <= max_retries:
        return "solver"

    return "explainer"


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("parser", parser_node)
    workflow.add_node("router", intent_router_node)
    workflow.add_node("solver", solver_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("explainer", explainer_node)

    workflow.set_entry_point("parser")

    workflow.add_conditional_edges(
        "parser",
        parser_router,
        {
            "needs_clarification": END,
            "router": "router",
        },
    )

    workflow.add_edge("router", "solver")
    workflow.add_edge("solver", "verifier")

    workflow.add_conditional_edges(
        "verifier",
        verifier_router,
        {
            "solver": "solver",
            "explainer": "explainer",
        },
    )

    workflow.add_edge("explainer", END)

    return workflow.compile()