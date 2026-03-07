import os
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Create a custom exception if we need to wrap specific provider errors
class LLMRateLimitError(Exception):
    pass

# Retry decorator: retries up to 3 times, waiting 2^x seconds between retries (2s, 4s...)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception, LLMRateLimitError)),
    reraise=True
)
def invoke_with_retry(llm, messages):
    """
    Invokes the LLM with the provided messages, applying exponential backoff retries.
    """
    return llm.invoke(messages)


def get_llm(streaming=False):
    """
    Factory function to get the appropriate LLM based on environment variables.
    Supports 'gemini' (free API via OpenAI-compatible endpoint) and 'ollama'.
    Defaults to 'gemini'.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found. Falling back to Ollama.")
            return get_ollama_llm(streaming)
        return ChatOpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            streaming=streaming
        )

    elif provider == "ollama":
        return get_ollama_llm(streaming)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

def get_ollama_llm(streaming=False):
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
    return ChatOllama(
        model=model_name,
        streaming=streaming
    )
