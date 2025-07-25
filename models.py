from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class AsyncCrawlResponse(BaseModel):
  html: str
  js_execution_result: Optional[Dict[str, Any]] = None
  status_code: int
  screenshot: Optional[str] = None
  downloaded_files: Optional[List[str]] = None
  network_requests: Optional[List[Dict[str, Any]]] = None
  console_messages: Optional[List[Dict[str, Any]]] = None

class CrawlResult(BaseModel):
  url: str
  html: str
  js_execution_result: Optional[Dict[str, Any]] = None
  status_code: int
  success: bool
  error_message: Optional[str] = None
  screenshot: Optional[str] = None
  downloaded_files: Optional[List[str]] = None
  network_requests: Optional[List[Dict[str, Any]]] = None
  console_messages: Optional[List[Dict[str, Any]]] = None

class Link(BaseModel):
  href: Optional[str] = ""
  text: Optional[str] = ""
  title: Optional[str] = ""
  head_data: Optional[Dict[str, Any]] = None
  intrinsic_score: Optional[float] = None
  contextual_score: Optional[float] = None
  total_score: Optional[float] = None
  meta: Optional[Dict] = None

class ScrapingResult(BaseModel):
  cleaned_html: str
  media: Dict[str, Any]
  links: Dict[str, List[Link]]
  metadata: Dict[str, Any] = {}
