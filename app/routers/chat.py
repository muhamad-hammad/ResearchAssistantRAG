from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.dependencies import get_current_user
from app.models import User
from app.schemas import ChatRequest
from app.services.workflow.graph import build_graph
from app.services.rag_chain import generate_answer
import json

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)

# Instantiate the compiled graph once
graph = build_graph()

@router.post("/stream")
async def chat_stream(request: ChatRequest, current_user: User = Depends(get_current_user)):
    try:
        # Use existing rag_chain to support simple token streaming
        response_stream, _ = generate_answer(request.paper_id, request.message, streaming=True)
        
        def token_generator():
            for chunk in response_stream:
                yield chunk.content
                
        return StreamingResponse(token_generator(), media_type="text/plain")
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Paper index not found. Has it finished processing?")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/explain")
async def chat_explain(request: ChatRequest, current_user: User = Depends(get_current_user)):
    initial_state = {
        "paper_id": request.paper_id,
        "mode": "explain",
        "message": "",
        "context": "",
        "response": "",
        "error": None
    }
    
    final_state = graph.invoke(initial_state)
    if final_state.get("error"):
        raise HTTPException(status_code=400, detail=final_state["error"])
        
    try:
        return json.loads(final_state["response"])
    except json.JSONDecodeError:
        return {"raw_response": final_state["response"]}

@router.post("/visualize")
async def chat_visualize(request: ChatRequest, current_user: User = Depends(get_current_user)):
    initial_state = {
        "paper_id": request.paper_id,
        "mode": "visualize",
        "message": "",
        "context": "",
        "response": "",
        "error": None
    }
    
    final_state = graph.invoke(initial_state)
    if final_state.get("error"):
        raise HTTPException(status_code=400, detail=final_state["error"])
        
    try:
        return json.loads(final_state["response"])
    except json.JSONDecodeError:
        return {"raw_response": final_state["response"]}
