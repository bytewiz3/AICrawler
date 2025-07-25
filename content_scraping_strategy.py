from abc import ABC, abstractmethod
from .async_logger import AsyncLogger
from .models import ScrapingResult

class ScrapingStrategy(ABC):
  """Abstract base class for scraping strategies."""
  def __init__(self): self.logger = AsyncLogger() # A logger is needed
  @abstractmethod
  def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult: pass

class NoScrapingStrategy(ScrapingStrategy):
  """A no-op scraping strategy, just returns cleaned HTML as raw."""
  def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
    return ScrapingResult(
      cleaned_html=html,
      links={"internal": [], "external": []},
      media={},
      metadata={}
    )