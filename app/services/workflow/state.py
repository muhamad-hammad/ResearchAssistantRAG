from typing import TypedDict, Annotated, Optional
import operator

class GraphState(TypedDict):
    """
    Represents the state of our LangGraph state machine.
    """
    paper_id: str
    mode: str          # 'chat', 'explain', or 'visualize'
    message: Optional[str]  # The user's query (mainly for 'chat')
    
    # Context retrieved from FAISS
    context: str
    
    # Generated response (Text or JSON-string depending on mode)
    response: str
    
    # Error message if something fails (e.g., paper not found)
    error: Optional[str]
