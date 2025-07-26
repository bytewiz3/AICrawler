from abc import ABC, abstractmethod

class ContentFilterStrategy(ABC):
    @abstractmethod
    def filter(self, text: str) -> str: pass

class NoContentFilter(ContentFilterStrategy):
    def filter(self, text: str) -> str: return text