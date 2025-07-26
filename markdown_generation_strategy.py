from abc import ABC, abstractmethod
import html2text
from typing import Optional
from .models import MarkdownGenerationResult
from .content_filter_strategy import ContentFilterStrategy, NoContentFilter


class MarkdownGenerationStrategy(ABC):
  def __init__(self, content_filter: Optional[ContentFilterStrategy] = None):
      self.content_filter = content_filter or NoContentFilter()
  @abstractmethod
  def generate_markdown(self, input_html: str, base_url: str = "") -> MarkdownGenerationResult: pass

class DefaultMarkdownGenerator(MarkdownGenerationStrategy):
  def __init__(self, content_filter: Optional[ContentFilterStrategy] = None):
      super().__init__(content_filter)
      self.h = html2text.HTML2Text()
      self.h.ignore_images = False
      self.h.ignore_links = False
      self.h.body_width = 0
      self.h.single_line_break = True

  def generate_markdown(self, input_html: str, base_url: str = "") -> MarkdownGenerationResult:
      if not input_html:
          return MarkdownGenerationResult(raw_markdown="")
      try:
          markdown_content = self.h.handle(input_html)
          markdown_content = self.content_filter.filter(markdown_content)
          return MarkdownGenerationResult(raw_markdown=markdown_content)
      except Exception:
          return MarkdownGenerationResult(raw_markdown="")