import os
import sys
import asyncio
import json
from crawl4ai import AsyncWebCrawler

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import QUEBEC_SOURCES, SOURCE_CATEGORIES

def update_config_url(original_url: str, fallback_url: str):
    config_path = os.path.join("src", "config.py")
    if not os.path.exists(config_path):
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith("#"):
            new_lines.append(line)
        elif original_url in line:
            new_lines.append(line.replace(original_url, fallback_url))
            updated = True
        else:
            new_lines.append(line)
            
    if updated:
        with open(config_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"  📝 Updated src/config.py: '{original_url}' ➔ '{fallback_url}'")

async def crawl_quebec_sources(urls=None):
    target_urls = urls if urls is not None else QUEBEC_SOURCES
    documents = []

    print(f"🕸️ Crawling {len(target_urls)} target source(s)...")

    async with AsyncWebCrawler(verbose=False) as crawler:
        for url in target_urls:
            category = SOURCE_CATEGORIES.get(url, "core")
            success = False
            
            try:
                result = await crawler.arun(url=url)
                markdown_content = getattr(result, 'markdown', '') or getattr(getattr(result, 'markdown_v2', None), 'raw_markdown', '')
                status_code = getattr(result, 'status_code', 200)
                
                if result.success and markdown_content.strip() and status_code < 400:
                    documents.append({
                        "url": url,
                        "category": category,
                        "text": markdown_content
                    })
                    print(f"  ✓ [{category.upper()}] Successfully scraped: {url}")
                    success = True
                else:
                    print(f"  ⚠️ Direct scrape failed or blocked: {url} (Status: {status_code})")
            except Exception as e:
                print(f"  ❌ Error direct scraping {url}: {e}")

            if not success and "web.archive.org/web/" not in url:
                fallback_url = f"https://web.archive.org/web/{url}"
                print(f"  🔄 Attempting Wayback Machine fallback: {fallback_url}")
                
                try:
                    fb_result = await crawler.arun(url=fallback_url)
                    fb_markdown = getattr(fb_result, 'markdown', '') or getattr(getattr(fb_result, 'markdown_v2', None), 'raw_markdown', '')
                    fb_status = getattr(fb_result, 'status_code', 200)
                    
                    if fb_result.success and fb_markdown.strip() and fb_status < 400:
                        documents.append({
                            "url": fallback_url,
                            "category": category,
                            "text": fb_markdown
                        })
                        print(f"  ✓ [{category.upper()}] Successfully scraped fallback: {fallback_url}")
                        update_config_url(url, fallback_url)
                    else:
                        print(f"  ❌ Fallback failed for: {fallback_url} (Status: {fb_status})")
                except Exception as fb_err:
                    print(f"  ❌ Error scraping fallback {fallback_url}: {fb_err}")

    if documents:
        output_dir = os.path.join("data", "raw")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "scraped_documents.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(documents)} document(s) to '{output_file}'")

    return documents

if __name__ == "__main__":
    asyncio.run(crawl_quebec_sources())