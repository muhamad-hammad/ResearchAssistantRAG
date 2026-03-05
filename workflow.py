import argparse
import sys
import json
from app.services.workflow.graph import build_graph

def main():
    parser = argparse.ArgumentParser(description="Test the LangGraph Workflow Orchestrator.")
    parser.add_argument("--paper", type=str, required=True, help="The ID of the paper to process (e.g., 100)")
    parser.add_argument("--mode", type=str, required=True, choices=["chat", "explain", "visualize"], help="The mode of operation")
    parser.add_argument("--message", type=str, default="", help="The user's question (required for chat mode)")
    
    args = parser.parse_args()
    
    if args.mode == "chat" and not args.message:
        print("Error: --message is required when --mode is 'chat'", file=sys.stderr)
        sys.exit(1)
        
    print(f"\n--- Running Workflow Orchestrator ---")
    print(f"Paper ID: {args.paper}")
    print(f"Mode:     {args.mode}")
    if args.mode == "chat":
        print(f"Message:  {args.message}")
        
    # 1. Initialize Graph
    graph = build_graph()
    
    # 2. Build initial state
    initial_state = {
        "paper_id": args.paper,
        "mode": args.mode,
        "message": args.message,
        "context": "",
        "response": "",
        "error": None
    }
    
    print("\nExecuting graph...")
    try:
        # 3. Run the state machine
        final_state = graph.invoke(initial_state)
        
        # 4. Handle errors if any arose during retrieval or parsing
        if final_state.get("error"):
            print(f"\n[ERROR] Graph Execution Failed: {final_state['error']}")
            if final_state.get('response'):
                print(f"Raw response was: {final_state['response']}")
            sys.exit(1)
            
        print("\n=== Final Response ===")
        
        # 5. Format output based on mode
        if args.mode in ["explain", "visualize"]:
            # Pretty-print structured JSON
            raw_json = final_state["response"]
            try:
                parsed_json = json.loads(raw_json)
                print(json.dumps(parsed_json, indent=2))
            except json.JSONDecodeError:
                print("Warning: Output is not valid JSON!")
                print(raw_json)
        else:
            # Print plain text for chat
            print(final_state["response"])
            
    except Exception as e:
        print(f"\n[FATAL] Unhandled exception during graph execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
