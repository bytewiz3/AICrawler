import re
from abc import ABC, abstractmethod
from typing import List, Optional, Set, Dict, Tuple
from collections import deque

from bs4 import BeautifulSoup, Tag, Comment, NavigableString
from rank_bm25 import BM25Okapi
from snowballstemmer import stemmer

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
    
    def extract_page_query(self, soup: BeautifulSoup) -> str:
        if self.user_query:
            return self.user_query

        query_parts = []
        if soup.title and soup.title.string:
            query_parts.append(soup.title.string)
        if soup.find("h1"):
            query_parts.append(soup.find("h1").get_text())

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            query_parts.append(meta_desc["content"])
        
        return " ".join(filter(None, query_parts))

    def extract_text_chunks(self, body: Tag) -> List[Tuple[int, str, Tag]]:
        chunks = []
        significant_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "pre", "blockquote", "td"}
        
        for i, tag in enumerate(body.find_all(significant_tags)):
            if self.is_excluded(tag):
                continue
            
            text = tag.get_text(strip=True)
            if len(text.split()) >= self.min_word_count:
                chunks.append((i, text, tag))
        return chunks

class BM25ContentFilter(RelevantContentFilter):
    def __init__(
        self,
        user_query: Optional[str] = None,
        bm25_threshold: float = 0.5,
        language: str = "english",
    ):
        super().__init__(user_query)
        self.bm25_threshold = bm25_threshold
        try:
            self.stemmer = stemmer(language)
        except Exception:
            print(f"Warning: Stemmer for '{language}' not found. Falling back to no stemming.")
            self.stemmer = None

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r'\b\w+\b', text.lower())
        if self.stemmer:
            return self.stemmer.stemWords(tokens)
        return tokens

    def filter_content(self, html: str) -> List[str]:
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        if not soup.body:
            return []

        query = self.extract_page_query(soup)
        if not query:
            return []
        tokenized_query = self._tokenize(query)

        candidates = self.extract_text_chunks(soup.body)
        if not candidates:
            return []

        corpus_texts = [text for _, text, _ in candidates]
        tokenized_corpus = [self._tokenize(doc) for doc in corpus_texts]

        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)

        selected_chunks = []
        for i, score in enumerate(scores):
            if score >= self.bm25_threshold:
                original_index, _, source_tag = candidates[i]
                selected_chunks.append((original_index, str(source_tag)))

        selected_chunks.sort(key=lambda x: x[0])
        return [chunk_html for _, chunk_html in selected_chunks]

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