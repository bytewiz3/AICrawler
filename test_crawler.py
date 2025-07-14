import asyncio
from .async_crawler_strategy import AsyncPlaywrightStrategy
from .async_configs import CrawlerRunConfig
import base64
from bs4 import BeautifulSoup

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

    # # Example 4: Crawl with network request capturing
    # print("\n--- Crawling with Network Capture ---")
    # config_with_network = CrawlerRunConfig(
    #     capture_network_requests=True
    # )
    # response_with_network = await crawler.crawl(target_url, config=config_with_network)

    # print(f"Status Code: {response_with_network.status_code}")
    # print(f"JS Execution Result: {response_with_network.js_execution_result}")
    # if response_with_network.network_requests:
    #     print(f"Captured {len(response_with_network.network_requests)} network events.")
    #     # Print first 5 events for brevity
    #     for i, event in enumerate(response_with_network.network_requests[:5]):
    #         print(f"  Event {i+1}: Type={event['event_type']}, URL={event['url']}")
    #     if len(response_with_network.network_requests) > 5:
    #         print("  ... (more network events)")
    # else:
    #     print("No network requests captured.")
    # print(f"HTML (first 200 chars):\n{response_with_network.html[:200]}...")

    # Example 5: Crawl with screenshot
    # print("\n--- Crawling with Screenshot ---")
    # config_with_screenshot = CrawlerRunConfig(
    #     screenshot=True
    # )
    # response_with_screenshot = await crawler.crawl(target_url, config=config_with_screenshot)

    # print(f"Status Code: {response_with_screenshot.status_code}")
    # if response_with_screenshot.screenshot:
    #     print(f"Screenshot data collected (base64 encoded, length: {len(response_with_screenshot.screenshot)}).")
    #     with open("example_screenshot.png", "wb") as f:
    #         f.write(base64.b64decode(response_with_screenshot.screenshot))
    #     print("Screenshot saved to example_screenshot.png.")
    # else:
    #     print("No screenshot data captured.")
    # print(f"HTML (first 200 chars):\n{response_with_screenshot.html[:200]}...")

    # Example 6: Crawl iframes
    iframe_test_url = "https://the-internet.herokuapp.com/iframe"
    config_with_iframe = CrawlerRunConfig(
      process_iframes=True
    )
    response_iframe = await crawler.crawl(iframe_test_url, config=config_with_iframe)

    print(f"\nCrawl Result for {iframe_test_url}:")
    print(f"  Status Code: {response_iframe.status_code}")

    print("\n--- HTML content after iframe processing (looking for 'AICrawler-extracted-iframe-content') ---")
    soup = BeautifulSoup(response_iframe.html, "html.parser")
    found = soup.find("div", class_="AICrawler-extracted-iframe-content")
    if found:
      print("SUCCESS: Found content or placeholder from processed iframe!")
    else:
      print("NOTE: Could not verify iframe content directly in HTML. This might be due to iframe content, or the iframe was not found/processed.")
    print(f"HTML (first 1000 chars):\n{response_iframe.html[:1000]}...")

if __name__ == "__main__":
    asyncio.run(main())