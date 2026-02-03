"""Content deduplication utilities"""
from typing import List, Optional, Tuple
from difflib import SequenceMatcher
import hashlib
from loguru import logger


class ContentDeduplicator:
    """Detect and handle duplicate content"""

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize content deduplicator

        Args:
            similarity_threshold: Threshold for considering content similar (0-1)
        """
        self.similarity_threshold = similarity_threshold

    @staticmethod
    def get_content_hash(content: str) -> str:
        """
        Get hash of content for quick duplicate detection

        Args:
            content: Content to hash

        Returns:
            MD5 hash of content
        """
        normalized = content.lower().strip()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def get_url_fingerprint(url: str) -> str:
        """
        Get fingerprint of URL (normalized form)

        Args:
            url: URL to fingerprint

        Returns:
            Normalized URL
        """
        # Remove common tracking parameters
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign',
            'utm_content', 'utm_term', 'fbclid', 'gclid'
        ]

        # Parse and clean URL
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        parsed = urlparse(url)

        # Remove tracking parameters
        query_params = parse_qs(parsed.query)
        clean_params = {
            k: v for k, v in query_params.items()
            if k not in tracking_params
        }

        # Rebuild URL
        clean_query = urlencode(clean_params, doseq=True)
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            clean_query,
            ''  # Remove fragment
        ))

        return clean_url.lower().rstrip('/')

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        # Normalize texts
        norm1 = text1.lower().strip()
        norm2 = text2.lower().strip()

        # Quick check for exact match
        if norm1 == norm2:
            return 1.0

        # Use SequenceMatcher for fuzzy matching
        matcher = SequenceMatcher(None, norm1, norm2)
        return matcher.ratio()

    def is_duplicate_content(
        self,
        content1: str,
        content2: str,
        threshold: Optional[float] = None
    ) -> Tuple[bool, float]:
        """
        Check if two pieces of content are duplicates

        Args:
            content1: First content
            content2: Second content
            threshold: Custom similarity threshold (optional)

        Returns:
            Tuple of (is_duplicate, similarity_score)
        """
        threshold = threshold or self.similarity_threshold

        # Calculate similarity
        similarity = self.calculate_similarity(content1, content2)

        is_duplicate = similarity >= threshold

        if is_duplicate:
            logger.debug(
                f"Duplicate detected with {similarity:.2%} similarity "
                f"(threshold: {threshold:.2%})"
            )

        return is_duplicate, similarity

    def find_duplicates_in_list(
        self,
        articles: List[dict],
        key: str = 'content'
    ) -> List[Tuple[int, int, float]]:
        """
        Find all duplicate pairs in a list of articles

        Args:
            articles: List of article dictionaries
            key: Key to use for content comparison

        Returns:
            List of tuples (index1, index2, similarity)
        """
        duplicates = []

        for i in range(len(articles)):
            for j in range(i + 1, len(articles)):
                content1 = articles[i].get(key, '')
                content2 = articles[j].get(key, '')

                is_dup, similarity = self.is_duplicate_content(content1, content2)

                if is_dup:
                    duplicates.append((i, j, similarity))

        return duplicates

    def deduplicate_by_url(self, articles: List[dict]) -> List[dict]:
        """
        Remove articles with duplicate URLs

        Args:
            articles: List of article dictionaries with 'url' key

        Returns:
            Deduplicated list of articles
        """
        seen_urls = set()
        unique_articles = []

        for article in articles:
            url = article.get('url', '')
            fingerprint = self.get_url_fingerprint(url)

            if fingerprint not in seen_urls:
                seen_urls.add(fingerprint)
                unique_articles.append(article)
            else:
                logger.debug(f"Skipping duplicate URL: {url}")

        removed_count = len(articles) - len(unique_articles)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate URLs")

        return unique_articles

    def deduplicate_by_content(
        self,
        articles: List[dict],
        content_key: str = 'content'
    ) -> List[dict]:
        """
        Remove articles with duplicate content

        Args:
            articles: List of article dictionaries
            content_key: Key to use for content comparison

        Returns:
            Deduplicated list of articles
        """
        if not articles:
            return []

        # Track which articles to keep
        keep_indices = set(range(len(articles)))

        # Find all duplicates
        duplicates = self.find_duplicates_in_list(articles, key=content_key)

        # Mark duplicates for removal (keep first occurrence)
        for idx1, idx2, similarity in duplicates:
            if idx2 in keep_indices:
                keep_indices.remove(idx2)
                logger.debug(
                    f"Marking article {idx2} as duplicate of {idx1} "
                    f"({similarity:.2%} similar)"
                )

        # Keep only unique articles
        unique_articles = [
            article for i, article in enumerate(articles)
            if i in keep_indices
        ]

        removed_count = len(articles) - len(unique_articles)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate articles by content")

        return unique_articles

    def full_deduplication(self, articles: List[dict]) -> List[dict]:
        """
        Perform full deduplication (URL + content)

        Args:
            articles: List of article dictionaries

        Returns:
            Fully deduplicated list
        """
        logger.info(f"Starting deduplication of {len(articles)} articles")

        # Step 1: Remove URL duplicates
        unique_by_url = self.deduplicate_by_url(articles)

        # Step 2: Remove content duplicates
        fully_unique = self.deduplicate_by_content(unique_by_url)

        logger.info(
            f"Deduplication complete: {len(articles)} → {len(fully_unique)} "
            f"({len(articles) - len(fully_unique)} removed)"
        )

        return fully_unique


# Global deduplicator instance
content_deduplicator = ContentDeduplicator(similarity_threshold=0.85)
