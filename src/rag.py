import json
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
    enable_logging: bool = True,
    language: str = "English"
):
    # Retrieve top 25 chunks
    retrieved_docs = retrieve_similar_chunks(user_query, collection, top_k=25)
    
    # Assign unique chunk IDs so the LLM can precisely cite what it actually uses
    context_parts = []
    for i, doc in enumerate(retrieved_docs):
        doc["chunk_id"] = i
        context_parts.append(
            f"<source id='{i}' url='{doc.get('url', '')}' file='{doc.get('source_file', '')}' "
            f"page='{doc.get('page', '')}' is_vault='{doc.get('is_vault', False)}'>\n"
            f"{doc['text']}\n</source>"
        )
    context_str = "\n\n".join(context_parts)
    
    # Bulletproof language detection
    french_indicators = ["le", "la", "les", "un", "une", "des", "pour", "est", "comment", "congé", "maternité", "québec", "quoi", "qui", "maladie", "invalidité", "employé"]
    is_french = (language.lower() in ["french", "fr"]) or any(w in user_query.lower().split() for w in french_indicators)
    
    lang_rule = "RÉPONDEZ ENTIÈREMENT EN FRANÇAIS." if is_french else "ANSWER ENTIRELY IN ENGLISH."
    v_empty = "Aucune réponse pertinente trouvée." if is_french else "No relevant answer found."

    system_instruction = "You are a practical HR & Payroll Assistant for Quebec employers. You operate strictly in JSON mode."

    full_prompt = f"""<context>\n{context_str}\n</context>

USER QUERY: {user_query}

=========================================
STRICT INSTRUCTIONS FOR YOUR OUTPUT:
1. LANGUAGE: {lang_rule} Ignore all other languages.
2. PRIORITIZATION (VAULT FIRST): 
   - Prioritize answering the query using ONLY the Internal Vault Documents (is_vault='True'). 
   - IF the Internal Vault completely answers the question, STOP, provide your answer, and ignore all other Web/External contexts.
   - IF the Internal Vault does NOT fully answer the question, THEN use the Web contexts (is_vault='False').
3. SINGLE ANSWER: Provide ONE cohesive answer. Do not split it into "Vault" and "Web" sections.
4. EXACT CITATIONS: Only include a source ID in your `used_source_ids` list if you directly extracted facts from it. If a document contains no relevant data, ignore it completely.
5. FORMAT: Output ONLY a valid JSON object. No markdown wrappers.
   Schema: 
   {{
       "answer": "Your comprehensive answer here. Max 3 bullet points. Keep it brief and focused on practical obligations.",
       "used_source_ids": [0, 3, 5] 
   }}
=========================================
"""

    for model in FALLBACK_MODELS:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,  
                        top_p=0.90,
                        response_mime_type="application/json"
                    )
                )
                
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()
                
                try:
                    data = json.loads(raw_text)
                    answer = data.get("answer", v_empty)
                    used_ids = data.get("used_source_ids", [])
                    
                    # ONLY return the sources the LLM explicitly declared as useful
                    filtered_docs = [doc for doc in retrieved_docs if doc["chunk_id"] in used_ids]
                    
                except Exception as parse_error:
                    answer = f"⚠️ Format Error: The model failed to format the response.\n\nRaw Text:\n{raw_text}"
                    filtered_docs = []
                
                if enable_logging:
                    try:
                        log_session_event(
                            session_id,
                            user_query,
                            [d.get('url') or d.get('source_file') for d in filtered_docs],
                            answer
                        )
                    except Exception:
                        pass

                return answer, filtered_docs

            except (errors.APIError, errors.ClientError) as e:
                err_str = str(e)
                if "503" in err_str or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "UNAVAILABLE" in err_str:
                    delay = (2 ** attempt) * 3 + random.uniform(1, 3)
                    time.sleep(delay)
                else:
                    break

    return "❌ Unable to generate response.", []