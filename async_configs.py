from typing import Optional, Union, List, Literal, Dict, Any
import tempfile
from .content_scraping_strategy import NoScrapingStrategy, ScrapingStrategy
from .markdown_generation_strategy import DefaultMarkdownGenerator, MarkdownGenerationStrategy

class BrowserConfig:
  def __init__(self, headless: bool = True, timeout: int = 6000, user_agent: Optional[str] = None, 
    viewport_width: int = 1920, viewport_height: int = 1080, screenshot_height_threshold: int = 15000,
    accept_downloads: bool = False, downloads_path: Optional[str] = None):
    self.headless = headless
    self.timeout = timeout
    self.user_agent = user_agent
    self.viewport_width = viewport_width
    self.viewport_height = viewport_height
    self.screenshot_height_threshold = screenshot_height_threshold
    self.accept_downloads = accept_downloads
    self.downloads_path = downloads_path if downloads_path else tempfile.gettempdir()

class CrawlerRunConfig:
  def __init__(
    self, wait_until: str = "load", page_timeout: int = 6000, js_code: Optional[Union[str, List[str]]] = None, 
    capture_network_requests: bool = False, screenshot: bool = False, process_iframes: bool = False, 
    wait_for: Optional[str] = None, remove_overlay_elements: bool = False,
     user_agent_mode: Literal["default", "random"] = "default", user_agent_generator_config: Optional[Dict[str, Any]] = None, 
     user_agent: Optional[str] = None, override_navigator: bool = False, simulate_user: bool = False, magic: bool = False, 
     scan_full_page: bool = False, scroll_delay: float = 0.1, capture_console_messages: bool = False, 
     scraping_strategy: Optional[ScrapingStrategy] = None, markdown_generator: Optional[MarkdownGenerationStrategy] = None,
     prettify: bool = False, fetch_ssl_certificate: bool = False, capture_mhtml: bool = False
  ):
    self.wait_until = wait_until
    self.page_timeout = page_timeout
    self.js_code = js_code
    self.capture_network_requests = capture_network_requests
    self.screenshot = screenshot
    self.process_iframes = process_iframes
    self.wait_for = wait_for
    self.remove_overlay_elements = remove_overlay_elements
    self.user_agent_mode = user_agent_mode
    self.user_agent_generator_config = user_agent_generator_config
    self.user_agent = user_agent
    self.override_navigator = override_navigator
    self.simulate_user = simulate_user
    self.magic = magic
    self.scan_full_page = scan_full_page
    self.scroll_delay = scroll_delay
    self.capture_console_messages = capture_console_messages
    self.scraping_strategy = scraping_strategy or NoScrapingStrategy() 
    self.markdown_generator = markdown_generator or DefaultMarkdownGenerator()
    self.prettify = prettify
    self.fetch_ssl_certificate = fetch_ssl_certificate
    self.capture_mhtml = capture_mhtml