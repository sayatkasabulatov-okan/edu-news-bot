"""Main application entry point"""
import asyncio
import signal
from loguru import logger

from src.utils.logger import setup_logger
from src.bot.app import create_bot_application
from src.scraper.scheduler import ScraperScheduler
from src.database.connection import init_db, get_session
from src.services.digest_service import DigestService
from src.services.post_service import PostService
from src.bot.keyboards.post_actions import get_digest_keyboard
from src.config import settings
from src.utils.shutdown_handler import shutdown_handler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


# Global instances
bot_app = None
scraper_scheduler = None
publish_scheduler = None


async def send_digest_to_moderator(digest_id: int):
    """Send digest to moderator with action buttons"""
    global bot_app

    try:
        async with get_session() as session:
            digest_service = DigestService(session)
            digest = await digest_service.get_digest(digest_id)

            if not digest:
                logger.error(f"Digest {digest_id} not found")
                return

            # Get articles and sources for this digest
            from src.database.repositories.article_repo import ArticleRepository
            from src.database.repositories.source_repo import SourceRepository
            from sqlalchemy import select
            from src.database.models import Article, Source

            article_repo = ArticleRepository(session)
            source_repo = SourceRepository(session)

            # Get articles used in this digest
            result = await session.execute(
                select(Article, Source).join(Source).where(Article.id.in_(digest.article_ids))
            )
            articles_with_sources = result.all()

            # Build sources info
            sources_info = "\n\n<b>📚 Источники:</b>\n"
            seen_sources = set()
            for article, source in articles_with_sources:
                if source.name not in seen_sources:
                    sources_info += f"• <a href='{article.url}'>{source.name}</a>\n"
                    seen_sources.add(source.name)

            # Check for hallucinations
            from src.services.hallucination_checker import HallucinationChecker
            checker = HallucinationChecker()

            # Prepare articles for checking
            articles_data = [
                {'url': article.url, 'content': article.content or ''}
                for article, _ in articles_with_sources
            ]

            # Run check
            check_result = checker.check_digest(digest.content, articles_data)

            # Add warning if issues found
            hallucination_warning = ""
            if check_result['has_issues'] or check_result['warnings']:
                hallucination_warning = "\n\n" + checker.format_warnings(check_result)
                logger.warning(f"Digest {digest_id} has potential hallucinations")

            # Build moderation header
            status_emoji = {
                'draft': '📝',
                'approved': '✅',
                'rejected': '❌',
                'scheduled': '📅',
                'published': '✅'
            }

            header = f"""
{status_emoji.get(digest.status, '📝')} <b>Новый дайджест #{digest_id}</b>
━━━━━━━━━━━━━━━━━━━━━━

"""

            footer = f"""

━━━━━━━━━━━━━━━━━━━━━━
<i>💡 Используй кнопки ниже для управления дайджестом</i>
"""

            # Combine all parts
            full_message = header + digest.content + sources_info + hallucination_warning + footer

            # Send to all moderators
            from src.database.repositories.digest_repo import DigestRepository
            digest_repo = DigestRepository(session)

            for mod_id in settings.moderator_ids:
                try:
                    message = await bot_app.bot.send_message(
                        chat_id=mod_id,
                        text=full_message,
                        reply_markup=get_digest_keyboard(digest_id),
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                    # Save last message ID for reference
                    await digest_repo.set_moderator_message(digest_id, message.message_id)
                    logger.info(f"Digest {digest_id} sent to moderator {mod_id}")
                except Exception as e:
                    logger.error(f"Failed to send digest {digest_id} to moderator {mod_id}: {e}")

            logger.info(f"Digest {digest_id} sent to {len(settings.moderator_ids)} moderator(s) with {len(seen_sources)} sources")

    except Exception as e:
        logger.error(f"Error sending digest to moderator: {e}")


async def check_and_create_digest():
    """Check if we can create a digest and send it to moderator"""
    try:
        async with get_session() as session:
            digest_service = DigestService(session)
            digest_id = await digest_service.create_digest_if_ready()

            if digest_id:
                logger.info(f"New digest {digest_id} created")
                await send_digest_to_moderator(digest_id)

    except Exception as e:
        logger.error(f"Error checking for digest creation: {e}")


async def publish_scheduled_posts():
    """Publish all posts scheduled for now"""
    global bot_app

    try:
        async with get_session() as session:
            post_service = PostService(session, bot_app.bot)
            count = await post_service.publish_scheduled_posts()

            if count > 0:
                logger.info(f"Published {count} scheduled posts")

    except Exception as e:
        logger.error(f"Error publishing scheduled posts: {e}")


async def main():
    """Main application function"""
    global bot_app, scraper_scheduler, publish_scheduler

    # Setup logger
    setup_logger()
    logger.info("Starting Telegram Education News Bot")

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def handle_signal(signum, frame):
        """Handle shutdown signals"""
        signal_name = signal.Signals(signum).name
        logger.warning(f"Received signal {signal_name}, initiating shutdown...")
        loop.call_soon_threadsafe(stop_event.set)

    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    try:
        # Initialize database
        logger.info("Initializing database")
        await init_db()

        # Create bot application
        logger.info("Creating bot application")
        bot_app = create_bot_application()

        # Start scraper scheduler
        logger.info("Starting scraper scheduler")
        scraper_scheduler = ScraperScheduler()
        scraper_scheduler.start()

        # Create scheduler for checking digests and publishing
        logger.info("Starting publish scheduler")
        publish_scheduler = AsyncIOScheduler()

        # Check for digest creation every 30 minutes
        publish_scheduler.add_job(
            check_and_create_digest,
            trigger=CronTrigger(minute='*/30'),
            id='check_digest',
            replace_existing=True,
            name='Check Digest Creation'
        )

        # Publish scheduled posts every 5 minutes
        publish_scheduler.add_job(
            publish_scheduled_posts,
            trigger=CronTrigger(minute='*/5'),
            id='publish_posts',
            replace_existing=True,
            name='Publish Scheduled Posts'
        )

        publish_scheduler.start()

        # Register shutdown callbacks
        async def stop_bot():
            """Stop the bot gracefully"""
            if bot_app and bot_app.updater and bot_app.updater.running:
                await bot_app.updater.stop()
            if bot_app:
                await bot_app.stop()
                await bot_app.shutdown()

        async def stop_scraper():
            """Stop the scraper scheduler"""
            if scraper_scheduler:
                scraper_scheduler.stop()

        async def stop_publisher():
            """Stop the publish scheduler"""
            if publish_scheduler:
                publish_scheduler.shutdown()

        shutdown_handler.register_shutdown_callback(stop_publisher)
        shutdown_handler.register_shutdown_callback(stop_scraper)
        shutdown_handler.register_shutdown_callback(stop_bot)

        # Start bot
        logger.info("Bot is starting...")
        logger.info(f"Moderator chat IDs: {settings.moderator_ids}")
        logger.info(f"Channel ID: {settings.CHANNEL_ID}")

        # Log scraping mode
        if settings.ENABLE_ARTICLE_MODE:
            logger.info(f"⚡ Article mode enabled: Processing at {settings.SCRAPING_HOURS} (3 times/day)")
        if settings.ENABLE_DIGEST_MODE:
            logger.info(f"📰 Digest mode enabled: Daily digests at {settings.SCRAPING_SCHEDULE_HOUR}:00")

        # Initialize and start the bot properly in async context
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()

        logger.info("Bot started successfully! Press Ctrl+C to stop.")

        # Keep the bot running until stop signal
        await stop_event.wait()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        # Execute graceful shutdown
        await shutdown_handler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
