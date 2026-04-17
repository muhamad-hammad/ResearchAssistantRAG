from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.dependencies import get_current_user
from app.models import User
from app.schemas import ChatRequest
from app.services.workflow.graph import build_graph
from app.services.rag_chain import generate_answer
import json
import asyncio

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)

# Instantiate the compiled graph once
graph = build_graph()

@router.post("/stream")
async def chat_stream(request: ChatRequest, current_user: User = Depends(get_current_user)):
    try:
        # Step 1: Load FAISS index + retrieve docs synchronously in a thread (blocking I/O)
        loop = asyncio.get_event_loop()
        response_stream, _ = await loop.run_in_executor(
            None, lambda: generate_answer(request.paper_id, request.message, True)
        )

        async def token_generator():
            try:
                async for chunk in response_stream:
                    if chunk.content:
                        yield f"data: {json.dumps({'event': 'token', 'data': chunk.content})}\n\n"
                yield f"data: {json.dumps({'event': 'end'})}\n\n"
            except Exception as stream_err:
                yield f"data: {json.dumps({'event': 'error', 'data': str(stream_err)})}\n\n"

        return StreamingResponse(token_generator(), media_type="text/event-stream")

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
    
    # graph.invoke is synchronous. Run in thread so event loop stays unblocked.
    final_state = await asyncio.to_thread(graph.invoke, initial_state)
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
    
    # graph.invoke is synchronous. Run in thread so event loop stays unblocked.
    final_state = await asyncio.to_thread(graph.invoke, initial_state)
    if final_state.get("error"):
        raise HTTPException(status_code=400, detail=final_state["error"])
        
    try:
        return json.loads(final_state["response"])
    except json.JSONDecodeError:
        return {"raw_response": final_state["response"]}
