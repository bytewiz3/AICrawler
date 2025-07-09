class AsyncCrawlResponse:
  def __init__(self, html: str, status_code: int):
    self.html = html
    self.status_code = status_code
