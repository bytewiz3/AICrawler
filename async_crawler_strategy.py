from .async_configs import BrowserConfig, CrawlerRunConfig
from .browser_manager import BrowserManager
from .models import AsyncCrawlResponse
from typing import Union, List, Dict, Any, Optional
from playwright.async_api import Page

class AsyncPlaywrightStrategy:
  def __init__(self, browser_config: BrowserConfig = None):
    self.browser_config = browser_config or BrowserConfig()
    self.browser_manager = BrowserManager(browser_config=self.browser_config)

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

  async def crawl(self, url: str, config: Optional[CrawlerRunConfig] = None) -> AsyncCrawlResponse:
    config = config or CrawlerRunConfig()
    page, context = await self.browser_manager.get_page()
    js_execution_result = None

    try:
        response = await page.goto(url=url, wait_until=config.wait_until, timeout=config.page_timeout)

        if config.js_code:
          js_execution_result = await self.robust_execute_user_script(page, config.js_code)
          if not js_execution_result.get("success"):
            print(f"WARNING: JavaScript execution had issues: {js_execution_result.get('results')}")

        html = await page.content()
        status_code = response.status if response else 200

        return AsyncCrawlResponse(html=html, status_code=status_code, js_execution_result=js_execution_result)
    
    finally:
      await page.close()
      await context.close()

