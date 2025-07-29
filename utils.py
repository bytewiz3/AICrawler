from .async_logger import AsyncLogger
from typing import Dict
import urllib.robotparser as robotparser
from urllib.parse import urlparse
import asyncio

def fast_format_html(html_content: str) -> str:
  return html_content.strip()

class RobotsParser:
  def __init__(self):
    self._parser_cache: Dict[str, robotparser.RobotFileParser] = {}
    self.logger = AsyncLogger()

  async def can_fetch(self, url: str, user_agent: str) -> bool:
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_txt_url = f"{base_url}/robots.txt"

    if base_url not in self._parser_cache:
      parser = robotparser.RobotFileParser()
      parser.set_url(robots_txt_url)
        
      try:
        await asyncio.to_thread(parser.read)
        self._parser_cache[base_url] = parser
        self.logger.info(f"Loaded robots.txt from {robots_txt_url}", tag="ROBOTS")
      except Exception as e:
        self.logger.warning(f"Failed to load robots.txt from {robots_txt_url}: {e}. Assuming allowed.", tag="ROBOTS_WARN")
        self._parser_cache[base_url] = None # Cache None to avoid repeated failures for this domain
        return True

    parser = self._parser_cache.get(base_url)
    if parser is None:
      return True

    allowed = parser.can_fetch(user_agent, url)
    if not allowed:
      self.logger.warning(f"Access to {url} denied by robots.txt for User-Agent: {user_agent}", tag="ROBOTS_BLOCKED")
    else:
      self.logger.debug(f"Access to {url} allowed by robots.txt for User-Agent: {user_agent}", tag="ROBOTS_ALLOWED")
    
    return allowed