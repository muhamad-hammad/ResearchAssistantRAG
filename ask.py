import argparse
import sys
from app.services.rag_chain import generate_answer

def main():
    parser = argparse.ArgumentParser(description="Query the RAG system using local FAISS and LLM Factory.")
    parser.add_argument("paper_id", type=str, help="The ID of the paper to query (e.g., 100)")
    parser.add_argument("question", type=str, help="The question to ask about the paper")
    parser.add_argument("--stream", action="store_true", help="Enable token streaming output")
    
    args = parser.parse_args()
    
    print(f"\n--- Asking question about Paper {args.paper_id} ---")
    print(f"Question: {args.question}")
    
    try:
        if args.stream:
            print("\nAnswer (Streaming):")
            response_stream, docs = generate_answer(args.paper_id, args.question, streaming=True)
            for chunk in response_stream:
                print(chunk.content, end="", flush=True)
            print() # Print final newline
            
        else:
            print("\nGenerating Answer...")
            answer, docs = generate_answer(args.paper_id, args.question, streaming=False)
            print("\nAnswer:")
            print(answer)
            
        print("\n--- Sources ---")
        for i, doc in enumerate(docs, 1):
            # Print a snippet of the chunk for verification
            snippet = doc.page_content.replace('\n', ' ')[:150]
            print(f"[Chunk {i}]: {snippet}...")
            
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
