import asyncio
from .async_crawler_strategy import AsyncPlaywrightStrategy

async def main():
  crawler = AsyncPlaywrightStrategy()
  async with crawler:
    target_url = "https://www.scrapingcourse.com/ecommerce/"
    print(f"Attempting to crawl: {target_url}")
    crawl_result = await crawler.crawl(target_url)

    print(f"Status Code: {crawl_result.status_code}")
    print("\n--- First 500 characters of HTML ---")
    print(crawl_result.html[:500])
    print("...")
    print("\n--- End of HTML preview ---")

if __name__ == "__main__":
    asyncio.run(main())