from .async_crawler_strategy import AsyncPlaywrightStrategy
from .async_configs import CrawlerRunConfig, BrowserConfig
from typing import Optional, List
from .async_logger import AsyncLogger
import time
from .models import CrawlResult, ScrapingResult, MarkdownGenerationResult
from .utils import fast_format_html, RobotsParser
import asyncio

class AsyncWebCrawler:
  def __init__(
    self,
    crawler_strategy: Optional[AsyncPlaywrightStrategy] = None,
    config: Optional[BrowserConfig] = None,
    logger: Optional[AsyncLogger] = None,
  ):
    self.browser_config = config or BrowserConfig()
    self.logger = logger or AsyncLogger()
    self.crawler_strategy = crawler_strategy or AsyncPlaywrightStrategy(
      browser_config=self.browser_config
    )
    self.ready = False
    self.robots_parser = RobotsParser()

  async def start(self):
    if not self.ready:
      await self.crawler_strategy.__aenter__()
      self.logger.info("AsyncWebCrawler started.", tag="INIT")
      self.ready = True
    return self

  async def close(self):
    if self.ready:
      await self.crawler_strategy.__aexit__(None, None, None)
      self.logger.info("AsyncWebCrawler closed.", tag="CLOSE")
      self.ready = False

  async def __aenter__(self):
    return await self.start()

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    await self.close()

  async def aprocess_html(
    self,
    url: str,
    html: str,
    config: CrawlerRunConfig,
    screenshot_data: Optional[str] = None,
    pdf_data: Optional[bytes] = None,
    **kwargs,
  ) -> CrawlResult:
    _url_display = url if not url.startswith("raw:") else "Raw HTML"
    start_time = time.perf_counter()

    scraping_strategy = config.scraping_strategy
    
    try:
      scraping_result: ScrapingResult = scraping_strategy.scrap(url, html, **kwargs)
    except Exception as e:
      self.logger.error(f"Scraping strategy failed for {url}: {e}", tag="SCRAPE_ERR")
      return CrawlResult(url=url, html=html, status_code=0, success=False, error_message=f"Scraping failed: {e}")

    cleaned_html = scraping_result.cleaned_html
    links = scraping_result.links
    media = scraping_result.media
    metadata = scraping_result.metadata

    if config.prettify:
      cleaned_html = fast_format_html(cleaned_html)

    markdown_generator = config.markdown_generator
    markdown_input_html = cleaned_html 
    markdown_result: MarkdownGenerationResult = markdown_generator.generate_markdown(
      input_html=markdown_input_html,
      base_url=url
    )
    self.logger.info(f"HTML processing and Markdown generation complete for {_url_display}", tag="PROCESS", params={"timing": time.perf_counter() - start_time})

    return CrawlResult(
      url=url,
      html=html,
      status_code=200,
      success=True,
      error_message="",
      cleaned_html=cleaned_html,
      links=links,
      metadata=metadata,
      screenshot=screenshot_data,
      markdown=markdown_result,
    )

  async def arun_many(self, urls: List[str], config: Optional[CrawlerRunConfig] = None) -> List[CrawlResult]:
    if not self.ready: 
      await self.start()
    config = config or CrawlerRunConfig()
    
    self.logger.info(f"Starting concurrent crawl for {len(urls)} URLs.", tag="ARUN_MANY")
    start_time = time.perf_counter()
    
    tasks = [self.arun(url, config) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    final_results = []
    for result in results:
      if isinstance(result, Exception):
        self.logger.error(f"Error during concurrent crawl: {result}", tag="ARUN_MANY_ERROR")
        final_results.append(CrawlResult(url="", html="", status_code=0, success=False, error_message=str(result)))
      else:
        final_results.append(result)

    self.logger.info(f"Finished concurrent crawl for {len(urls)} URLs in {time.perf_counter() - start_time:.2f}s", tag="ARUN_MANY")
    
    return final_results

  async def arun(
    self,
    url: str,
    config: Optional[CrawlerRunConfig] = None,
    **kwargs,
  ) -> CrawlResult:
    if not self.ready:
      await self.start()

    config = config or CrawlerRunConfig()

    self.logger.info(f"Starting single crawl for: {url}", tag="ARUN")
    start_time = time.perf_counter()

    if url.startswith(("http://", "https://")) and config.check_robots_txt:
      ua_for_robots = config.user_agent or self.crawler_strategy.ua_generator.generate(
        **(config.user_agent_generator_config or {})
      )
      
      if not await self.robots_parser.can_fetch(url, ua_for_robots): #
        return CrawlResult(
          url=url,
          html="",
          status_code=403,
          success=False,
          error_message="Access denied by robots.txt",
          links={"internal":[], "external":[]}
        )

    try:
      async_response = await self.crawler_strategy.crawl(
        url=url,
        config=config,
      )

      crawl_result = CrawlResult(
        url=url,
        html=async_response.html,
        status_code=async_response.status_code,
        success=True, # Assume success if no exception was raised
        downloaded_files=async_response.downloaded_files
      )
      
      self.logger.info(f"Finished single crawl for: {url} (Status: {crawl_result.status_code})", tag="ARUN", params={"timing": time.perf_counter() - start_time})
      return crawl_result

    except Exception as e:
      self.logger.error(f"Error during arun for {url}: {e}", tag="ARUN_ERROR")
      return CrawlResult(
        url=url,
        html="",
        status_code=0,
        success=False,
        error_message=str(e)
      )