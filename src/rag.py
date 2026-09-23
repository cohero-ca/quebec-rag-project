import time
import random
import warnings
from google.genai.models import Models
from google.genai import types, errors
from src.config import client, LLM_MODEL
from src.vector_store import retrieve_similar_chunks
from src.logger import log_session_event

Models._logged_afc_warning = True
warnings.filterwarnings("ignore", message=".*automatic function calling.*")

FALLBACK_MODELS = [
    LLM_MODEL,                   
    "gemini-3.5-flash-lite",     
    "gemini-3.1-flash-lite"      
]
def generate_rag_response(
    user_query: str, 
    collection, 
    insurer_context: str = "General", 
    session_id: str = "default",
    enable_logging: bool = True  # <--- New parameter
):
    retrieved_docs = retrieve_similar_chunks(user_query, collection, top_k=25)
    
    context_str = "\n\n".join([
        f"<source url='{doc['url']}'>\n{doc['text']}\n</source>"
        for doc in retrieved_docs
    ])
    
    system_instruction = f"""
You are an expert advisor on Quebec insurance regulatory policies and coverage rules.
Use the provided XML context chunks from Quebec insurance websites (RAMQ, AMF, carrier documents) to answer the user's question accurately.

Active Insurer Context: {insurer_context}

Rules:
1. Ground your answers strictly in the provided sources where possible.
2. Clearly distinguish between mandatory provincial laws (e.g., Act A-29.01) and carrier-specific contract options.
3. If information is missing or unclear, state what is known and what needs verification.
"""

    full_prompt = f"""<context>
{context_str}
</context>

User Query: {user_query}"""

    for model in FALLBACK_MODELS:
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                        top_p=0.95
                    )
                )
                
                answer = response.text
                
                # Only log if logging is enabled
                if enable_logging:
                    try:
                        log_session_event(
                            session_id,
                            user_query,
                            [d['url'] for d in retrieved_docs],
                            answer
                        )
                    except Exception:
                        pass

                return answer

            except (errors.APIError, errors.ClientError) as e:
                err_str = str(e)
                if "503" in err_str or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "UNAVAILABLE" in err_str:
                    delay = (2 ** attempt) * 3 + random.uniform(1, 3)
                    print(f"\n⚠️ [{model}] Model busy/rate limited ({err_str[:40]}...). Retrying in {delay:.1f}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)
                else:
                    print(f"❌ API Error: {e}")
                    break

        print(f"⚠️ Model [{model}] unavailable after retries. Trying fallback model...")

    return "❌ Unable to generate response: All Vertex AI model endpoints are currently experiencing high traffic. Please wait a moment and try again."
