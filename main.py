import asyncio
import argparse
import sys
import warnings
from google.genai.models import Models
from src.config import QUEBEC_SOURCES
from src.scraper import crawl_quebec_sources
from src.vector_store import get_or_build_vector_store, get_existing_urls, reset_vector_store

Models._logged_afc_warning = True
warnings.filterwarnings("ignore", message=".*automatic function calling.*")

async def main():
    parser = argparse.ArgumentParser(description="Quebec Insurance RAG Ingestion Pipeline")
    parser.add_argument("--mode", choices=["new", "full"], help="Run mode: 'new' (incremental) or 'full' (re-process all)")
    args = parser.parse_args()

    mode = args.mode

    # Interactive Menu if no --mode flag is passed
    if not mode:
        print("\n====================================================")
        print("  Quebec Insurance RAG - Ingestion Manager")
        print("====================================================")
        print("Select ingestion mode:")
        print("  [1] Incremental Update (Scrape & embed ONLY newly added URLs)")
        print("  [2] Full Re-index (Wipe DB & re-process ALL sources from scratch)")
        print("  [3] Cancel")
        print("----------------------------------------------------")
        choice = input("Enter choice [1/2/3]: ").strip()

        if choice == "1":
            mode = "new"
        elif choice == "2":
            mode = "full"
        else:
            print("Ingestion cancelled.")
            sys.exit(0)

    # Mode 1: Full Re-index
    if mode == "full":
        print("\n⚠️  FULL RE-INDEX SELECTED")
        print("Wiping existing vector store and re-processing all configured sources...")
        vector_store = reset_vector_store()
        
        print(f"Scraping all {len(QUEBEC_SOURCES)} sources with Crawl4AI...")
        documents = await crawl_quebec_sources(urls=QUEBEC_SOURCES)
        
        get_or_build_vector_store(documents=documents)
        print("\n🎉 Full re-index complete!")

    # Mode 2: Incremental Sync
    elif mode == "new":
        print("\n🔍 INCREMENTAL UPDATE SELECTED")
        vector_store = get_or_build_vector_store()
        existing_urls = get_existing_urls(vector_store)
        print(f"Found {len(existing_urls)} existing URL(s) in local ChromaDB.")

        new_urls = [url for url in QUEBEC_SOURCES if url not in existing_urls]

        if not new_urls:
            print("✅ All URLs in config.py are already processed. Vector store is up to date!")
            print(f"Total chunks stored: {vector_store.count()}")
            return

        print(f"\n🆕 Detected {len(new_urls)} new URL(s) to process:")
        for url in new_urls:
            print(f"  + {url}")

        print("\nStarting Crawl4AI for new sources...")
        new_documents = await crawl_quebec_sources(urls=new_urls)
        
        get_or_build_vector_store(documents=new_documents)
        print("\n🎉 Incremental update complete!")

if __name__ == "__main__":
    asyncio.run(main())
