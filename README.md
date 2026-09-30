# ⚖️ Quebec Insurance & Regulatory RAG Pipeline

A production-ready Retrieval-Augmented Generation (RAG) system built to query and synthesize insights from Quebec insurance regulations and legal framework documents. 

Powered by **FastAPI**, **ChromaDB**, **Google Vertex AI** (`text-embedding-005` and Gemini Flash), and **Streamlit**, fully containerized and deployed to **Google Cloud Run** with automated CI/CD via **GitHub Actions**.

---

## 🏗️ Architecture Overview

                          +-------------------------------+
                          |    Streamlit Web Interface    |
                          |   (Cloud Run / Local App)     |
                          +---------------+---------------+
                                          |
                                HTTP POST | X-API-Key
                                          v
                          +---------------+---------------+
                          |    FastAPI RAG Service        |
                          |        (Cloud Run)            |
                          +---------------+---------------+
                                          |
                      +-------------------+-------------------+
                      |                                       |
                      v                                       v
         +------------+------------+             +------------+------------+
         |      ChromaDB Vector    |             |  Google Vertex AI API     |
         |    Context Retrieval    |             | (Embeddings & Gemini Gen) |
         +-------------------------+             +-------------------------+

---

## 🛠️ Tech Stack & Key Services

| Component | Technology / Service | Deployment Context |
| :--- | :--- | :--- |
| **Backend API** | Python 3.12, FastAPI, Uvicorn | Google Cloud Run (`quebec-rag-api`) |
| **Frontend UI** | Streamlit | Google Cloud Run (`quebec-rag-ui`) |
| **Vector Store** | ChromaDB (`./chroma_db`) | Embedded in API Container |
| **Embeddings** | Vertex AI (`text-embedding-005`) | GCP Region: `northamerica-northeast1` |
| **LLM Synthesis**| Gemini Flash (`google-genai` SDK) | GCP Region: `northamerica-northeast1` |
| **CI/CD Pipeline**| GitHub Actions | Automated build and deploy on `git push` |

---

## 📂 Project Structure

quebec-rag-project/
├── api.py                  # FastAPI server, RAG orchestration, and Vertex AI hooks
├── Dockerfile              # Container definition for the FastAPI backend service
├── chroma_db/              # Persisted vector database containing indexed regulations
├── ui/
│   ├── app.py              # Streamlit frontend client app
│   └── Dockerfile          # Container definition for the Streamlit UI service
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD deployment workflow for Google Cloud Run
├── .gitignore              # Ignores sensitive keys, python environments, and caches
└── README.md               # Project documentation

---

## 🔒 Authentication & API Endpoints

All API endpoints are protected using an HTTP header key.

* **Header Name**: `X-API-Key`
* **Base URL**: `https://quebec-rag-api-822652243793.northamerica-northeast1.run.app`

### `POST /api/rag/query`

Performs context retrieval against ChromaDB embeddings and generates a synthesized answer using Gemini.

#### Request Body
{
  "query": "What are the requirements for group insurance coverage in Quebec?"
}

#### Example Response
{
  "answer": "In Quebec, group insurance regulations mandate that...",
  "sources": [
    { "document": "Quebec_Insurance_Act_Sec42.pdf" }
  ]
}

---

## 🚀 Local Development Setup

### 1. Clone Repository & Create Virtual Environment
git clone https://github.com/cohero-ca/quebec-rag-project.git
cd quebec-rag-project
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

### 2. Run FastAPI Backend Locally
uvicorn api:app --reload --port 8000

### 3. Run Streamlit UI Locally
python -m streamlit run ui/app.py

---

## 🔄 CI/CD & Deployment

This repository uses **GitHub Actions** to automate deployments to Google Cloud Run whenever changes are merged into the `main` branch.

1. **GitHub Secret**: The deployment requires a service account JSON key saved under `GCP_SA_KEY` in **Repository Settings -> Secrets and variables -> Actions**.
2. **Workflow File**: Managed inside `.github/workflows/deploy.yml`.