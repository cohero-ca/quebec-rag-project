import os
import json
from datetime import datetime

LOGS_DIR = "logs"

def log_session_event(session_id: str, query: str, insurer: str, response_text: str, retrieved_sources: list):
    """Appends structured Q&A data to a session-specific JSON file."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    log_file = os.path.join(LOGS_DIR, f"session_{session_id}.json")
    
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "session_id": session_id,
        "insurer": insurer,
        "query": query,
        "response": response_text,
        "sources": retrieved_sources
    }

    # Load existing logs or start fresh array
    session_logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                session_logs = json.load(f)
        except json.JSONDecodeError:
            session_logs = []

    session_logs.append(event)

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(session_logs, f, indent=2, ensure_ascii=False)
