import os
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Paper
from app.services.llm_factory import get_ollama_llm # Might need it if embeddings fail
from langchain_community.embeddings import HuggingFaceEmbeddings

VECTOR_STORE_DIR = "vector_stores"
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
EMBEDDING_MODEL_NAME = "sentence-transformers/allenai-specter"

def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def chunk_text(text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

def build_faiss_index(chunks, paper_id: str):
    embeddings = get_embeddings()
    metadatas = [{"source": paper_id} for _ in chunks]
    vector_store = FAISS.from_texts(chunks, embeddings, metadatas=metadatas)
    
    index_path = os.path.join(VECTOR_STORE_DIR, f"faiss_index_{paper_id}")
    vector_store.save_local(index_path)
    return len(chunks)

def process_pdf_sync(paper_id: str, pdf_path: str, user_id: int):
    """
    Synchronously extracts text, chunks it, builds FAISS index, and updates DB.
    For Sprint 5, this blocks the API. Sprint 6 will move this to Celery.
    """
    db: Session = SessionLocal()
    try:
        # Fetch the paper record created by the router
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return

        print(f"Starting processing for paper {paper_id}")
        text = extract_text_from_pdf(pdf_path)
        
        if not text.strip():
            print("No text extracted.")
            paper.status = "failed"
            db.commit()
            return
            
        chunks = chunk_text(text)
        chunk_count = build_faiss_index(chunks, str(paper_id))
        
        # Update DB record with success
        paper.status = "ready"
        paper.chunk_count = chunk_count
        db.commit()
        print(f"Processing complete for {paper_id}. {chunk_count} chunks generated.")
    except Exception as e:
        print(f"Error processing paper {paper_id}: {e}")
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if paper:
            paper.status = "failed"
            db.commit()
    finally:
        db.close()
