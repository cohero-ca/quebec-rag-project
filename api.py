import os
import uvicorn
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.vector_store import get_or_build_vector_store
from src.rag import generate_rag_response

app = FastAPI(title="Quebec Insurance RAG API")

# 1. Enable CORS so your website frontend can make requests from any domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set your specific website domain here in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Simple API Key Security
API_KEY = os.getenv("API_KEY", "your-secret-key-123")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(header_key: str = Depends(api_key_header)):
    if header_key == API_KEY:
        return header_key
    raise HTTPException(status_code=403, detail="Invalid or missing API Key")

# Initialize ChromaDB once at server startup
vector_store = get_or_build_vector_store()

class QueryRequest(BaseModel):
    query: str
    insurer_context: str = "General"
    enable_logging: bool = True

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Quebec RAG Pipeline is active"}

@app.post("/api/rag/query", dependencies=[Depends(get_api_key)])
async def rag_query_endpoint(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    try:
        response = generate_rag_response(
            user_query=request.query,
            collection=vector_store,
            insurer_context=request.insurer_context,
            enable_logging=request.enable_logging
        )
        return {"query": request.query, "answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)