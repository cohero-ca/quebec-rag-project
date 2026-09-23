import os
import requests
import streamlit as st

st.set_page_config(page_title="Quebec Insurance RAG", page_icon="⚖️", layout="wide")

st.title("⚖️ Quebec Insurance & Regulatory Assistant")
st.caption("Powered by FastAPI, ChromaDB, and Google Vertex AI on Cloud Run")

# Load configuration securely from environment variables
API_KEY = os.getenv("API_KEY", "")
API_URL = os.getenv(
    "API_URL",
    "https://quebec-rag-api-822652243793.northamerica-northeast1.run.app/api/rag/query",
)

# User query input
query = st.text_area(
    "Ask a question about Quebec insurance regulations:",
    height=100,
    placeholder="e.g., What are the requirements for group insurance coverage in Quebec?",
)

if st.button("Submit Query", type="primary") and query:
    if not API_KEY:
        st.error("API_KEY environment variable is not configured on the server.")
    else:
        headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}

        with st.spinner("Searching ChromaDB context and generating answer with Gemini..."):
            try:
                response = requests.post(
                    API_URL, headers=headers, json={"query": query}, timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    st.subheader("💡 Answer")
                    st.markdown(data.get("answer", "No answer text provided."))

                    if "sources" in data or "context" in data:
                        with st.expander("📚 View Retrieved Sources / Context"):
                            st.json(data.get("sources") or data.get("context"))
                else:
                    st.error(f"Error {response.status_code}: {response.text}")

            except Exception as e:
                st.error(f"Connection error: {e}")
