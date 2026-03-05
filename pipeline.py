import os
import argparse
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Paper, User

# Configure where FAISS indexes will be saved
VECTOR_STORE_DIR = "vector_stores"
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

# Define embedding model explicitly (allenai-specter)
EMBEDDING_MODEL_NAME = "sentence-transformers/allenai-specter"

def extract_text_from_pdf(pdf_path: str) -> str:
    print(f"Extracting text from {pdf_path}...")
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def chunk_text(text: str):
    print("Chunking text logically...")
    # Using RecursiveCharacterTextSplitter for intelligent section chunking
    # We aim for ~1000 characters per chunk with some overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_embeddings():
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}. This may take a while on first run...")
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

def build_faiss_index(chunks, paper_id: str):
    print(f"Building FAISS index for {len(chunks)} chunks...")
    embeddings = get_embeddings()
    
    # We store the paper_id in metadata so we know where chunks came from
    metadatas = [{"source": paper_id} for _ in chunks]
    vector_store = FAISS.from_texts(chunks, embeddings, metadatas=metadatas)
    
    index_path = os.path.join(VECTOR_STORE_DIR, f"faiss_index_{paper_id}")
    vector_store.save_local(index_path)
    print(f"FAISS index saved to {index_path}")
    return len(chunks)

def update_db(user_id: int, paper_id: str, title: str, chunk_count: int):
    print("Updating database with paper information...")
    db: Session = SessionLocal()
    try:
        # For standalone script, we just create the paper directly
        # Ensure user exists for FK constraint (We'll use user_id 1 for testing)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"User ID {user_id} not found. Creating a dummy test user.")
            user = User(id=user_id, email="test_pipeline@t.com", hashed_password="dummy")
            db.add(user)
            db.commit()

        paper = Paper(
            id=int(paper_id) if paper_id.isdigit() else 1, # Dummy ID generation
            user_id=user_id,
            title=title,
            status="ready",
            chunk_count=chunk_count
        )
        db.add(paper)
        db.commit()
        print(f"Database updated! Paper '{title}' stored with {chunk_count} chunks.")
    finally:
        db.close()

def run_pipeline(pdf_path: str):
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    # Basic setup for standalone test run
    file_name = os.path.basename(pdf_path)
    paper_title = os.path.splitext(file_name)[0]
    # For testing, we use a simple generic ID (like 100)
    paper_id = "100" 
    user_id = 1

    text = extract_text_from_pdf(pdf_path)
    if not text.strip():
        print("No text could be extracted from this PDF.")
        return

    chunks = chunk_text(text)
    
    chunk_count = build_faiss_index(chunks, paper_id)
    
    update_db(user_id, paper_id, paper_title, chunk_count)
    print("Pipeline completed successfully!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the standalone PDF to FAISS pipeline.")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file to process.")
    args = parser.parse_args()
    
    run_pipeline(args.pdf_path)
