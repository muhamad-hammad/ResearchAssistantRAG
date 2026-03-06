import os
from celery import Celery
from app.services.pdf_pipeline import process_pdf_sync

# Set default broker and backend to local Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "research_assistant_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="process_pdf_task")
def process_pdf_task(paper_id: str, pdf_path: str, user_id: int):
    """
    Celery background task for processing the PDF.
    This runs asynchronously in a detached worker process, so the main API
    returns immediately.
    """
    print(f"Celery picked up task for paper {paper_id}")
    try:
        # Our pdf_pipeline is synchronous DB code, which plays nicely with Celery.
        process_pdf_sync(paper_id, pdf_path, user_id)
        return {"status": "success", "paper_id": paper_id}
    except Exception as e:
        print(f"Celery Task Failed for paper {paper_id}: {e}")
        return {"status": "error", "error": str(e)}
