from typing import Optional, Dict, Any

class AsyncCrawlResponse:
  def __init__(self, html: str, status_code: int, js_execution_result: Optional[Dict[str, Any]] = None, network_requests: Optional[list[Dict[str, Any]]] = None):
    self.html = html
    self.status_code = status_code
    self.js_execution_result = js_execution_result
    self.network_requests = network_requests
