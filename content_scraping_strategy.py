from abc import ABC, abstractmethod
from .async_logger import AsyncLogger
from .models import ScrapingResult, Media, MediaItem, Links, Link

class ScrapingStrategy(ABC):
  """Abstract base class for scraping strategies."""
  def __init__(self): self.logger = AsyncLogger() # A logger is needed
  @abstractmethod
  def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult: pass

class WebScrapingStrategy(ScrapingStrategy):
  def __init__(self, logger=None):
    self.logger = logger

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