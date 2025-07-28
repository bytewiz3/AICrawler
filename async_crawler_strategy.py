from .async_configs import BrowserConfig, CrawlerRunConfig
from .browser_manager import BrowserManager
from .models import AsyncCrawlResponse
from typing import Union, List, Dict, Any, Optional
from playwright.async_api import Page, Error, TimeoutError as PlaywrightTimeoutError, Download
import time
import base64
from .async_logger import AsyncLogger
from .js_snippet import load_js_script
from .user_agent_generator import ValidUAGenerator
import re
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os
import asyncio
from .ssl_certificate import SSLCertificate

class AsyncPlaywrightStrategy:
  def __init__(self, browser_config: BrowserConfig = None):
    self.browser_config = browser_config or BrowserConfig()
    self.browser_manager = BrowserManager(browser_config=self.browser_config)
    self.logger = AsyncLogger()
    self.ua_generator = ValidUAGenerator()
    self._downloaded_files: List[str] = []

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

  async def page_need_scroll(self, page: Page) -> bool:
    try:
      need_scroll = await page.evaluate(
        """
        () => {
            const scrollHeight = document.documentElement.scrollHeight;
            const viewportHeight = window.innerHeight;
            return scrollHeight > viewportHeight;
        }
        """
      )
      return need_scroll
    except Exception as e:
      self.logger.warning(
        message="Failed to check scroll need for screenshot: {error}. Defaulting to True for safety.",
        tag="SCREENSHOT",
        params={"error": str(e)},
      )
      return True
    
  async def take_screenshot_naive(self, page: Page) -> str:
    try:
      screenshot_bytes = await page.screenshot(full_page=False)
      return base64.b64encode(screenshot_bytes).decode("utf-8")
    except Exception as e:
      self.logger.error(message="Failed to take naive screenshot: {error}", tag="SCREENSHOT", params={"error": str(e)})
      img = Image.new("RGB", (800, 600), color="black")
      draw = ImageDraw.Draw(img)
      font = ImageFont.load_default()
      error_message = f"Screenshot Failed: {str(e)}"
      draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
      buffered = BytesIO()
      img.save(buffered, format="JPEG")
      return base64.b64encode(buffered.getvalue()).decode("utf-8")
  
  async def take_screenshot_scroller(self, page: Page, screenshot_height_threshold: int) -> str:
    self.logger.info(message="Taking advanced (scrolling/stitching) screenshot.", tag="SCREENSHOT")
    try:
      dimensions = await self.get_page_dimensions(page)
      page_width = dimensions["width"]
      page_height = dimensions["height"]

      segments = []
      viewport_size = page.viewport_size
      if viewport_size is None:
        await page.set_viewport_size(
          {"width": self.browser_config.viewport_width, "height": self.browser_config.viewport_height}
        )
        viewport_size = page.viewport_size

      viewport_height = viewport_size["height"]

      num_segments = (page_height // viewport_height) + (1 if page_height % viewport_height > 0 else 0)
      
      for i in range(num_segments):
        y_offset = i * viewport_height
        await self.safe_scroll(page, 0, y_offset, delay=0.01)
        seg_shot = await page.screenshot(full_page=False)
        img = Image.open(BytesIO(seg_shot)).convert("RGB")
        segments.append(img)

      stitched = Image.new("RGB", (segments[0].width, page_height))
      offset = 0
      for i, img in enumerate(segments):
        paste_height = min(img.height, page_height - offset)
        stitched.paste(img.crop((0, 0, img.width, paste_height)), (0, offset))
        offset += paste_height

      buffered = BytesIO()
      stitched.save(buffered, format="JPEG", quality=85) # Using JPEG for smaller size
      encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
      self.logger.info(message="Advanced screenshot (stitched) captured.", tag="SCREENSHOT")
      return encoded

    except Exception as e:
      error_message = f"Failed to take advanced (scrolling/stitching) screenshot: {str(e)}"
      self.logger.error(message="Advanced screenshot failed: {error}", tag="SCREENSHOT", params={"error": error_message})
      img = Image.new("RGB", (800, 600), color="black")
      draw = ImageDraw.Draw(img)
      font = ImageFont.load_default()
      draw.text((10, 10), error_message, fill=(255, 255, 255), font=font)
      buffered = BytesIO()
      img.save(buffered, format="JPEG")
      return base64.b64encode(buffered.getvalue()).decode("utf-8")
  
  async def take_screenshot(self, page: Page, config: CrawlerRunConfig) -> str:
    need_scroll = await self.page_need_scroll(page)
   
    dimensions = await self.get_page_dimensions(page)
    page_height = dimensions["height"]
    
    if page_height > self.browser_config.screenshot_height_threshold:
      self.logger.info(message="Page height ({ph}px) exceeds screenshot threshold ({thresh}px). Using advanced screenshot.", tag="SCREENSHOT", params={"ph": page_height, "thresh": self.browser_config.screenshot_height_threshold})
      return await self.take_screenshot_scroller(page, self.browser_config.screenshot_height_threshold)
    else:
      self.logger.info(message="Page height ({ph}px) within screenshot threshold. Using naive screenshot (full_page=True if possible).", tag="SCREENSHOT", params={"ph": page_height})
      try:
        screenshot_bytes = await page.screenshot(full_page=True)
        return base64.b64encode(screenshot_bytes).decode("utf-8")
      except Error as e:
        self.logger.warning(
          message="Native full_page screenshot failed ({error}). Falling back to naive viewport capture.",
          tag="SCREENSHOT",
          params={"error": str(e)}
        )
        return await self.take_screenshot_naive(page)

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

  async def csp_compliant_wait(self, page: Page, user_wait_function: str, timeout: float = 3000) -> bool:
    wrapper_js = f"""
    async () => {{
        const userFunction = {user_wait_function};
        const startTime = Date.now();
        try {{
            while (true) {{
                if (await userFunction()) {{
                    return true;
                }}
                if (Date.now() - startTime > {timeout}) {{
                    return false;
                }}
                await new Promise(resolve => setTimeout(resolve, 100));
            }}
        }} catch (error) {{
            throw new Error(`Error evaluating condition: ${{error.message}}`);
        }}
    }}
    """
    try:
      result = await page.evaluate(wrapper_js)
      return result
    except Exception as e:
      self.logger.error(
          message="Failed to evaluate CSP-compliant wait condition: {error}",
          tag="SMART_WAIT",
          params={"error": str(e)}
      )
      return False

  async def smart_wait(self, page: Page, wait_for: str, timeout: float = 30000):
    wait_for = wait_for.strip()

    if wait_for.startswith("js:"):
      js_code = wait_for[3:].strip()
      result = await self.csp_compliant_wait(page, js_code, timeout)
      if not result:
          raise PlaywrightTimeoutError(f"Timeout after {timeout}ms waiting for JS condition '{js_code}'")
      self.logger.info(message="JS wait condition met.", tag="SMART_WAIT")
    elif wait_for.startswith("css:"):
      css_selector = wait_for[4:].strip()
      try:
          await page.wait_for_selector(css_selector, timeout=timeout)
          self.logger.info(message="CSS selector found.", tag="SMART_WAIT")
      except PlaywrightTimeoutError:
          raise PlaywrightTimeoutError(f"Timeout after {timeout}ms waiting for selector '{css_selector}'")
      except Error as e:
          raise ValueError(f"Invalid CSS selector '{css_selector}': {e}")
    else:
      if wait_for.startswith("()") or wait_for.startswith("function"):
        result = await self.csp_compliant_wait(page, wait_for, timeout)
        if not result:
          raise PlaywrightTimeoutError(f"Timeout after {timeout}ms waiting for JS function '{wait_for}'")
        self.logger.info(message="Auto-detected JS wait condition met.", tag="SMART_WAIT")
      else:
        try:
          await page.wait_for_selector(wait_for, timeout=timeout)
          self.logger.info(message="Auto-detected CSS selector found.", tag="SMART_WAIT")
        except PlaywrightTimeoutError:
          raise PlaywrightTimeoutError(f"Timeout after {timeout}ms waiting for selector '{wait_for}'")
        except Error as e:
          self.logger.warning(message="CSS selector failed, attempting as JS function.", tag="SMART_WAIT")
          try:
            result = await self.csp_compliant_wait(page, f"() => {{{wait_for}}}", timeout)
            if not result:
              raise PlaywrightTimeoutError(f"Timeout after {timeout}ms waiting for JS function fallback '{wait_for}'")
            self.logger.info(message="JS function fallback wait condition met.", tag="SMART_WAIT")
          except Exception:
            raise ValueError(
              f"Invalid wait_for parameter: '{wait_for}'. "
              "It should be either a valid CSS selector, a JavaScript function, "
              "or explicitly prefixed with 'js:' or 'css:'."
            )
  
  async def remove_overlay_elements(self, page: Page) -> Dict[str, Any]:
    self.logger.info(message="Attempting to remove overlay elements.", tag="OVERLAY_REMOVAL")
    remove_overlays_js = load_js_script("remove_overlay_elements")
    try:
      removal_result = await page.evaluate(remove_overlays_js)
      await page.wait_for_timeout(500) # Give a brief moment for DOM changes to apply
      self.logger.info(
        message="Overlay removal report: Clicked {clicked} buttons, Removed {removed} elements, Fixed {fixed} fixed elements, Removed {empty_blocks} empty blocks, Scroll enabled: {scroll_enabled}",
        tag="OVERLAY_REMOVAL",
          params={
            "clicked": removal_result.get("clickedCount", 0),
            "removed": removal_result.get("removedCount", 0),
            "fixed": removal_result.get("fixedElementsRemovedCount", 0),
            "empty_blocks": removal_result.get("emptyBlockElementsRemovedCount", 0),
            "scroll_enabled": removal_result.get("scrollReEnabled", False)
          }
        )
      return {"success": True, "details": removal_result}
    except Exception as e:
      self.logger.error(
        message="Failed to remove overlay elements: {error}",
        tag="OVERLAY_REMOVAL",
        params={"error": str(e)},
      )
      return {"success": False, "error": str(e)}

  def _generate_client_hints_from_ua(self, user_agent: str) -> Dict[str, str]:
    headers = {}
    sec_ch_ua_value = self.ua_generator.generate_client_hints(user_agent)
    if sec_ch_ua_value:
      headers['Sec-CH-UA'] = sec_ch_ua_value

    if "Windows NT" in user_agent:
      headers['Sec-CH-UA-Platform'] = '"Windows"'
      headers['Sec-CH-UA-Platform-Version'] = '"10.0"'
    elif "Macintosh" in user_agent:
      headers['Sec-CH-UA-Platform'] = '"macOS"'
      headers['Sec-CH-UA-Platform-Version'] = '"13.0.0"'
    elif "Linux" in user_agent and "Android" not in user_agent:
      headers['Sec-CH-UA-Platform'] = '"Linux"'
      headers['Sec-CH-UA-Platform-Version'] = '""'
    elif "Android" in user_agent:
      headers['Sec-CH-UA-Platform'] = '"Android"'
      match = re.search(r"Android (\d+)", user_agent)
      if match:
        headers['Sec-CH-UA-Platform-Version'] = f'"{match.group(1)}.0.0"'
      else:
        headers['Sec-CH-UA-Platform-Version'] = '"13.0.0"'
        
    headers['Sec-CH-UA-Mobile'] = '?0' if "Mobi" not in user_agent and "Android" not in user_agent and "iPhone" not in user_agent else '?1'

    if "Chrome/" in user_agent:
      chrome_version_match = re.search(r"Chrome/(\d+\.\d+\.\d+\.\d+)", user_agent)
      if chrome_version_match:
        chrome_version = chrome_version_match.group(1)
        headers['Sec-CH-UA-Full-Version-List'] = f'"Chromium";v="{chrome_version}", "Not A(Brand";v="99.0.0.0", "Google Chrome";v="{chrome_version}"'
    elif "Firefox/" in user_agent:
      pass
    
    return headers
  
  async def get_page_dimensions(self, page: Page):
    return await page.evaluate(
      """
      () => {
        const {scrollWidth, scrollHeight} = document.documentElement;
        return {width: scrollWidth, height: scrollHeight};
      }
      """
    )

  async def csp_scroll_to(self, page: Page, x: int, y: int) -> Dict[str, Any]:
    try:
      result = await page.evaluate(
        f"""() => {{
          try {{
            const startX = window.scrollX;
            const startY = window.scrollY;
            window.scrollTo({x}, {y});
            
            const endX = window.scrollX;
            const endY = window.scrollY;
            
            return {{
              success: true,
              startPosition: {{ x: startX, y: startY }},
              endPosition: {{ x: endX, y: endY }},
              targetPosition: {{ x: {x}, y: {y} }},
              delta: {{
                x: Math.abs(endX - {x}),
                y: Math.abs(endY - {y})
              }}
            }};
          }} catch (e) {{
            return {{
              success: false,
              error: e.toString()
            }};
          }}
        }}"""
      )
      if not result["success"]:
        self.logger.warning(
          message="Scroll operation failed: {error}",
          tag="SCROLL",
          params={"error": result.get("error")},
        )
      return result
    except Exception as e:
      self.logger.error(
        message="Failed to execute scroll: {error}",
        tag="SCROLL",
        params={"error": str(e)},
      )
      return {"success": False, "error": str(e)}

  async def safe_scroll(self, page: Page, x: int, y: int, delay: float = 0.1):
    result = await self.csp_scroll_to(page, x, y)
    if result["success"]:
      await page.wait_for_timeout(delay * 1000) # delay in milliseconds
    return result

  async def _handle_full_page_scan(self, page: Page, scroll_delay: float = 0.1):
    self.logger.info(message="Starting full page scan (scrolling).", tag="PAGE_SCAN")
    try:
      if page.viewport_size is None:
        await page.set_viewport_size(
          {"width": self.browser_config.viewport_width, "height": self.browser_config.viewport_height}
        )
      
      viewport_height = page.viewport_size.get(
        "height", self.browser_config.viewport_height
      )
      current_position = 0

      dimensions = await self.get_page_dimensions(page)
      total_height = dimensions["height"]
      
      self.logger.debug(message="Initial page height: {total_height}, Viewport height: {viewport_height}", tag="PAGE_SCAN", params={"total_height": total_height, "viewport_height": viewport_height})

      while current_position < total_height:
        current_position = min(current_position + viewport_height, total_height)
        await self.safe_scroll(page, 0, current_position, delay=scroll_delay)
        
        new_height = (await self.get_page_dimensions(page))["height"]
        if new_height > total_height:
          self.logger.debug(message="Page height increased to {new_height}.", tag="PAGE_SCAN", params={"new_height": new_height})
          total_height = new_height
        else:
          if current_position >= total_height:
            break

      await self.safe_scroll(page, 0, 0, delay=scroll_delay)
      self.logger.info(message="Full page scan completed.", tag="PAGE_SCAN")

    except Exception as e:
      self.logger.warning(
        message="Failed to perform full page scan: {error}",
        tag="PAGE_SCAN",
        params={"error": str(e)},
      )

  async def _handle_download(self, download: Download):
    try:
      suggested_filename = download.suggested_filename
      download_path = os.path.join(self.browser_config.downloads_path, suggested_filename) #
      
      os.makedirs(self.browser_config.downloads_path, exist_ok=True)

      self.logger.info(
        message="Downloading {filename} to {path}",
        tag="DOWNLOAD",
        params={"filename": suggested_filename, "path": download_path},
      )

      start_time = time.perf_counter()
      await download.save_as(download_path)
      end_time = time.perf_counter()
      self._downloaded_files.append(download_path)

      self.logger.info(
        message="Downloaded {filename} successfully in {duration:.2f}s",
        tag="DOWNLOAD",
        params={
          "filename": suggested_filename,
          "path": download_path,
          "duration": end_time - start_time,
        },
      )
    except Exception as e:
      self.logger.error(
        message="Failed to handle download: {error}",
        tag="DOWNLOAD_ERROR",
        params={"error": str(e)},
      )
  
  async def capture_mhtml(self, page: Page) -> Optional[str]:
    self.logger.info(message="Capturing page as MHTML.", tag="MHTML_CAPTURE")
    try:
      try:
        await page.wait_for_load_state("domcontentloaded", timeout=5000)
        await page.wait_for_load_state("networkidle", timeout=5000)
        await page.wait_for_timeout(1000)
      except PlaywrightTimeoutError:
        self.logger.warning(message="Wait for load state timed out before MHTML capture.", tag="MHTML_CAPTURE")
      except Exception as e:
        self.logger.warning(message="Error during pre-MHTML load state wait: {error}", tag="MHTML_CAPTURE", params={"error": str(e)})
      cdp_session = await page.context.new_cdp_session(page)
      result = await cdp_session.send("Page.captureSnapshot", {"format": "mhtml"})
      mhtml_content = result.get("data")
      await cdp_session.detach()
      if mhtml_content:
        self.logger.info(message="MHTML capture complete. Size: {size} bytes.", tag="MHTML_CAPTURE", params={"size": len(mhtml_content)})
      else:
        self.logger.warning(message="MHTML capture returned no data.", tag="MHTML_CAPTURE")
      return mhtml_content
    except Exception as e:
      self.logger.error(message="Failed to capture MHTML: {error}", tag="MHTML_CAPTURE_ERROR", params={"error": str(e)},)
      return None

  async def crawl(self, url: str, config: Optional[CrawlerRunConfig] = None) -> AsyncCrawlResponse:
    config = config or CrawlerRunConfig()

    user_agent_to_set: Optional[str] = None
    if config.user_agent:
      user_agent_to_set = config.user_agent
      self.logger.info(message="Using explicit User-Agent: {ua}", tag="USER_AGENT", params={"ua": user_agent_to_set})
    elif config.user_agent_mode == "random" or config.magic:
      user_agent_to_set = self.ua_generator.generate( 
        **(config.user_agent_generator_config or {})
      )
      self.logger.info(message="Using random User-Agent: {ua}", tag="USER_AGENT", params={"ua": user_agent_to_set})
  
    context_options = {}
    if user_agent_to_set:
      context_options["user_agent"] = user_agent_to_set

    if user_agent_to_set:
      client_hints = self._generate_client_hints_from_ua(user_agent_to_set)
      if client_hints:
        context_options['extra_http_headers'] = {
          **context_options.get('extra_http_headers', {}),
          **client_hints
        }
        self.logger.info(message="Added Client Hints: {hints}", tag="CLIENT_HINTS", params={"hints": client_hints})
    
    if self.browser_config.accept_downloads: 
      context_options['accept_downloads'] = True
      self.logger.info(message="Accepting downloads to: {path}", tag="DOWNLOAD", params={"path": self.browser_config.downloads_path})

    context = await self.browser_manager._browser_instance.new_context(**context_options)
    page = await context.new_page()

    self._downloaded_files = []

    download_completed_event = asyncio.Event() 
    async def _download_completion_wrapper(download_obj: Download):
      try:
        await self._handle_download(download_obj)
      finally:
        download_completed_event.set()

    if self.browser_config.accept_downloads:
      page.on("download", _download_completion_wrapper)
      self.logger.debug(message="Attached download listener to page.", tag="DOWNLOAD")

    if config.override_navigator or config.magic:
      self.logger.info(message="Adding navigator override init script.", tag="SPOOFING")
      await context.add_init_script(load_js_script("navigator_overrider"))

    if config.simulate_user or config.magic:
      self.logger.info(message="Simulating basic user interaction (mouse/keyboard).", tag="SPOOFING")
      await page.mouse.move(random.randint(50, 200), random.randint(50, 200))
      await page.mouse.down()
      await page.mouse.up()
      await page.keyboard.press("ArrowDown")
      await page.wait_for_timeout(random.uniform(500, 1500))

    js_execution_result = None
    captured_requests = []
    screenshot_data = None
    captured_console = []

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

    if config.capture_console_messages:
      def handle_console_capture(msg):
        try:
          entry = {
            "type": msg.type,
            "text": msg.text,
            "timestamp": time.time()
          }
          captured_console.append(entry)
        except Exception as e:
          self.logger.warning(
            message="Error capturing console message: {error}",
            tag="CONSOLE_CAPTURE",
            params={"error": str(e)}
          )

      def handle_pageerror_capture(err):
        try:
          entry = {
            "type": "error",
            "text": err.message,
            "stack": err.stack,
            "timestamp": time.time()
          }
          captured_console.append(entry)
        except Exception as e:
          self.logger.warning(
            message="Error capturing page error: {error}",
            tag="CONSOLE_CAPTURE",
            params={"error": str(e)}
          )

      page.on("console", handle_console_capture)
      page.on("pageerror", handle_pageerror_capture)
      self.logger.debug(message="Attached console message and page error listeners.", tag="CONSOLE_CAPTURE")    
     
    is_direct_download_url = url.lower().endswith(('.pdf', '.zip', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg', '.gif', '.mp4', '.mp3'))

    try:
      if config.fetch_ssl_certificate and url.startswith("https://"):
        self.logger.info(message="Attempting to fetch SSL certificate for {url}.", tag="SSL_FETCH", params={"url": url})
        ssl_cert = SSLCertificate.from_url(url)
        if ssl_cert:
          self.logger.info(message="SSL certificate fetched successfully from {url}. Issuer: {issuer}", tag="SSL_FETCH", params={"url": url, "issuer": ssl_cert.issuer})
        else:
          self.logger.warning(message="Failed to fetch SSL certificate for {url}.", tag="SSL_FETCH", params={"url": url})
        
      self.logger.info(message="Navigating to {url}", tag="GOTO", params={"url": url})
      response = None
      try:
        response = await page.goto(url=url, wait_until=config.wait_until, timeout=config.page_timeout)
        self.logger.info(message="Navigation complete, status: {status}", tag="GOTO", params={"status": response.status if response else 'N/A'})
        if config.js_code:
          js_execution_result = await self.robust_execute_user_script(page, config.js_code)
          if not js_execution_result.get("success"):
            print(f"WARNING: JavaScript execution had issues: {js_execution_result.get('results')}")

        if config.remove_overlay_elements:
          await self.remove_overlay_elements(page)
          
        if config.wait_for:
          self.logger.info(message="Applying smart wait condition: {condition}", tag="SMART_WAIT", params={"condition": config.wait_for})
          try:
            await self.smart_wait(page, config.wait_for, timeout=config.page_timeout)
          except (PlaywrightTimeoutError, ValueError) as e:
            self.logger.error(message="Smart wait condition failed: {error}", tag="SMART_WAIT", params={"error": str(e)})
            raise

        if config.process_iframes:
          self.logger.info(message="Initiating iframe processing.", tag="IFRAME")
          page = await self.process_iframes(page)

        if config.capture_mhtml:
          mhtml_data = await self.capture_mhtml(page)
            
        if config.screenshot:
          self.logger.info(message="Taking screenshot (intelligent).", tag="SCREENSHOT")
          screenshot_data = await self.take_screenshot(page, config)
          if screenshot_data:
            self.logger.info(message="Screenshot captured. Data size: {size} KB", tag="SCREENSHOT", params={"size": len(screenshot_data) // 1024})
          else:
            self.logger.warning(message="No screenshot data captured.", tag="SCREENSHOT")
      
        final_html = ""
        final_status_code = 0
        if response:
          try:
            final_html = await page.content()
            final_status_code = response.status
          except Error as content_error:
            self.logger.warning(message="Could not get HTML content after navigation (likely a direct download): {error}", tag="HTML_RETRIEVAL", params={"error": str(content_error)})
            final_html = ""
            final_status_code = response.status if response.status else 200
        elif is_direct_download_url and download_completed_event.is_set():
          final_html = ""
          final_status_code = 200 
        else:
          final_html = ""
          final_status_code = 0

      except Error as e:
        if "net::ERR_ABORTED" in str(e) and self.browser_config.accept_downloads and is_direct_download_url:
          self.logger.warning(
            message="Navigation aborted for download URL: {url}. Waiting for download completion.",
            tag="GOTO_ABORTED",
            params={"url": url}
          )
          try:
            await asyncio.wait_for(download_completed_event.wait(), timeout=config.page_timeout)
            self.logger.info(message="Download completion confirmed.", tag="DOWNLOAD")
            response = type('obj', (object,), {'status': 200, 'url': url, 'headers': {}})()
          except asyncio.TimeoutError:
            self.logger.error(message="Timeout waiting for download completion for {url}.", tag="DOWNLOAD_TIMEOUT", params={"url": url})
            raise
          except Exception as inner_e:
            self.logger.error(message="Error during direct download handling for {url}: {error}", tag="DOWNLOAD_ERROR", params={"url": url, "error": str(inner_e)})
            return AsyncCrawlResponse(
              html="", status_code=0, js_execution_result={"success": False, "error": f"Download handling error: {str(inner_e)}"},
              network_requests=captured_requests if config.capture_network_requests else None,
              console_messages=captured_console if config.capture_console_messages else None,
              screenshot=None, downloaded_files=self._downloaded_files if self._downloaded_files else None
            )
        else:
          self.logger.error(message="Playwright navigation error: {error}", tag="GOTO_ERROR", params={"error": str(e)})
          return AsyncCrawlResponse(
            html="", status_code=0, js_execution_result={"success": False, "error": f"Navigation failed: {str(e)}"},
            network_requests=captured_requests if config.capture_network_requests else None,
            console_messages=captured_console if config.capture_console_messages else None,
            screenshot=None, downloaded_files=self._downloaded_files if self._downloaded_files else None,
            mhtml_data=mhtml_data
          )

      return AsyncCrawlResponse(
        html=final_html,
        status_code=final_status_code,
        js_execution_result=js_execution_result,
        network_requests=captured_requests if config.capture_network_requests else None,
        console_messages=captured_console if config.capture_console_messages else None,
        screenshot=screenshot_data,
        downloaded_files=self._downloaded_files if self._downloaded_files else None,
        ssl_certificate=ssl_cert if config.fetch_ssl_certificate else None,
        mhtml_data=mhtml_data
      )
    
    except Exception as e:
      self.logger.error(message="Crawl failed for {url}: {error}", tag="CRAWL_ERROR", params={"url": url, "error": str(e)})
      return AsyncCrawlResponse(
        html="", status_code=0, js_execution_result={"success": False, "error": f"Overall crawl failed: {str(e)}"},
        network_requests=captured_requests if config.capture_network_requests else None,
        console_messages=captured_console if config.capture_console_messages else None,
        screenshot=None, downloaded_files=self._downloaded_files if self._downloaded_files else None,
        ssl_certificate=ssl_cert if config.fetch_ssl_certificate else None,
        mhtml_data=mhtml_data
      )
    
    finally:
      if self.browser_config.accept_downloads:
        page.remove_listener("download", _download_completion_wrapper)
      if config.capture_network_requests:
        page.remove_listener("request", handle_request_capture)
        page.remove_listener("response", handle_response_capture)
      if config.capture_console_messages:
        page.remove_listener("console", handle_console_capture)
        page.remove_listener("pageerror", handle_pageerror_capture)
      await page.close()
      await context.close()

