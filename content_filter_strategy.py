import re
import math
from abc import ABC, abstractmethod
from typing import List, Optional, Set, Dict
from bs4 import BeautifulSoup, Tag, Comment

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

class PruningContentFilter(RelevantContentFilter):
    def __init__(self, user_query: Optional[str] = None, threshold: float = 0.45):
        super().__init__(user_query)
        self.threshold = threshold
        self.tag_weights: Dict[str, float] = {
            "p": 1.0, "article": 1.5, "main": 1.4, "section": 1.2,
            "h1": 1.3, "h2": 1.2, "h3": 1.1,
            "div": 0.8, "span": 0.6, "li": 0.7,
        }

    def filter_content(self, html: str) -> List[str]:
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        
        for tag in soup.find_all(True):
             if self.is_excluded(tag):
                 tag.decompose()
        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()

        if soup.body:
            self._prune_tree(soup.body)
            return [str(child) for child in soup.body.find_all(recursive=False) if isinstance(child, Tag)]

        return []

    def _prune_tree(self, node: Tag):
        for child in list(node.children):
            if isinstance(child, Tag):
                self._prune_tree(child)

        score = self._compute_node_score(node)
        if score < self.threshold:
            node.decompose()

    def _compute_node_score(self, node: Tag) -> float:
        if not isinstance(node, Tag):
            return 0.0

        text_len = len(node.get_text(strip=True))
        if text_len < self.min_word_count * 3:
            return 0.0

        total_len = len(str(node))
        text_density = text_len / total_len if total_len > 0 else 0

        link_text_len = sum(len(a.get_text(strip=True)) for a in node.find_all("a", recursive=False))
        link_density = link_text_len / text_len if text_len > 0 else 0.5
        
        tag_weight = self.tag_weights.get(node.name, 0.7)

        score = text_density * 1.2 + (1 - link_density) * 0.8 * tag_weight
        return score