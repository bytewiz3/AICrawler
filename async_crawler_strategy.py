from .async_configs import BrowserConfig, CrawlerRunConfig
from .browser_manager import BrowserManager
from .models import AsyncCrawlResponse

class AsyncPlaywrightStrategy:
  def __init__(self, browser_config: BrowserConfig = None):
    self.browser_config = browser_config or BrowserConfig()
    self.browser_manager = BrowserManager(browser_config=self.browser_config)

  async def __aenter__(self):
    await self.browser_manager.start()
    return self

  async def __aexit__(self, exc_type, exc_value, exc_tb):
    await self.browser_manager.close()

  async def crawl(self, url: str) -> AsyncCrawlResponse:
    config = CrawlerRunConfig()
    page, context = await self.browser_manager.get_page()
    try:
        response = await page.goto(url=url, wait_until=config.wait_until, timeout=config.page_timeout)
        html = await page.content()
        status_code = response.status if response else 200

        return AsyncCrawlResponse(html=html, status_code=status_code)
    
    finally:
      await page.close()
      await context.close()

