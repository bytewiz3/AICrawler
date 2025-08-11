from abc import ABC, abstractmethod
from .async_logger import AsyncLogger
from .models import ScrapingResult, Media, MediaItem, Links, Link
import re
from lxml import etree
from lxml import html as lhtml
import asyncio
from typing import Dict, Any

class ScrapingStrategy(ABC):
  """Abstract base class for scraping strategies."""
  def __init__(self): self.logger = AsyncLogger()

  @abstractmethod
  def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
    pass

  @abstractmethod
  async def ascrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
    pass

class LXMLWebScrapingStrategy(ScrapingStrategy):
  def __init__(self, logger=None):
    self.logger = logger
    self.DIMENSION_REGEX = re.compile(r"(\d+)(\D*)")
    self.BASE64_PATTERN = re.compile(r'data:image/[^;]+;base64,([^"]+)')

  def _log(self, level, message, tag="SCRAPE", **kwargs):
    if self.logger:
      log_method = getattr(self.logger, level)
      log_method(message=message, tag=tag, **kwargs)

  def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
    actual_url = kwargs.get("redirected_url", url)
    raw_result = self._scrap(actual_url, html, is_async=False, **kwargs)
    if raw_result is None:
      return ScrapingResult(
        cleaned_html="",
        success=False,
        media=Media(),
        links=Links(),
        metadata={},
      )

    media = Media(
      images=[
        MediaItem(**img)
        for img in raw_result.get("media", {}).get("images", [])
        if img
      ],
      videos=[
        MediaItem(**vid)
        for vid in raw_result.get("media", {}).get("videos", [])
        if vid
      ],
      audios=[
        MediaItem(**aud)
        for aud in raw_result.get("media", {}).get("audios", [])
        if aud
      ],
      tables=raw_result.get("media", {}).get("tables", [])
    )

    links = Links(
      internal=[
        Link(**link)
        for link in raw_result.get("links", {}).get("internal", [])
        if link
      ],
      external=[
        Link(**link)
        for link in raw_result.get("links", {}).get("external", [])
        if link
      ],
    )

    return ScrapingResult(
      cleaned_html=raw_result.get("cleaned_html", ""),
      success=raw_result.get("success", False),
      media=media,
      links=links,
      metadata=raw_result.get("metadata", {}),
    )
  
  async def ascrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
    return await asyncio.to_thread(self.scrap, url, html, **kwargs)
  
  def process_element(self, url, element: lhtml.HtmlElement, **kwargs) -> Dict[str, Any]:
    media = {"images": [], "videos": [], "audios": [], "tables": []}
    internal_links_dict = {}
    external_links_dict = {}
    self._process_element(
        url, element, media, internal_links_dict, external_links_dict, **kwargs
    )
    return {
        "media": media,
        "internal_links_dict": internal_links_dict,
        "external_links_dict": external_links_dict,
    }