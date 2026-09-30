import uuid
import time
import warnings
import chromadb
from google.genai.models import Models
from google.genai import errors
from src.config import client, EMBEDDING_MODEL

Models._logged_afc_warning = True
warnings.filterwarnings("ignore", message=".*automatic function calling.*")

chroma_client = chromadb.PersistentClient(path="./chroma_db")

def embed_with_retry(batch_chunks, max_retries=5):
    """Wrapper around embed_content that automatically waits out 429 rate limits."""
    for attempt in range(max_retries):
        try:
            return client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch_chunks,
                config={"task_type": "RETRIEVAL_DOCUMENT"}
            )
        except (errors.APIError, errors.ClientError) as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_time = (attempt + 1) * 15
                print(f"⚠️ Hit 429 Rate Limit. Pausing for {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise e
    raise RuntimeError("Exceeded maximum retries for embedding API call.")

def get_existing_urls(collection):
    """Scans ChromaDB metadata and returns a set of unique URLs already stored."""
    if collection.count() == 0:
        return set()
    
    existing_data = collection.get(include=["metadatas"])
    existing_urls = set()
    if existing_data and existing_data["metadatas"]:
        for meta in existing_data["metadatas"]:
            if meta and "url" in meta:
                existing_urls.add(meta["url"])
                
    return existing_urls

def reset_vector_store():
    """Deletes the existing collection and creates a fresh empty one."""
    try:
        chroma_client.delete_collection(name="quebec_insurance")
        print("🗑️ Existing ChromaDB collection cleared.")
    except Exception:
        pass
    return chroma_client.get_or_create_collection(name="quebec_insurance")

def get_or_build_vector_store(documents=None):
    collection = chroma_client.get_or_create_collection(name="quebec_insurance")
    
    if documents is None:
        return collection
        
    if len(documents) > 0:
        print(f"Chunking {len(documents)} document(s) and batching embeddings...")
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        for doc in documents:
            chunks = [p.strip() for p in doc["text"].split("\n\n") if len(p.strip()) > 120]
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadatas.append({"url": doc["url"]})
                all_ids.append(str(uuid.uuid4()))
                
        if not all_chunks:
            print("No valid text chunks found in documents.")
            return collection

        batch_size = 15
        total_chunks = len(all_chunks)
        print(f"Total chunks to embed and add: {total_chunks}")
        
        for i in range(0, total_chunks, batch_size):
            batch_chunks = all_chunks[i:i + batch_size]
            batch_metadatas = all_metadatas[i:i + batch_size]
            batch_ids = all_ids[i:i + batch_size]
            
            response = embed_with_retry(batch_chunks)
            batch_embeddings = [emb.values for emb in response.embeddings]
            
            collection.add(
                ids=batch_ids,
                documents=batch_chunks,
                metadatas=batch_metadatas,
                embeddings=batch_embeddings
            )
            print(f"Processed batch {i} to {i + len(batch_chunks)} of {total_chunks}...")
            
            if i + batch_size < total_chunks:
                time.sleep(5)
            
        print(f"✅ Collection successfully updated. Total chunks in DB: {collection.count()}")
        
    return collection

def retrieve_similar_chunks(query, collection, top_k=25):
    query_response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config={"task_type": "RETRIEVAL_QUERY"}
    )
    query_vector = query_response.embeddings[0].values
    
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k
    )
    
    formatted_results = []
    if results["documents"] and len(results["documents"]) > 0:
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "text": results["documents"][0][i],
                "url": results["metadatas"][0][i]["url"]
            })
            
    return formatted_results
