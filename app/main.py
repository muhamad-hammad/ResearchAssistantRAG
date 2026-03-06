from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from .routers import auth, papers, chat
from . import models
from .database import engine
from .dependencies import get_current_user


def _warm_embeddings():
    """Pre-loads the HuggingFace embedding model into memory at startup."""
    try:
        from .services.rag_chain import get_embeddings
        get_embeddings()
        print("✅ Embedding model warmed up and ready.")
    except Exception as e:
        print(f"⚠️ Could not pre-warm embeddings: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the heavy embedding model in a background thread so auth routes
    # are never blocked by a 30-second model load on the first request.
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _warm_embeddings)
    yield


app = FastAPI(title="Research Assistant API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(papers.router)
app.include_router(chat.router)


@app.get("/api/protected")
def protected_route(current_user: models.User = Depends(get_current_user)):
    return {"message": "You have access to this protected route!", "user_email": current_user.email}


@app.get("/")
def root():
    return {"message": "Welcome to the Research Assistant API. Check /docs."}
