import asyncio
from .async_crawler_strategy import AsyncPlaywrightStrategy
from .async_configs import CrawlerRunConfig

async def main():
  crawler = AsyncPlaywrightStrategy()
  target_url = "https://www.scrapingcourse.com/ecommerce/"

  async with crawler:
    # # Example 1: Basic crawl (no JS)
    # print(f"Attempting to crawl: {target_url}")
    # crawl_result = await crawler.crawl(target_url)

    # print(f"Status Code: {crawl_result.status_code}")
    # print("\n--- First 500 characters of HTML ---")
    # print(crawl_result.html[:500])
    # print("...")
    # print("\n--- End of HTML preview ---")

    # # Example 2: Crawl with JavaScript to change page title
    # print("\n--- Crawling with JavaScript (changing title) ---")
    # js_config_1 = CrawlerRunConfig(
    #     js_code="document.title = 'New Title from Scraper';"
    # )
    # response_with_js_1 = await crawler.crawl(target_url, config=js_config_1)
    # print(f"Status Code: {response_with_js_1.status_code}")
    # print(f"JS Execution Result: {response_with_js_1.js_execution_result}")
    # print(f"HTML (first 1000 chars):\n{response_with_js_1.html[:1000]}...")

    # # Example 3: Crawl with JavaScript to click the "Add to Cart" button
    # print("\n--- Crawling with JavaScript (simulated click) ---")
    # js_config_2 = CrawlerRunConfig(
    #     js_code="""
    #     (() => {
    #         const button = document.querySelector('.add_to_cart_button');
    #         if (button) {
    #             button.click();
    #             return 'Add to cart button clicked!';
    #         } else {
    #             return 'Add to cart button not found.';
    #         }
    #     })();
    #     """
    # )
    # response_with_js_2 = await crawler.crawl(target_url, config=js_config_2)
    # print(f"Status Code: {response_with_js_2.status_code}")
    # print(f"JS Execution Result: {response_with_js_2.js_execution_result}")
    # print(f"HTML (first 60000 chars after potential click):\n{response_with_js_2.html[:60000]}...")

    # Example 4: Crawl with network request capturing
    print("\n--- Crawling with Network Capture ---")
    config_with_network = CrawlerRunConfig(
        capture_network_requests=True
    )
    response_with_network = await crawler.crawl(target_url, config=config_with_network)

    print(f"Status Code: {response_with_network.status_code}")
    print(f"JS Execution Result: {response_with_network.js_execution_result}")
    if response_with_network.network_requests:
        print(f"Captured {len(response_with_network.network_requests)} network events.")
        # Print first 5 events for brevity
        for i, event in enumerate(response_with_network.network_requests[:5]):
            print(f"  Event {i+1}: Type={event['event_type']}, URL={event['url']}")
        if len(response_with_network.network_requests) > 5:
            print("  ... (more network events)")
    else:
        print("No network requests captured.")
    print(f"HTML (first 200 chars):\n{response_with_network.html[:200]}...")

if __name__ == "__main__":
    asyncio.run(main())