from typing import Optional, Dict, Any, List

class AsyncCrawlResponse:
  def __init__(self, html: str, status_code: int, js_execution_result: Optional[Dict[str, Any]] = None, 
    network_requests: Optional[list[Dict[str, Any]]] = None, screenshot: Optional[str] = None,
    downloaded_files: Optional[List[str]] = None):
    self.html = html
    self.status_code = status_code
    self.js_execution_result = js_execution_result
    self.network_requests = network_requests
    self.screenshot = screenshot
    self.downloaded_files = downloaded_files
