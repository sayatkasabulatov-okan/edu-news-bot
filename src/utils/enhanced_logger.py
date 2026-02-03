"""Enhanced logging utilities with context and structured logging"""
from typing import Optional, Dict, Any
from contextvars import ContextVar
from functools import wraps
from loguru import logger
import time
import traceback


# Context variables for logging
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[int]] = ContextVar('user_id', default=None)


class LogContext:
    """Context manager for adding context to logs"""

    def __init__(self, **context):
        """
        Initialize log context

        Args:
            **context: Context key-value pairs
        """
        self.context = context
        self.tokens = {}

    def __enter__(self):
        """Enter context and set context variables"""
        for key, value in self.context.items():
            if key == 'request_id':
                self.tokens['request_id'] = request_id_var.set(value)
            elif key == 'user_id':
                self.tokens['user_id'] = user_id_var.set(value)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and reset context variables"""
        for token in self.tokens.values():
            if hasattr(token, 'var'):
                token.var.reset(token)


def get_log_context() -> Dict[str, Any]:
    """Get current log context"""
    context = {}

    request_id = request_id_var.get()
    if request_id:
        context['request_id'] = request_id

    user_id = user_id_var.get()
    if user_id:
        context['user_id'] = user_id

    return context


def log_function_call(log_args: bool = False, log_result: bool = False):
    """
    Decorator to log function calls with timing

    Args:
        log_args: Whether to log function arguments
        log_result: Whether to log function result
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = get_log_context()
            context_str = f" [{', '.join(f'{k}={v}' for k, v in context.items())}]" if context else ""

            # Log function entry
            if log_args:
                logger.debug(
                    f"{context_str} → {func.__name__}("
                    f"args={args[1:]}, kwargs={kwargs})"  # Skip self/cls
                )
            else:
                logger.debug(f"{context_str} → {func.__name__}()")

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000

                # Log function exit
                if log_result:
                    logger.debug(
                        f"{context_str} ← {func.__name__}() = {result} "
                        f"({elapsed:.2f}ms)"
                    )
                else:
                    logger.debug(
                        f"{context_str} ← {func.__name__}() "
                        f"({elapsed:.2f}ms)"
                    )

                return result

            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(
                    f"{context_str} ✗ {func.__name__}() failed after {elapsed:.2f}ms: "
                    f"{type(e).__name__}: {e}"
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            context = get_log_context()
            context_str = f" [{', '.join(f'{k}={v}' for k, v in context.items())}]" if context else ""

            # Log function entry
            if log_args:
                logger.debug(
                    f"{context_str} → {func.__name__}("
                    f"args={args[1:]}, kwargs={kwargs})"
                )
            else:
                logger.debug(f"{context_str} → {func.__name__}()")

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000

                # Log function exit
                if log_result:
                    logger.debug(
                        f"{context_str} ← {func.__name__}() = {result} "
                        f"({elapsed:.2f}ms)"
                    )
                else:
                    logger.debug(
                        f"{context_str} ← {func.__name__}() "
                        f"({elapsed:.2f}ms)"
                    )

                return result

            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(
                    f"{context_str} ✗ {func.__name__}() failed after {elapsed:.2f}ms: "
                    f"{type(e).__name__}: {e}"
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class StructuredLogger:
    """Structured logging with consistent format"""

    @staticmethod
    def log_event(
        event_type: str,
        level: str = "info",
        **data
    ):
        """
        Log a structured event

        Args:
            event_type: Type of event (e.g., "user_action", "api_call")
            level: Log level (info, warning, error, debug)
            **data: Additional event data
        """
        context = get_log_context()
        event_data = {
            'event': event_type,
            **context,
            **data
        }

        log_message = f"[{event_type}] " + ", ".join(
            f"{k}={v}" for k, v in event_data.items() if k != 'event'
        )

        getattr(logger, level)(log_message)

    @staticmethod
    def log_user_action(
        user_id: int,
        action: str,
        **details
    ):
        """
        Log a user action

        Args:
            user_id: User ID
            action: Action performed
            **details: Additional details
        """
        StructuredLogger.log_event(
            "user_action",
            user_id=user_id,
            action=action,
            **details
        )

    @staticmethod
    def log_api_call(
        service: str,
        endpoint: str,
        status: str,
        duration_ms: Optional[float] = None,
        **details
    ):
        """
        Log an API call

        Args:
            service: Service name (e.g., "telegram", "openai")
            endpoint: API endpoint
            status: Call status (success, error, timeout)
            duration_ms: Call duration in milliseconds
            **details: Additional details
        """
        StructuredLogger.log_event(
            "api_call",
            service=service,
            endpoint=endpoint,
            status=status,
            duration_ms=duration_ms,
            **details
        )

    @staticmethod
    def log_database_query(
        operation: str,
        table: str,
        duration_ms: Optional[float] = None,
        rows_affected: Optional[int] = None,
        **details
    ):
        """
        Log a database query

        Args:
            operation: Operation type (select, insert, update, delete)
            table: Table name
            duration_ms: Query duration in milliseconds
            rows_affected: Number of rows affected
            **details: Additional details
        """
        StructuredLogger.log_event(
            "db_query",
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            **details
        )

    @staticmethod
    def log_error_with_context(
        error: Exception,
        context_message: str,
        **additional_context
    ):
        """
        Log an error with full context and traceback

        Args:
            error: Exception object
            context_message: Context description
            **additional_context: Additional context data
        """
        error_context = get_log_context()
        error_context.update(additional_context)

        context_str = ", ".join(f"{k}={v}" for k, v in error_context.items())

        logger.error(
            f"❌ {context_message}\n"
            f"   Error: {type(error).__name__}: {error}\n"
            f"   Context: {context_str}\n"
            f"   Traceback:\n{traceback.format_exc()}"
        )


# Global structured logger instance
structured_logger = StructuredLogger()
