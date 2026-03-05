import argparse
import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

VECTOR_STORE_DIR = "vector_stores"
EMBEDDING_MODEL_NAME = "sentence-transformers/allenai-specter"

def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

def query_faiss(paper_id: str, question: str):
    index_path = os.path.join(VECTOR_STORE_DIR, f"faiss_index_{paper_id}")
    if not os.path.exists(index_path):
        print(f"FAISS index not found at {index_path}. Did you run the pipeline first?")
        return
    
    print(f"Loading FAISS index for paper {paper_id}...")
    embeddings = get_embeddings()
    vector_store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    
    print(f"Querying: '{question}'")
    # Retrieve top 3 relevant chunks
    docs = vector_store.similarity_search(question, k=3)
    
    print(f"--- Found {len(docs)} Relevant Chunks ---")
    for i, doc in enumerate(docs, 1):
        print(f"\n[Chunk {i}]")
        print(doc.page_content)
        print("-" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query a FAISS index.")
    parser.add_argument("paper_id", type=str, help="ID of the paper to query (e.g., 100)")
    parser.add_argument("question", type=str, help="Question to ask the index")
    args = parser.parse_args()
    
    query_faiss(args.paper_id, args.question)
