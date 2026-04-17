import json
import re
from langchain_core.prompts import ChatPromptTemplate
from app.services.rag_chain import load_faiss_index, format_docs
from app.services.llm_factory import get_llm, invoke_with_retry
from app.services.workflow.state import GraphState
from openai import PermissionDeniedError, AuthenticationError, BadRequestError

def retrieve_node(state: GraphState) -> GraphState:
    """
    Loads FAISS index and retrieves entire context or chunks depending on mode.
    Since explain/visualize need broader context, we return top k=5 or simply
    return a wide retrieval. For chat, we return top k=3 based on the message.
    """
    paper_id = state.get("paper_id")
    mode = state.get("mode")
    message = state.get("message", "")

    try:
        vector_store = load_faiss_index(paper_id)
        
        # If mode is chat, search by query. Otherwise, try to fetch a broad context
        # (FAISS similarity search requires a query string. For explain/visualize, 
        # we can pass a generic summarization prompt to get chunks)
        if mode == "chat" and message:
            retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            docs = retriever.invoke(message)
        else:
            # For explain/visualize, we retrieve 5 chunks using a generic query
            retriever = vector_store.as_retriever(search_kwargs={"k": 5})
            docs = retriever.invoke("academic paper problem statement methodology results summary")
            
        state["context"] = format_docs(docs)
        state["error"] = None
        
    except FileNotFoundError:
        state["error"] = f"Paper ID {paper_id} not found in vector store."
        state["context"] = ""
        
    return state

def chat_node(state: GraphState) -> GraphState:
    """Standard RAG Chat Q&A."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert academic research assistant. Use the provided context to answer the user's question. Always cite sources where appropriate using [Chunk X]."),
        ("human", "Context:\n{context}\n\nQuestion: {question}")
    ])
    
    prompt_val = prompt.format_prompt(context=state["context"], question=state["message"])
    response = invoke_with_retry(llm, prompt_val.to_messages())
    
    state["response"] = response.content
    return state

def extract_json(text: str) -> str:
    """Defensive JSON extractor: strips markdown fences and slices first { to last }."""
    text = text.strip()
    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    # Slice from the first '{' to the last '}' to handle nested objects
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return text

def explain_node(state: GraphState) -> GraphState:
    """Extracts structured JSON explaining the paper."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert AI researcher. Based on the provided context chunks from a paper, extract a structured analysis. "
                   "You MUST return ONLY a valid JSON object with EXACTLY these 6 keys: "
                   "'problem_statement', 'key_contributions', 'methodology', 'results', 'limitations', 'eli5'. "
                   "Do NOT wrap the JSON in markdown blocks. Just output raw JSON."),
        ("human", "Context:\n{context}")
    ])
    
    prompt_val = prompt.format_prompt(context=state["context"])
    response = invoke_with_retry(llm, prompt_val.to_messages())
    
    # Defensive JSON parsing
    cleaned_json = extract_json(response.content)
    try:
        # Validate that we actually got JSON
        json.loads(cleaned_json)
        state["response"] = cleaned_json
    except json.JSONDecodeError:
        state["error"] = "Failed to parse 'explain' JSON from LLM response."
        state["response"] = cleaned_json # Still keep it so the user sees what failed
        
    return state

def visualize_node(state: GraphState) -> GraphState:
    """Extracts structured JSON for a knowledge graph (nodes & edges)."""
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at mapping academic concepts. Based on the provided context chunks, map the relationships between key concepts. "
                   "You MUST return ONLY a valid JSON object with EXACTLY two array keys: 'nodes' and 'edges'. "
                   "A node is exactly: {{\"id\": \"concept_name\", \"label\": \"Concept Name\"}}. "
                   "An edge is exactly: {{\"source\": \"concept1_id\", \"target\": \"concept2_id\", \"label\": \"relationship description\"}}. "
                   "Do NOT wrap the JSON in markdown blocks. Just output raw JSON."),
        ("human", "Context:\n{context}")
    ])
    
    prompt_val = prompt.format_prompt(context=state["context"])
    response = invoke_with_retry(llm, prompt_val.to_messages())
    
    cleaned_json = extract_json(response.content)
    try:
        json.loads(cleaned_json)
        state["response"] = cleaned_json
    except json.JSONDecodeError:
        state["error"] = "Failed to parse 'visualize' JSON from LLM response."
        state["response"] = cleaned_json
        
    return state
