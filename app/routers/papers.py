from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import shutil

from app.database import get_db
from app.models import Paper, User
from app.schemas import PaperResponse
from app.dependencies import get_current_user
from app.worker import process_pdf_task

router = APIRouter(
    prefix="/api/papers",
    tags=["papers"],
    responses={404: {"description": "Not found"}},
)

UPLOAD_DIR = "uploads"

@router.post("/upload", response_model=PaperResponse)
async def upload_paper(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Create DB record
    new_paper = Paper(
        user_id=current_user.id,
        title=file.filename,
        status="pending",
        chunk_count=0
    )
    db.add(new_paper)
    db.commit()
    db.refresh(new_paper)

    # Save file locally (AWS S3 alternative path to be added here if needed)
    file_path = os.path.join(UPLOAD_DIR, f"{new_paper.id}.pdf")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Dispatch to Celery Background Worker Queue
    process_pdf_task.delay(str(new_paper.id), file_path, current_user.id)

    return new_paper

@router.get("", response_model=List[PaperResponse])
def get_papers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    papers = db.query(Paper).filter(Paper.user_id == current_user.id).all()
    return papers

@router.get("/{paper_id}/status")
def get_paper_status(paper_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {"status": paper.status}
