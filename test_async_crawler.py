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
    print("\n--- Concurrently crawling a list of URLs ---")
    urls_to_crawl = [
        "https://www.scrapingcourse.com/ecommerce/",
        "https://www.scrapingcourse.com/pagination",
        "https://www.scrapingcourse.com/button-click"
    ]
    
    # Configure a single run for all URLs
    config_many = CrawlerRunConfig()
    
    results = await crawler.arun_many(urls_to_crawl, config=config_many)
    
    print(f"\nFinished crawling {len(results)} URLs concurrently.")
    for result in results:
        print("-" * 50)
        print(f"URL: {result.url}")
        print(f"Status: {result.status_code}")
        print(f"Success: {result.success}")
        if not result.success:
            print(f"Error: {result.error_message}")
        if result.html:
            print(f"HTML (first 50 chars): {result.html[:50]}...")

    # print("\n--- Crawl: Robots.txt Allowed Page ---")
    # allowed_url = "https://www.scrapingcourse.com/ecommerce/"
    # config_allowed = CrawlerRunConfig(check_robots_txt=True, page_timeout=6000)
    # result_allowed = await crawler.arun(allowed_url, config=config_allowed)
    # print(f"Result URL: {result_allowed.url}")
    # print(f"Result Status: {result_allowed.status_code}")
    # print(f"Result Success: {result_allowed.success}")
    # if not result_allowed.success:
    #     print(f"Result Error Message: {result_allowed.error_message}")
    # print(f"HTML (first 200 chars):\n{result_allowed.html[:200]}...")


    # print("\n--- Crawl: Robots.txt Disallowed Page ---")
    # A URL that is likely disallowed for common bots on many WordPress sites
    # wordpress_disallowed_url = "https://wordpress.com/wp-admin/"
    # config_wordpress_disallowed = CrawlerRunConfig(
    #     check_robots_txt=True,
    # )
    # print(f"Attempting to crawl: {wordpress_disallowed_url}")
    # result_disallowed = await crawler.arun(wordpress_disallowed_url, config=config_wordpress_disallowed)
    # print(f"Result URL: {result_disallowed.url}")
    # print(f"Result Status: {result_disallowed.status_code}")
    # print(f"Result Success: {result_disallowed.success}")
    # if not result_disallowed.success:
    #     print(f"Result Error Message: {result_disallowed.error_message}")
    # print(f"HTML (first 200 chars):\n{result_disallowed.html[:200]}...")

if __name__ == "__main__":
  asyncio.run(main())