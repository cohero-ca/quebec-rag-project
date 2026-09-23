import os
import asyncio
from crawl4ai import AsyncWebCrawler
from src.config import QUEBEC_SOURCES

def update_config_url(original_url: str, fallback_url: str):
    """Replaces original_url with fallback_url inside src/config.py."""
    config_path = os.path.join("src", "config.py")
    if not os.path.exists(config_path):
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if original_url in content:
        new_content = content.replace(original_url, fallback_url)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  📝 Updated src/config.py: '{original_url}' ➔ '{fallback_url}'")

async def crawl_quebec_sources(urls=None):
    target_urls = urls if urls is not None else QUEBEC_SOURCES
    documents = []

    print(f"🕸️ Crawling {len(target_urls)} target source(s)...")

    async with AsyncWebCrawler(verbose=False) as crawler:
        for url in target_urls:
            success = False
            
            # 1. Primary Scrape Attempt
            try:
                result = await crawler.arun(url=url)
                markdown_content = getattr(result, 'markdown', '') or getattr(getattr(result, 'markdown_v2', None), 'raw_markdown', '')
                status_code = getattr(result, 'status_code', 200)
                
                if result.success and markdown_content.strip() and status_code < 400:
                    documents.append({
                        "url": url,
                        "text": markdown_content
                    })
                    print(f"  ✓ Successfully scraped: {url}")
                    success = True
                else:
                    print(f"  ⚠️ Direct scrape failed or blocked: {url} (Status: {status_code})")
            except Exception as e:
                print(f"  ❌ Error direct scraping {url}: {e}")

            # 2. Dynamic Fallback Attempt
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
                            "text": fb_markdown
                        })
                        print(f"  ✓ Successfully scraped fallback: {fallback_url}")
                        update_config_url(url, fallback_url)
                    else:
                        print(f"  ❌ Fallback failed for: {fallback_url} (Status: {fb_status})")
                except Exception as fb_err:
                    print(f"  ❌ Error scraping fallback {fallback_url}: {fb_err}")

    return documents
