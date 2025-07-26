import asyncio
from .async_webcrawler import AsyncWebCrawler
from .async_configs import CrawlerRunConfig, BrowserConfig

async def main():
  crawler = AsyncWebCrawler()

  async with crawler: # This will call crawler.start() and crawler.close()
    print("\n--- Simple Crawl: www.scrapingcourse.com ---")
    result_example = await crawler.arun("https://www.scrapingcourse.com/ecommerce/")
    print(f"Result URL: {result_example.url}")
    print(f"Result Status: {result_example.status_code}")
    print(f"Result Success: {result_example.success}")
    print(f"HTML (first 200 chars):\n{result_example.html[:200]}...")

    if result_example.markdown:
      print(f"Markdown (first 200 chars):\n{result_example.markdown.raw_markdown[:200]}...")

    # print("\n--- Simple Crawl: Non-existent Page (Error Handling) ---")
    # result_error = await crawler.arun("https://www.example.com/non-existent-page-12345")
    # print(f"Result URL: {result_error.url}")
    # print(f"Result Status: {result_error.status_code}")
    # print(f"Result Success: {result_error.success}")
    # print(f"Result Error Message: {result_error.error_message}")

if __name__ == "__main__":
  asyncio.run(main())