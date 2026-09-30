import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")

# --- Authentication Function ---
def login_user(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    return response.json()

# --- Session State Initialization ---
if "id_token" not in st.session_state:
    st.session_state.id_token = None
    st.session_state.tenant_id = None

# --- Login Screen ---
if not st.session_state.id_token:
    st.title("Plan Sponsor Portal")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        auth_res = login_user(email, password)
        if "idToken" in auth_res:
            st.session_state.id_token = auth_res["idToken"]
            st.session_state.tenant_id = auth_res["localId"]
            st.rerun()
        else:
            st.error("Invalid email or password. Please try again.")
    
    st.stop()

# --- Chatbot UI (Only visible if logged in) ---
st.sidebar.button("Logout", on_click=lambda: st.session_state.clear() or st.rerun())

st.title("Enhanced HR Chatbot")
st.write(f"Securely connected. Tenant ID: `{st.session_state.tenant_id}`")


st.write(f"Securely connected. Tenant ID: {st.session_state.tenant_id}")

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
