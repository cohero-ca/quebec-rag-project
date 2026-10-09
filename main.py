import os
import sys
import re
import tempfile
import uuid
import json
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
import chromadb
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
from google.cloud import storage
from pypdf import PdfReader
import docx
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.drive_manager import get_storage_client

load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT", "gen-lang-client-0426110783")
API_KEY = os.getenv("API_KEY", "")

# Initialize Vertex AI
vertexai.init(project=GCP_PROJECT, location="northamerica-northeast1")
model = GenerativeModel("gemini-3.5-flash")
embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="/home/ubuntu/hr-chatbot-project/chroma_db")
collection = chroma_client.get_or_create_collection(name="quebec_insurance")

app = FastAPI(title="Quebec HR/Insurance 3-Tier RAG API")

def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

def clean_wayback_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    pattern = r"^https?://web\.archive\.org/web/\d+/(https?://.*)$"
    match = re.match(pattern, raw_url)
    if match:
        return match.group(1)
    pattern_simple = r"^https?://web\.archive\.org/web/(https?://.*)$"
    match_simple = re.match(pattern_simple, raw_url)
    if match_simple:
        return match_simple.group(1)
    return raw_url

def get_768d_embeddings(texts: list[str]) -> list[list[float]]:
    inputs = [TextEmbeddingInput(text=t, task_type="RETRIEVAL_DOCUMENT") for t in texts]
    embeddings = []
    batch_size = 50
    for i in range(0, len(inputs), batch_size):
        batch = inputs[i:i + batch_size]
        res = embedding_model.get_embeddings(batch)
        embeddings.extend([e.values for e in res])
    return embeddings

def chunk_text(text: str, chunk_size: int = 1500) -> list[str]:
    # Simple character chunker for Word/Excel texts
    words = text.split()
    chunks = []
    current_chunk = []
    current_len = 0
    for word in words:
        current_chunk.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_len = 0
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

class IngestRequest(BaseModel):
    tenant_id: str
    filename: str
    gcs_uri: str
    category: str = "vault"  # Default to vault, but allows "validated"

class DeleteRequest(BaseModel):
    tenant_id: str
    filename: str

class SyncRequest(BaseModel):
    tenant_id: str
    valid_filenames: list[str]

class QueryRequest(BaseModel):
    query: str
    tenant_id: str = "default"
    include_third_parties: bool = False
    language: str = "English"
    history: Optional[dict] = None

