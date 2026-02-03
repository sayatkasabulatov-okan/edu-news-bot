"""Graceful shutdown handler for the bot"""
import signal
import asyncio
from typing import List, Callable, Awaitable
from loguru import logger


class ShutdownHandler:
    """Handles graceful shutdown of the bot and all components"""

    def __init__(self):
        self._shutdown_callbacks: List[Callable[[], Awaitable[None]]] = []
        self._is_shutting_down = False

    def register_shutdown_callback(self, callback: Callable[[], Awaitable[None]]):
        """
        Register a callback to be called during shutdown

        Args:
            callback: Async function to call during shutdown
        """
        self._shutdown_callbacks.append(callback)
        logger.debug(f"Registered shutdown callback: {callback.__name__}")

    async def shutdown(self):
        """Execute graceful shutdown"""
        if self._is_shutting_down:
            logger.warning("Shutdown already in progress")
            return

        self._is_shutting_down = True
        logger.info("=" * 60)
        logger.info("🛑 Initiating graceful shutdown...")
        logger.info("=" * 60)

        # Execute all shutdown callbacks
        for i, callback in enumerate(self._shutdown_callbacks, 1):
            try:
                logger.info(f"[{i}/{len(self._shutdown_callbacks)}] Executing: {callback.__name__}")
                await callback()
                logger.info(f"✅ {callback.__name__} completed")
            except Exception as e:
                logger.error(f"❌ Error in {callback.__name__}: {e}")

        logger.info("=" * 60)
        logger.info("✅ Graceful shutdown completed")
        logger.info("=" * 60)

    def setup_signal_handlers(self, loop: asyncio.AbstractEventLoop):
        """
        Setup signal handlers for graceful shutdown

        Args:
            loop: Event loop to use for shutdown
        """
        def handle_signal(signum, frame):
            """Handle shutdown signals"""
            signal_name = signal.Signals(signum).name
            logger.warning(f"Received signal {signal_name}")

            # Schedule shutdown in the event loop
            asyncio.create_task(self.shutdown())

        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, handle_signal)
            logger.debug(f"Registered handler for {signal.Signals(sig).name}")


# Global shutdown handler instance
shutdown_handler = ShutdownHandler()
