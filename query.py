import warnings
import logging
import argparse
import sys

# Mute standard Python warnings
warnings.filterwarnings("ignore", message=".*automatic function calling.*")

# Mute the Google SDK's internal logging (forces it to only print critical crashes)
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)

from src.vector_store import get_or_build_vector_store, retrieve_similar_chunks
from src.rag import generate_rag_response

def main():
    parser = argparse.ArgumentParser(description="Quebec Insurance RAG CLI Query Tool")
    parser.add_argument(
        "--no-log", "-n",
        action="store_true",
        help="Disable session audit logging for testing"
    )
    args = parser.parse_args()

    enable_logging = not args.no_log

    print("Connecting to local ChromaDB store...")
    vector_store = get_or_build_vector_store()
    
    chunk_count = vector_store.count()
    if chunk_count == 0:
        print("❌ Vector store is empty! Please run main.py first to crawl and embed sources.")
        sys.exit(1)
        
    print(f" Ready! Vector store loaded with {chunk_count} document chunks.")
    if not enable_logging:
        print("🧪 Test mode active: Audit logging is DISABLED.")
    else:
        print("📝 Audit logging is ENABLED.")
        
    print("Type your question below. Commands: 'exit' to quit, '/inspect <query>' to view raw retrieved chunks.\n")
    print("=" * 70)

    while True:
        try:
            user_input = input("\n[Quebec Insurance RAG] > ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting RAG interface.")
                break
                
            # Inspect raw chunks without calling Gemini LLM or logging
            if user_input.startswith("/inspect"):
                raw_query = user_input.replace("/inspect", "").strip()
                if not raw_query:
                    print("Please provide a query after /inspect (e.g., /inspect RAMQ eligibility)")
                    continue
                    
                print(f"\n🔍 Retrieving top chunks for: '{raw_query}'...")
                chunks = retrieve_similar_chunks(raw_query, vector_store, top_k=5)
                for i, chunk in enumerate(chunks, 1):
                    print(f"\n--- CHUNK {i} ---")
                    print(f"URL: {chunk['url']}")
                    print(f"TEXT:\n{chunk['text'][:300]}...") # Truncate long text
                continue

            # Standard RAG Query
            print("\n Searching vectors & generating answer...")
            answer = generate_rag_response(
                user_input, 
                vector_store, 
                enable_logging=enable_logging
            )
            print("\n--- RESPONSE ---")
            print(answer)
            print("-" * 70)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ Error processing query: {e}")

if __name__ == "__main__":
    main()
