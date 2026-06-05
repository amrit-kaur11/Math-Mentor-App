from agents.state import GraphState
from agents.rag import retrieve_context
from agents.memory import get_similar_past_problems, get_recent_history

def intent_router_node(state: GraphState):
    # Retrieve RAG context and Memory context based on the topic and parsed problem
    rag_context = retrieve_context(state["parsed_problem"])
    memory_context = get_similar_past_problems(state.get("topic", "general"))
    chat_history = get_recent_history(limit=5)
    
    combined_context = f"{chat_history}\n\n{memory_context}\n\n### RAG KB Context:\n{rag_context}"
    return {"retrieved_context": combined_context}
