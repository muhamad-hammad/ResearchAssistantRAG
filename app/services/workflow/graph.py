from langgraph.graph import StateGraph, END
from app.services.workflow.state import GraphState
from app.services.workflow.nodes import retrieve_node, chat_node, explain_node, visualize_node

def route_request(state: GraphState) -> str:
    """
    Conditional edge routing: Decides which node to go to next based on state['mode'],
    or ends the graph if there is an error.
    """
    if state.get("error"):
        return END
        
    mode = state.get("mode")
    if mode == "chat":
        return "chat"
    elif mode == "explain":
        return "explain"
    elif mode == "visualize":
        return "visualize"
        
    # Default fallback
    state["error"] = f"Unknown mode: {mode}"
    return END

def build_graph():
    """Builds and compiles the LangGraph state machine."""
    workflow = StateGraph(GraphState)
    
    # 1. Add all nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("explain", explain_node)
    workflow.add_node("visualize", visualize_node)
    
    # 2. Set the entry point
    workflow.set_entry_point("retrieve")
    
    # 3. Add conditional routing from the retrieval node
    workflow.add_conditional_edges(
        "retrieve",
        route_request,
        {
            "chat": "chat",
            "explain": "explain",
            "visualize": "visualize",
            END: END
        }
    )
    
    # 4. Tie all final nodes to the END of the graph
    workflow.add_edge("chat", END)
    workflow.add_edge("explain", END)
    workflow.add_edge("visualize", END)
    
    # Compile and return the executable app
    return workflow.compile()
