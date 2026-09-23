import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Initialize the crawler
    async with AsyncWebCrawler() as crawler:
        print("Crawler initialized. Fetching page...")
        
        # Execute the crawl on a simple test page
        result = await crawler.arun(url="https://example.com")
        
        # Verify the output
        if result.success:
            print("\n✅ Success! Here is the extracted Markdown:\n")
            # Print the first 500 characters of the markdown
            print(result.markdown[:500])
        else:
            print(f"\n❌ Crawl failed: {result.error_message}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())