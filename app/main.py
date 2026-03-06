from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, papers, chat
from . import models
from .database import engine
from .dependencies import get_current_user

app = FastAPI(title="Research Assistant API")

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
