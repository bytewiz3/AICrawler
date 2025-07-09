from .async_configs import BrowserConfig
from playwright.async_api import Page, Browser, async_playwright
from typing import Any, Optional

class BrowserManager:
  _playwright_instance = None
  _browser_instance: Optional[Browser] = None

  def __init__(self, browser_config: BrowserConfig):
    self.browser_config = browser_config

  async def start(self):
    if not BrowserManager._playwright_instance:
      BrowserManager._playwright_instance = await async_playwright().start()
    if not BrowserManager._browser_instance:
      BrowserManager._browser_instance = await BrowserManager._playwright_instance.chromium.launch(headless=self.browser_config.headless)

  async def close(self):
    if BrowserManager._browser_instance:
      await BrowserManager._browser_instance.close()
      BrowserManager._browser_instance = None
    if BrowserManager._playwright_instance:
      await BrowserManager._playwright_instance.stop()
      BrowserManager._playwright_instance = None
  
  async def get_page(self) -> tuple[Page, Any]:
    context = await BrowserManager._browser_instance.new_context()
    page = await context.new_page()
    return page, context

