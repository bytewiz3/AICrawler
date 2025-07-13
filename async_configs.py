from typing import Optional, Union, List

class BrowserConfig:
  def __init__(self, headless: bool = True, timeout: int = 6000):
    self.headless = headless
    self.timeout = timeout

class CrawlerRunConfig:
  def __init__(self, wait_until: str = "load", page_timeout: int = 6000, js_code: Optional[Union[str, List[str]]] = None, capture_network_requests: bool = False, screenshot: bool = False):
    self.wait_until = wait_until
    self.page_timeout = page_timeout
    self.js_code = js_code
    self.capture_network_requests = capture_network_requests
    self.screenshot = screenshot
    