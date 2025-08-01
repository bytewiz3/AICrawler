import re
from abc import ABC, abstractmethod
from typing import List, Optional, Set
from bs4 import Tag 

class RelevantContentFilter(ABC):
    def __init__(self, user_query: Optional[str] = None):
        self.user_query = user_query
        
        self.included_tags: Set[str] = {
            "article", "main", "section", "p", "h1", "h2", "h3", 
            "h4", "h5", "h6", "table", "pre", "code", "blockquote"
        }
        
        self.excluded_tags: Set[str] = {
            "nav", "footer", "header", "aside", "script", 
            "style", "form", "iframe", "noscript"
        }
        
        self.negative_patterns = re.compile(
            r"nav|footer|header|sidebar|ads|comment|promo|advert|social|share", re.IGNORECASE
        )
        
        self.min_word_count = 5

    @abstractmethod
    def filter_content(self, html: str) -> List[str]:
        pass

    def is_excluded(self, tag: Tag) -> bool:
        if tag.name in self.excluded_tags:
            return True
        
        class_id_string = " ".join(tag.get("class", [])) + " " + tag.get("id", "")
        if self.negative_patterns.search(class_id_string):
            return True
            
        return False

class NoContentFilter(RelevantContentFilter):
    def filter_content(self, html: str) -> List[str]:
        return [html] if html else []