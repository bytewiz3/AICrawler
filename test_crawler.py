import asyncio
from .async_crawler_strategy import AsyncPlaywrightStrategy
from .async_configs import CrawlerRunConfig, BrowserConfig
import base64
from bs4 import BeautifulSoup
import tempfile
import os

async def main():
  my_download_dir = os.path.join(os.getcwd(), "my_downloads")
  os.makedirs(my_download_dir, exist_ok=True) # Ensure the directory exists

  crawler = AsyncPlaywrightStrategy(
    browser_config=BrowserConfig(
        accept_downloads=True,
        downloads_path=my_download_dir
    )
  )
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
    # target_url = "https://www.theverge.com/tech"
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
    # iframe_test_url = "https://the-internet.herokuapp.com/iframe"
    # config_with_iframe = CrawlerRunConfig(
    #   process_iframes=True
    # )
    # response_iframe = await crawler.crawl(iframe_test_url, config=config_with_iframe)

    # print(f"\nCrawl Result for {iframe_test_url}:")
    # print(f"  Status Code: {response_iframe.status_code}")

    # print("\n--- HTML content after iframe processing (looking for 'AICrawler-extracted-iframe-content') ---")
    # soup = BeautifulSoup(response_iframe.html, "html.parser")
    # found = soup.find("div", class_="AICrawler-extracted-iframe-content")
    # if found:
    #   print("SUCCESS: Found content or placeholder from processed iframe!")
    # else:
    #   print("NOTE: Could not verify iframe content directly in HTML. This might be due to iframe content, or the iframe was not found/processed.")
    # print(f"HTML (first 1000 chars):\n{response_iframe.html[:1000]}...")

    # Example 7: smart wait
    # print("\n--- Crawling with Smart Wait (CSS Selector) ---")
    # config_wait_css = CrawlerRunConfig(
    #   wait_for="css:tr.athing", # Wait for the element containing posts to appear
    #   page_timeout=5000
    # )
    # response_wait_css = await crawler.crawl("https://news.ycombinator.com/", config=config_wait_css)

    # print(f"Status Code: {response_wait_css.status_code}")

    # Example 8: crawl with overlay removal
    # print("\n--- Crawling a page with potential overlays ---")
    # test_url = "https://www.asos.com/"

    # config_with_original_overlays = CrawlerRunConfig(
    #   # wait_for="css:#onetrust-policy-text",
    #   # page_timeout=6000,
    #   # remove_overlay_elements=True,
    #   magic=True,
    #   scan_full_page=True,
    #   scroll_delay=0.5,
    #   page_timeout=10000,
    #   wait_until="networkidle",
    #   user_agent_mode="random",
    #   user_agent_generator_config={"browsers": ["Chrome", "Firefox"], "platforms": ["desktop"]},
    # )
    # print(f"Attempting to crawl: {test_url}")
    # response_original_overlays = await crawler.crawl(test_url, config=config_with_original_overlays)

    # print(f"\nCrawl Result for {test_url}:")
    # print(f"  Status Code: {response_original_overlays.status_code}")
    # print(f"HTML (first 1000 chars):\n{response_original_overlays.html[:1000]}...")
    # soup = BeautifulSoup(response_original_overlays.html, "html.parser")
    # element = soup.select_one("#onetrust-policy-text")
    # if element:
    #   print("Element found:", element.text.strip())
    # else:
    #   print("Element not found")

    # Example 9: crawl a page with a download link
    # print("\n--- Crawling a Page with a Download Link ---")
    # download_test_url = "https://africau.edu/resource/austrategicplan.pdf"
    # print(f"\n--- Crawling with FIXED download path: {my_download_dir} ---")

    # config_download = CrawlerRunConfig(
    #     page_timeout=6000,
    # )
    # print(f"Attempting to crawl and download from: {download_test_url}")
    # response_download = await crawler.crawl(download_test_url, config=config_download)

    # print(f"\nCrawl Result for {download_test_url}:")
    # print(f"  Status Code: {response_download.status_code}")
    # if response_download.downloaded_files:
    #     print(f"  Downloaded Files: {response_download.downloaded_files}")
    #     for f_path in response_download.downloaded_files:
    #         if os.path.exists(f_path):
    #             print(f"    - File exists at: {f_path} (size: {os.path.getsize(f_path)} bytes)")
    #         else:
    #             print(f"    - File NOT found at: {f_path}")
    # else:
    #     print("  No files were downloaded.")

    # await asyncio.sleep(1)

    # Example 10: crawl a page with console message capturing
    # print("\n--- Crawling a Page with Console Message Capturing ---")

    # config = CrawlerRunConfig(
    #     page_timeout=6000,
    #     capture_console_messages=True,
    # )

    # response = await crawler.crawl(target_url, config=config)

    # print(f"Crawled HTML length: {len(response.html)}")
    # print(f"Status Code: {response.status_code}")
    
    # if response.console_messages:
    #     print(f"\n--- Captured {len(response.console_messages)} Console Messages ---")
    #     for msg in response.console_messages:
    #         print(f"[{msg['timestamp']:.2f}] Type: {msg['type'].upper()}, Text: {msg['text']}")
    #         if msg['type'] == 'error' and 'stack' in msg:
    #             print(f"  Stack: {msg['stack']}")
    #     print("------------------------------------------")
    # else:
    #     print("\nNo console messages captured.")

    # Example 10: capture TLS certificate
    # print("\n--- Crawling a Page with TLS certificate fetching ---")

    # config = CrawlerRunConfig(
    #     capture_console_messages=True,
    #     fetch_ssl_certificate=True,
    # )

    # response = await crawler.crawl(target_url, config=config)

    # print(f"Crawled HTML length: {len(response.html)}")
    # print(f"Status Code: {response.status_code}")
    
    # if response.ssl_certificate:
    #   cert = response.ssl_certificate
    #   print(f"SSL Certificate Info:")
    #   print(f"Issuer: {cert.issuer}")
    #   print(f"Subject: {cert.subject}")
    #   print(f"Valid From: {cert.valid_from}")
    #   print(f"Valid Until: {cert.valid_until}")
    #   print(f"Fingerprint (SHA256): {cert.fingerprint}")
    # else:
    #     print("\nNo TLS certificate fetched.")

    # Example 11: capture mhtml
    config = CrawlerRunConfig(
      capture_mhtml=True,
    )

    response = await crawler.crawl(target_url, config=config)

    print(f"Crawled HTML length: {len(response.html)}")
    print(f"Status Code: {response.status_code}")

    if response.mhtml_data:
      print(f"\nMHTML capture successful. Size: {len(response.mhtml_data)} bytes.")
      print(f"HTML (first 200 chars):\n{response.mhtml_data[:200]}...")
    else:
      print("\nNo MHTML data captured.")
if __name__ == "__main__":
  asyncio.run(main())