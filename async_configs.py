class BrowserConfig:
  def __init__(self, headless: bool = True, timeout: int = 6000):
    self.headless = headless
    self.timeout = timeout

class CrawlerRunConfig:
  def __init__(self, wait_until: str = "load", page_timeout: int = 6000):
    self.wait_until = wait_until
    self.page_timeout = page_timeout