@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- 1. Multi-Format Ingest Endpoint ---
@app.post("/api/rag/ingest", dependencies=[Depends(verify_api_key)])
async def ingest_document(req: IngestRequest):
    try:
        storage_client = get_storage_client()
        bucket_name = req.gcs_uri.replace("gs://", "").split("/")[0]
        blob_name = "/".join(req.gcs_uri.replace("gs://", "").split("/")[1:])
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        ext = req.filename.lower().split(".")[-1]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_file:
            blob.download_to_filename(temp_file.name)
            
            text_chunks, metadatas, ids = [], [], []
            
            if ext == "pdf":
                reader = PdfReader(temp_file.name)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        text_chunks.append(text)
                        metadatas.append({
                            "tenant_id": req.tenant_id,
                            "source_file": req.filename,
                            "page": str(i + 1),
                            "is_tenant_doc": req.category == "vault",
                            "category": req.category
                        })
                        ids.append(f"{req.tenant_id}_{req.filename}_page_{i+1}_{uuid.uuid4().hex[:6]}")
            
            elif ext in ["docx", "doc"]:
                doc = docx.Document(temp_file.name)
                full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                chunks = chunk_text(full_text)
                for i, chunk in enumerate(chunks):
                    text_chunks.append(chunk)
                    metadatas.append({
                        "tenant_id": req.tenant_id,
                        "source_file": req.filename,
                        "page": f"Part {i+1}",
                        "is_tenant_doc": req.category == "vault",
                        "category": req.category
                    })
                    ids.append(f"{req.tenant_id}_{req.filename}_part_{i+1}_{uuid.uuid4().hex[:6]}")
                    
            elif ext in ["xlsx", "xls"]:
                df = pd.read_excel(temp_file.name)
                full_text = df.to_string(index=False)
                chunks = chunk_text(full_text)
                for i, chunk in enumerate(chunks):
                    text_chunks.append(chunk)
                    metadatas.append({
                        "tenant_id": req.tenant_id,
                        "source_file": req.filename,
                        "page": f"Part {i+1}",
                        "is_tenant_doc": req.category == "vault",
                        "category": req.category
                    })
                    ids.append(f"{req.tenant_id}_{req.filename}_part_{i+1}_{uuid.uuid4().hex[:6]}")
                    
            if text_chunks:
                embeddings = get_768d_embeddings(text_chunks)
                collection.add(documents=text_chunks, embeddings=embeddings, metadatas=metadatas, ids=ids)
        
        os.unlink(temp_file.name)
        return {"status": "success", "message": f"Ingested {len(text_chunks)} segments."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

# --- 2. Delete Endpoint ---
@app.post("/api/rag/delete", dependencies=[Depends(verify_api_key)])
async def delete_document(req: DeleteRequest):
    try:
        res = collection.get(where={"tenant_id": {"$eq": req.tenant_id}}, include=["metadatas"])
        ids_to_delete = []
        if res and res.get("ids") and res.get("metadatas"):
            for chunk_id, m in zip(res["ids"], res["metadatas"]):
                if m and (m.get("source_file") == req.filename or m.get("filename") == req.filename):
                    ids_to_delete.append(chunk_id)
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
        return {"status": "success", "deleted_count": len(ids_to_delete)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# --- 3. Vault Sync Endpoint ---
@app.post("/api/rag/sync", dependencies=[Depends(verify_api_key)])
async def sync_vault(req: SyncRequest):
    try:
        res = collection.get(where={"tenant_id": {"$eq": req.tenant_id}}, include=["metadatas"])
        indexed_files = set()
        
        if res and res.get("metadatas"):
            for m in res["metadatas"]:
                if m:
                    file_key = m.get("source_file") or m.get("filename") or m.get("source")
                    if file_key:
                        indexed_files.add(str(file_key).strip())
                    
        valid_set = {str(f).strip() for f in req.valid_filenames}
        orphans = indexed_files - valid_set
        
        for orphan in orphans:
            res_orphan = collection.get(where={"tenant_id": {"$eq": req.tenant_id}}, include=["metadatas"])
            del_ids = [
                cid for cid, m in zip(res_orphan["ids"], res_orphan["metadatas"])
                if m and (m.get("source_file") == orphan or m.get("filename") == orphan)
            ]
            if del_ids:
                collection.delete(ids=del_ids)
            
        matched = list(valid_set & indexed_files)
        return {"status": "success", "purged": list(orphans), "indexed": matched}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

# --- 4. Partitioned 3-Tier RAG Query Endpoint ---
@app.post("/api/rag/query", dependencies=[Depends(verify_api_key)])
async def query_rag(req: QueryRequest):
    try:
        query_input = TextEmbeddingInput(text=req.query, task_type="RETRIEVAL_QUERY")
        query_embedding = embedding_model.get_embeddings([query_input])[0].values
        
        vault_docs, vault_metas = [], []
        val_docs, val_metas = [], []
        core_docs, core_metas = [], []
        
        # --- STAGE 1: Tenant Vault Retrieval ---
        try:
            vault_res = collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                where={"tenant_id": {"$eq": req.tenant_id}}
            )
            vault_docs = vault_res.get("documents", [[]])[0]
            vault_metas = vault_res.get("metadatas", [[]])[0]
        except Exception:
            pass

        # --- STAGE 2: Validated Answers Retrieval ---
        try:
            val_res = collection.query(
                query_embeddings=[query_embedding],
                n_results=2,
                where={"category": {"$eq": "validated"}}
            )
            val_docs = val_res.get("documents", [[]])[0]
            val_metas = val_res.get("metadatas", [[]])[0]
        except Exception:
            pass
            
        # --- STAGE 3: Regulatory Baseline Retrieval (Fallback) ---
        try:
            if req.include_third_parties:
                core_res = collection.query(query_embeddings=[query_embedding], n_results=3)
            else:
                core_res = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=3,
                    where={"category": {"$ne": "third_party"}}
                )
            core_docs = core_res.get("documents", [[]])[0]
            core_metas = core_res.get("metadatas", [[]])[0]
        except Exception:
            pass
        
        all_docs = vault_docs + val_docs + core_docs
        all_metas = vault_metas + val_metas + core_metas
        
        context_blocks = []
        structured_sources = []
        
        for doc, meta in zip(all_docs, all_metas):
            if not meta:
                meta = {}
            
            is_vault = meta.get("is_tenant_doc") or meta.get("tenant_id") == req.tenant_id
            is_validated = meta.get("category") == "validated"
            
            source_file = meta.get("source_file") or meta.get("url") or meta.get("source") or "Quebec Regulatory Baseline"
            page = meta.get("page", "1")
            raw_url = meta.get("url", "")
            clean_url = clean_wayback_url(raw_url)
            
            structured_sources.append({
                "is_vault": bool(is_vault),
                "is_validated": bool(is_validated),
                "source_file": source_file,
                "page": page,
                "url": clean_url,
                "category": meta.get("category", "core")
            })
            
            if is_validated:
                header = f"[Validated HR Answer: {source_file}]"
            elif is_vault:
                header = f"[Vault Policy Doc: {source_file} (Page {page})]"
            else:
                header = f"[Quebec Regulation Source: {clean_url or source_file}]"
                
            context_blocks.append(f"{header}\n{doc}")
            
        context_str = "\n\n---\n\n".join(context_blocks) if context_blocks else "No relevant context found."
        
        # --- HISTORY & LANGUAGE LOGIC ---
        text_to_evaluate = req.query.lower()
        if req.history:
            text_to_evaluate += " " + req.history.get("q", "").lower() + " " + req.history.get("a", "").lower()
            
        french_indicators = ["le", "la", "les", "un", "une", "des", "pour", "est", "comment", "congé", "maternité", "québec", "quoi", "qui", "maladie", "invalidité", "employé", "oui", "non", "réponse", "archivés"]
        is_french = (req.language.lower() in ["french", "fr"]) or any(w in text_to_evaluate.split() for w in french_indicators)
        
        target_lang = "FRENCH" if is_french else "ENGLISH"
        lang_rule = "RÉPONDEZ ENTIÈREMENT EN FRANÇAIS." if is_french else "ANSWER ENTIRELY IN ENGLISH."
        vault_hdr = "### Réponses basées sur vos documents archivés" if is_french else "### Answers based on your vaulted documents"
        general_hdr = "### Réponses générales" if is_french else "### General Answers"
        v_empty = "Aucune réponse pertinente trouvée dans les documents archivés." if is_french else "No relevant answer found from vaulted documents."
        
        history_block = ""
        if req.history and req.history.get("q") and req.history.get("a"):
            if is_french:
                history_block = f"\n=========================================\nTOUR PRÉCÉDENT (Pour contexte) :\nUtilisateur a dit : {req.history.get('q')}\nVous avez répondu : {req.history.get('a')}\n=========================================\n"
            else:
                history_block = f"\n=========================================\nPREVIOUS TURN (For Context):\nUser Said: {req.history.get('q')}\nYou Answered: {req.history.get('a')}\n=========================================\n"

        prompt = f"""You are a practical HR & Payroll Assistant for Quebec employers. You operate strictly in JSON mode.
        
<context>
{context_str}
</context>
{history_block}
USER QUERY: {req.query}

=========================================
STRICT INSTRUCTIONS FOR YOUR OUTPUT:
1. LANGUAGE: {lang_rule} Ignore all other languages.
2. FORMAT: Output ONLY a valid JSON object. No markdown wrappers.
   Schema: {{"vault_answer": "...", "general_answer": "..."}}
3. VAULT_ANSWER RULES: 
   - Base ONLY on [Vault Policy Doc] context.
   - MAXIMUM 2 short bullet points. Keep it extremely brief.
   - Focus ONLY on payroll, premiums, and portal admin actions.
   - If no direct administrative answer exists, output exactly: "NOT_FOUND"
   - Use the PREVIOUS TURN context to understand short user replies.
4. GENERAL_ANSWER RULES:
   - Base PRIMARILY on [Validated HR Answer] context if available.
   - Use [Quebec Regulation Source] ONLY as a fallback.
   - MAXIMUM 3 short bullet points. Keep it extremely brief.
   - DO NOT quote specific laws, acts, or sections. 
   - End with exactly ONE short follow-up question for the user.
=========================================
"""
        
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1
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
            v_ans = data.get("vault_answer", "NOT_FOUND")
            g_ans = data.get("general_answer", data.get("web_answer", ""))
            
            if v_ans == "NOT_FOUND" or "not found" in v_ans.lower() or "aucune réponse" in v_ans.lower():
                v_ans = v_empty
                
            final_answer = f"{vault_hdr}\n{v_ans}\n\n{general_hdr}\n{g_ans}"
        except Exception as e:
            final_answer = f"⚠️ Format Error: The model failed to format the response.\n\nRaw Text:\n{raw_text}"

        return {
            "status": "success",
            "answer": final_answer,
            "sources": structured_sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
