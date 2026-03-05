from fastapi import FastAPI, Depends
from .routers import auth
from . import models
from .database import engine
from .dependencies import get_current_user

app = FastAPI(title="Research Assistant API")

app.include_router(auth.router)

@app.get("/api/protected")
def protected_route(current_user: models.User = Depends(get_current_user)):
    return {"message": "You have access to this protected route!", "user_email": current_user.email}

@app.get("/")
def root():
    return {"message": "Welcome to the Research Assistant API. Check /docs."}
