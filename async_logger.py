from typing import Optional, Dict

class AsyncLogger:
  def info(self, message: str, tag: str, params: Optional[Dict] = None):
    formatted_message = message.format(**params) if params else message
    print(f"[{tag}] INFO: {formatted_message}")

  def warning(self, message: str, tag: str, params: Optional[Dict] = None):
    formatted_message = message.format(**params) if params else message
    print(f"[{tag}] WARNING: {formatted_message}")

  def error(self, message: str, tag: str, params: Optional[Dict] = None):
    formatted_message = message.format(**params) if params else message
    print(f"[{tag}] ERROR: {formatted_message}")

  def debug(self, message: str, tag: str, params: Optional[Dict] = None):
    # Adding debug for completeness, as seen in original
    formatted_message = message.format(**params) if params else message
    print(f"[{tag}] DEBUG: {formatted_message}")