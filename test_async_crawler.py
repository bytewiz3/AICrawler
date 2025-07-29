import asyncio
from .async_webcrawler import AsyncWebCrawler
from .async_configs import CrawlerRunConfig, BrowserConfig

async def main():
  crawler = AsyncWebCrawler()

  # async with crawler: # This will call crawler.start() and crawler.close()
  #   print("\n--- Simple Crawl: www.scrapingcourse.com ---")
  #   result_example = await crawler.arun("https://www.scrapingcourse.com/ecommerce/")
  #   print(f"Result URL: {result_example.url}")
  #   print(f"Result Status: {result_example.status_code}")
  #   print(f"Result Success: {result_example.success}")
  #   print(f"HTML (first 200 chars):\n{result_example.html[:200]}...")

  #   if result_example.markdown:
  #     print(f"Markdown (first 200 chars):\n{result_example.markdown.raw_markdown[:200]}...")

    # print("\n--- Simple Crawl: Non-existent Page (Error Handling) ---")
    # result_error = await crawler.arun("https://www.example.com/non-existent-page-12345")
    # print(f"Result URL: {result_error.url}")
    # print(f"Result Status: {result_error.status_code}")
    # print(f"Result Success: {result_error.success}")
    # print(f"Result Error Message: {result_error.error_message}")
  
  async with crawler:
    print("\n--- Crawl: Robots.txt Allowed Page ---")
    allowed_url = "https://www.scrapingcourse.com/ecommerce/"
    config_allowed = CrawlerRunConfig(check_robots_txt=True, page_timeout=6000)
    result_allowed = await crawler.arun(allowed_url, config=config_allowed)
    print(f"Result URL: {result_allowed.url}")
    print(f"Result Status: {result_allowed.status_code}")
    print(f"Result Success: {result_allowed.success}")
    if not result_allowed.success:
        print(f"Result Error Message: {result_allowed.error_message}")
    print(f"HTML (first 200 chars):\n{result_allowed.html[:200]}...")


    print("\n--- Crawl: Robots.txt Disallowed Page ---")
    # A URL that is likely disallowed for common bots on many WordPress sites
    wordpress_disallowed_url = "https://wordpress.com/wp-admin/"
    config_wordpress_disallowed = CrawlerRunConfig(
        check_robots_txt=True,
    )
    print(f"Attempting to crawl: {wordpress_disallowed_url}")
    result_disallowed = await crawler.arun(wordpress_disallowed_url, config=config_wordpress_disallowed)
    print(f"Result URL: {result_disallowed.url}")
    print(f"Result Status: {result_disallowed.status_code}")
    print(f"Result Success: {result_disallowed.success}")
    if not result_disallowed.success:
        print(f"Result Error Message: {result_disallowed.error_message}")
    print(f"HTML (first 200 chars):\n{result_disallowed.html[:200]}...")

if __name__ == "__main__":
  asyncio.run(main())