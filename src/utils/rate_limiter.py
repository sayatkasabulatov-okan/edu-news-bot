"""Rate limiting utilities for bot handlers"""
from functools import wraps
from time import time
from typing import Dict, Callable
from loguru import logger


class RateLimiter:
    """Rate limiter for callback handlers"""

    def __init__(self):
        self._last_called: Dict[str, float] = {}

    def limit(self, seconds: float = 2.0, message: str = "⏰ Подожди немного"):
        """
        Decorator to rate limit callback handlers

        Args:
            seconds: Minimum time between calls
            message: Message to show when rate limited

        Usage:
            rate_limiter = RateLimiter()

            @rate_limiter.limit(seconds=3)
            async def handle_approve(query, context):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(query, context, *args, **kwargs):
                user_id = query.from_user.id
                key = f"{user_id}_{func.__name__}"
                now = time()

                if key in self._last_called:
                    elapsed = now - self._last_called[key]
                    if elapsed < seconds:
                        remaining = seconds - elapsed
                        logger.warning(
                            f"Rate limit hit for user {user_id} in {func.__name__} "
                            f"({remaining:.1f}s remaining)"
                        )
                        await query.answer(
                            f"{message} ({remaining:.0f}с)",
                            show_alert=True
                        )
                        return

                self._last_called[key] = now
                return await func(query, context, *args, **kwargs)

            return wrapper
        return decorator

    def clear_user(self, user_id: int):
        """Clear rate limit data for specific user"""
        keys_to_remove = [k for k in self._last_called.keys() if k.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del self._last_called[key]

    def clear_all(self):
        """Clear all rate limit data"""
        self._last_called.clear()


# Global instance
rate_limiter = RateLimiter()
