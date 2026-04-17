from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.dependencies import get_current_user
from app.models import User
from app.schemas import ChatRequest
from app.services.workflow.graph import build_graph
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
        # Use asyncio.Queue to bridge sync LLM stream → async SSE generator.
        # generate_answer(streaming=False) runs fully in a thread (sync),
        # we manually stream by calling llm.stream() inside that thread.
        queue: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def run_sync_stream():
            """Runs in a thread: calls sync LLM stream and puts chunks on the queue."""
            try:
                vector_store = __import__('app.services.rag_chain', fromlist=['load_faiss_index', 'format_docs', 'get_embeddings'])
                from app.services.rag_chain import load_faiss_index, format_docs
                from app.services.llm_factory import get_llm
                from langchain_core.prompts import ChatPromptTemplate

                vs = load_faiss_index(request.paper_id)
                docs = vs.as_retriever(search_kwargs={"k": 3}).invoke(request.message)
                context_str = format_docs(docs)

                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are an expert academic research assistant. Use the provided context to answer the user's question. Always cite sources using [Chunk X]."),
                    ("human", "Context:\n{context}\n\nQuestion: {question}")
                ])
                prompt_val = prompt.format_prompt(context=context_str, question=request.message)

                llm = get_llm(streaming=False)  # streaming param unused here; we call .stream() directly
                for chunk in llm.stream(prompt_val.to_messages()):
                    if chunk.content:
                        loop.call_soon_threadsafe(queue.put_nowait, chunk.content)
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel: stream done
            except FileNotFoundError:
                loop.call_soon_threadsafe(queue.put_nowait, "__FNFE__")
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, f"__ERR__{e}")

        async def token_generator():
            # Kick off the sync stream in a thread
            loop.run_in_executor(None, run_sync_stream)
            while True:
                item = await queue.get()
                if item is None:  # sentinel
                    yield f"data: {json.dumps({'event': 'end'})}\n\n"
                    break
                if isinstance(item, str) and item.startswith("__FNFE__"):
                    yield f"data: {json.dumps({'event': 'error', 'data': 'Paper index not found. Has it finished processing?'})}\n\n"
                    break
                if isinstance(item, str) and item.startswith("__ERR__"):
                    yield f"data: {json.dumps({'event': 'error', 'data': item[7:]})}\n\n"
                    break
                yield f"data: {json.dumps({'event': 'token', 'data': item})}\n\n"

        return StreamingResponse(token_generator(), media_type="text/event-stream")

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
