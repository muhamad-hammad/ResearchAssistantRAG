import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from .llm_factory import get_llm, invoke_with_retry

VECTOR_STORE_DIR = "vector_stores"
EMBEDDING_MODEL_NAME = "sentence-transformers/allenai-specter"

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert academic research assistant. Use the provided context to answer the user's question. If you don't know the answer or the context doesn't contain the information, simply say you don't know. Always cite your sources by referencing the context chunks where appropriate."),
    ("human", "Context:\n{context}\n\nQuestion: {question}")
])

def get_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

def format_docs(docs):
    formatted = []
    for i, doc in enumerate(docs, 1):
        formatted.append(f"[Chunk {i}]\n{doc.page_content}\n")
    return "\n".join(formatted)

def load_faiss_index(paper_id: str):
    index_path = os.path.join(VECTOR_STORE_DIR, f"faiss_index_{paper_id}")
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found for paper {paper_id}")
    
    embeddings = get_embeddings()
    return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)

def generate_answer(paper_id: str, question: str, streaming: bool = False):
    """
    RAG Pipeline:
    1. Load FAISS Index
    2. Retrieve top-k chunks
    3. Format context
    4. Pass to LLM via prompt
    5. Return output
    """
    vector_store = load_faiss_index(paper_id)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    llm = get_llm(streaming=streaming)
    
    # Retrieve documents to include citations
    docs = retriever.invoke(question)
    context_str = format_docs(docs)

    prompt_val = qa_prompt.format_prompt(context=context_str, question=question)

    # For streaming, we want to return the generator directly instead of the retry wrapper
    # since the retry wrapper fully consumes the result before returning.
    # Retry logic is mainly for non-streaming standard invocations.
    if streaming:
        return llm.stream(prompt_val.to_messages()), docs
        
    # Standard invocation with retry
    response = invoke_with_retry(llm, prompt_val.to_messages())
    return response.content, docs
