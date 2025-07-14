from .async_configs import BrowserConfig, CrawlerRunConfig
from .browser_manager import BrowserManager
from .models import AsyncCrawlResponse
from typing import Union, List, Dict, Any, Optional
from playwright.async_api import Page, Error, TimeoutError as PlaywrightTimeoutError
import time
import base64
from .async_logger import AsyncLogger

class AsyncPlaywrightStrategy:
  def __init__(self, browser_config: BrowserConfig = None):
    self.browser_config = browser_config or BrowserConfig()
    self.browser_manager = BrowserManager(browser_config=self.browser_config)
    self.logger = AsyncLogger()

  async def __aenter__(self):
    await self.browser_manager.start()
    return self

  async def __aexit__(self, exc_type, exc_value, exc_tb):
    await self.browser_manager.close()

  async def robust_execute_user_script(self, page: Page, js_code: Union[str, List[str]]) -> Dict[str, Any]:
    results = []
    scripts = [js_code] if isinstance(js_code, str) else js_code

    for script in scripts:
      try:
        await page.evaluate(script)

        try:
            await page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            try:
                await page.wait_for_timeout(3000)
            except Exception:
                pass

        results.append({"success": True, "script": script})
      except Exception as e:
        results.append({"success": False, "script": script, "error": str(e)})
    return {"success": all(r.get("success", False) for r in results), "results": results}

  async def take_screenshot_naive(self, page: Page) -> str:
    try:
      screenshot_bytes = await page.screenshot(full_page=False)
      return base64.b64encode(screenshot_bytes).decode("utf-8")
    except Exception as e:
      print(f"ERROR: Failed to take screenshot: {e}")
      return ""
    
  async def process_iframes(self, page: Page) -> Page:
    self.logger.info(message="Starting iframe processing.", tag="IFRAME")
    iframes = await page.query_selector_all("iframe")

    if not iframes:
        self.logger.info(message="No iframes found on the page.", tag="IFRAME")
        return page

    for i, iframe in enumerate(iframes):
        try:
            await iframe.evaluate(f'(element) => element.id = "AICrawler-iframe-{i}"')

            frame = await iframe.content_frame()

            if frame:
                self.logger.debug(message="Accessing frame {index}, URL: {url}", tag="IFRAME", params={"index": i, "url": frame.url})
                await frame.wait_for_load_state("load", timeout=3000)

                iframe_content = await frame.evaluate("() => document.body.innerHTML")
                self.logger.debug(message="Extracted {length} bytes from iframe {index}", tag="IFRAME", params={"length": len(iframe_content), "index": i})

                _iframe_content_escaped = iframe_content.replace("`", "\\`")
                await page.evaluate(
                    f"""
                    () => {{
                        const iframe = document.getElementById('AICrawler-iframe-{i}');
                        if (iframe) {{
                            const div = document.createElement('div');
                            div.innerHTML = `{_iframe_content_escaped}`;
                            div.className = 'AICrawler-extracted-iframe-content';
                            iframe.replaceWith(div);
                            console.log('Replaced iframe {i} with extracted content div.');
                        }}
                    }}
                    """
                )
                self.logger.info(message="Successfully processed and replaced iframe {index}.", tag="IFRAME", params={"index": i})
            else:
                self.logger.warning(
                    message="Could not access content frame for iframe {index}. Skipping.",
                    tag="IFRAME",
                    params={"index": i},
                )
        except PlaywrightTimeoutError as e:
            self.logger.warning(
                message="Timeout waiting for iframe {index} to load: {error}",
                tag="IFRAME",
                params={"index": i, "error": str(e)},
            )
        except Error as e:
            # Catch Playwright-specific errors (e.g., 'Execution context was destroyed')
            self.logger.error(
                message="Playwright error processing iframe {index}: {error}",
                tag="IFRAME",
                params={"index": i, "error": str(e)},
            )
        except Exception as e:
            # Catch any other unexpected errors
            self.logger.error(
                message="General error processing iframe {index}: {error}",
                tag="IFRAME",
                params={"index": i, "error": str(e)},
            )
    self.logger.info(message="Finished iframe processing.", tag="IFRAME")
    return page

  async def crawl(self, url: str, config: Optional[CrawlerRunConfig] = None) -> AsyncCrawlResponse:
    config = config or CrawlerRunConfig()
    page, context = await self.browser_manager.get_page()
    js_execution_result = None
    captured_requests = []
    screenshot_data = None

    if config.capture_network_requests:
      def handle_request_capture(request):
        captured_requests.append({
            "event_type": "request",
            "url": request.url,
            "method": request.method,
            "resource_type": request.resource_type,
            "timestamp": time.time()
        })

      def handle_response_capture(response):
        captured_requests.append({
           "event_type": "response",
           "url": response.url,
           "status": response.status,
           "timestamp": time.time()
        })
      
      page.on("request", handle_request_capture)
      page.on("response", handle_response_capture)

    try:
        response = await page.goto(url=url, wait_until=config.wait_until, timeout=config.page_timeout)

        if config.js_code:
          js_execution_result = await self.robust_execute_user_script(page, config.js_code)
          if not js_execution_result.get("success"):
            print(f"WARNING: JavaScript execution had issues: {js_execution_result.get('results')}")

        if config.process_iframes:
          self.logger.info(message="Initiating iframe processing.", tag="IFRAME")
          page = await self.process_iframes(page)

        if config.screenshot:
          screenshot_data = await self.take_screenshot_naive(page)
          if screenshot_data:
            print(f"INFO: Screenshot captured for {url}. Data size: {len(screenshot_data) // 1024} KB")
          else:
            print(f"WARNING: No screenshot data captured for {url}.")

        html = await page.content()
        status_code = response.status if response else 200

        return AsyncCrawlResponse(
          html=html, 
          status_code=status_code, 
          js_execution_result=js_execution_result,
          network_requests=captured_requests if config.capture_network_requests else None,
          screenshot=screenshot_data
        )
    
    except Exception as e:
      self.logger.error(message="Crawl failed for {url}: {error}", tag="CRAWL_ERROR", params={"url": url, "error": str(e)})
      raise
    
    finally:
      if config.capture_network_requests:
        page.remove_listener("request", handle_request_capture)
        page.remove_listener("response", handle_response_capture)
      await page.close()
      await context.close()

