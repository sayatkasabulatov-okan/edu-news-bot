"""HTTP client with timeout and retry support"""
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from loguru import logger


class HTTPClient:
    """
    HTTP client with built-in timeout, retry, and error handling
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 2,
        user_agent: str = "Mozilla/5.0 (compatible; EduNewsBot/1.0)"
    ):
        """
        Initialize HTTP client

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            user_agent: User agent string
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.user_agent = user_agent
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers,
                raise_for_status=False  # Handle status codes manually
            )
        return self._session

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Perform GET request with retry logic

        Args:
            url: URL to fetch
            headers: Additional headers
            **kwargs: Additional arguments for aiohttp

        Returns:
            Response text or None if failed
        """
        session = await self._get_session()

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"GET {url} (attempt {attempt + 1}/{self.max_retries})")

                async with session.get(url, headers=headers, **kwargs) as response:
                    # Check status code
                    if response.status == 200:
                        text = await response.text()
                        logger.debug(f"Successfully fetched {url} ({len(text)} chars)")
                        return text

                    elif response.status == 404:
                        logger.warning(f"URL not found (404): {url}")
                        return None  # Don't retry 404s

                    elif response.status == 403:
                        logger.warning(f"Access forbidden (403): {url}")
                        return None  # Don't retry 403s

                    elif response.status >= 500:
                        # Server error - retry
                        logger.warning(f"Server error ({response.status}): {url}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        return None

                    else:
                        logger.warning(f"Unexpected status {response.status}: {url}")
                        return None

            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                return None

            except aiohttp.ClientError as e:
                logger.warning(f"Client error fetching {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                return None

            except Exception as e:
                logger.error(f"Unexpected error fetching {url}: {e}")
                return None

        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Perform POST request with retry logic

        Args:
            url: URL to post to
            data: Form data
            json: JSON data
            headers: Additional headers
            **kwargs: Additional arguments for aiohttp

        Returns:
            Response JSON or None if failed
        """
        session = await self._get_session()

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"POST {url} (attempt {attempt + 1}/{self.max_retries})")

                async with session.post(
                    url, data=data, json=json, headers=headers, **kwargs
                ) as response:
                    if response.status == 200 or response.status == 201:
                        result = await response.json()
                        logger.debug(f"Successfully posted to {url}")
                        return result

                    elif response.status >= 500:
                        logger.warning(f"Server error ({response.status}): {url}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (attempt + 1))
                            continue
                        return None

                    else:
                        logger.warning(f"POST failed with status {response.status}: {url}")
                        return None

            except asyncio.TimeoutError:
                logger.warning(f"Timeout posting to {url}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                return None

            except aiohttp.ClientError as e:
                logger.warning(f"Client error posting to {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                    continue
                return None

            except Exception as e:
                logger.error(f"Unexpected error posting to {url}: {e}")
                return None

        logger.error(f"Failed to post to {url} after {self.max_retries} attempts")
        return None

    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP session closed")

    async def __aenter__(self):
        """Context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()


# Global HTTP client instance with sensible defaults
http_client = HTTPClient(
    timeout=30,  # 30 seconds timeout
    max_retries=3,  # 3 retry attempts
    retry_delay=2  # 2 seconds between retries
)
