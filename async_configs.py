from typing import Optional, Union, List, Literal, Dict, Any

class BrowserConfig:
  def __init__(self, headless: bool = True, timeout: int = 6000, user_agent: Optional[str] = None):
    self.headless = headless
    self.timeout = timeout
    self.user_agent = user_agent

class CrawlerRunConfig:
  def __init__(
    self, wait_until: str = "load", page_timeout: int = 6000, js_code: Optional[Union[str, List[str]]] = None, 
    capture_network_requests: bool = False, screenshot: bool = False, process_iframes: bool = False, 
    wait_for: Optional[str] = None, remove_overlay_elements: bool = False,
     user_agent_mode: Literal["default", "random"] = "default", user_agent_generator_config: Optional[Dict[str, Any]] = None, 
     user_agent: Optional[str] = None
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


    