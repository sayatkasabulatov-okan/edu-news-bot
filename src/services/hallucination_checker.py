"""Service for checking AI hallucinations in generated content"""
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse
from loguru import logger


class HallucinationChecker:
    """Check generated content for AI hallucinations"""

    def __init__(self):
        # Pattern to find URLs in text
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

    def check_digest(
        self,
        digest_content: str,
        source_articles: List[Dict[str, str]]
    ) -> Dict[str, any]:
        """
        Check digest for potential hallucinations

        Args:
            digest_content: Generated digest text
            source_articles: List of source articles with 'content' and 'url' keys

        Returns:
            Dictionary with check results:
            {
                'has_issues': bool,
                'suspicious_urls': List[str],
                'warnings': List[str],
                'valid_urls': List[str]
            }
        """
        logger.debug("Starting hallucination check")

        result = {
            'has_issues': False,
            'suspicious_urls': [],
            'warnings': [],
            'valid_urls': []
        }

        # Extract URLs from digest
        digest_urls = self._extract_urls(digest_content)
        logger.debug(f"Found {len(digest_urls)} URLs in digest")

        # Extract URLs from source articles
        source_urls = set()
        for article in source_articles:
            # Add article URL itself
            source_urls.add(article.get('url', ''))
            # Add URLs from article content
            if article.get('content'):
                source_urls.update(self._extract_urls(article['content']))

        logger.debug(f"Found {len(source_urls)} URLs in source articles")

        # Check each URL in digest
        for url in digest_urls:
            # Check if URL is from source articles
            if url in source_urls:
                result['valid_urls'].append(url)
            else:
                # Check if domain matches any source
                digest_domain = self._get_domain(url)
                source_domains = [self._get_domain(u) for u in source_urls]

                if digest_domain in source_domains:
                    # Same domain but different URL - might be OK
                    result['valid_urls'].append(url)
                    result['warnings'].append(
                        f"URL from known domain but not in sources: {url[:50]}..."
                    )
                else:
                    # Completely unknown URL - likely hallucination
                    result['suspicious_urls'].append(url)
                    result['has_issues'] = True
                    logger.warning(f"Suspicious URL detected: {url}")

        # Check for suspicious patterns
        suspicious_patterns = [
            r'согласно исследованию',
            r'как сообщает',
            r'по данным',
            r'исследование показало',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, digest_content, re.IGNORECASE):
                # Check if there's a source reference nearby
                matches = list(re.finditer(pattern, digest_content, re.IGNORECASE))
                for match in matches:
                    # Check 200 chars around the match for URLs
                    start = max(0, match.start() - 100)
                    end = min(len(digest_content), match.end() + 100)
                    context = digest_content[start:end]

                    if not self._extract_urls(context):
                        result['warnings'].append(
                            f"Claim without source reference: '{match.group()}'..."
                        )

        # Summary
        if result['suspicious_urls']:
            result['has_issues'] = True

        logger.info(
            f"Hallucination check complete: "
            f"Issues={result['has_issues']}, "
            f"Suspicious={len(result['suspicious_urls'])}, "
            f"Warnings={len(result['warnings'])}"
        )

        return result

    def _extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from text"""
        if not text:
            return []
        return self.url_pattern.findall(text)

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""

    def format_warnings(self, check_result: Dict) -> str:
        """
        Format check results as user-friendly message

        Args:
            check_result: Result from check_digest()

        Returns:
            Formatted warning message
        """
        if not check_result['has_issues'] and not check_result['warnings']:
            return "✅ Проверка пройдена: галлюцинаций не обнаружено"

        message = ""

        if check_result['suspicious_urls']:
            message += "⚠️ <b>Подозрительные ссылки:</b>\n"
            for url in check_result['suspicious_urls'][:3]:  # Show max 3
                message += f"  • {url[:60]}...\n"
            message += "\n"

        if check_result['warnings']:
            message += "⚠️ <b>Предупреждения:</b>\n"
            for warning in check_result['warnings'][:3]:  # Show max 3
                message += f"  • {warning}\n"
            message += "\n"

        message += "<i>Пожалуйста, проверьте эти моменты перед публикацией.</i>"

        return message
