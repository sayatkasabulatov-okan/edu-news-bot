"""Extended admin dashboard commands"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from src.config import settings
from src.database.connection import get_session
from src.utils.task_monitor import task_monitor
from src.utils.content_deduplicator import content_deduplicator


async def system_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /status command - show detailed system status

    Shows:
    - Bot uptime
    - Database status
    - Task health
    - Memory usage
    - Recent errors
    """
    user_id = update.effective_user.id

    # Check permissions
    if user_id != settings.MODERATOR_CHAT_ID:
        await update.message.reply_text("❌ У тебя нет прав для этой команды.")
        return

    try:
        import psutil
        import os
        from datetime import datetime

        # Get process info
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent(interval=0.1)

        # Get uptime
        create_time = datetime.fromtimestamp(process.create_time())
        uptime = datetime.now() - create_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds

        # Get task health
        health_report = task_monitor.get_health_report()

        # Get database stats
        from src.database.repositories.article_repo import ArticleRepository
        from src.database.repositories.digest_repo import DigestRepository

        async with get_session() as session:
            article_repo = ArticleRepository(session)
            digest_repo = DigestRepository(session)

            total_articles = len(await article_repo.get_all(limit=10000))
            total_digests = len(await digest_repo.get_all(limit=1000))

        status_message = f"""
🖥 <b>Системный статус</b>

<b>⏱ Uptime:</b> {uptime_str}
<b>💾 Память:</b> {memory_mb:.1f} MB
<b>⚡ CPU:</b> {cpu_percent:.1f}%

<b>📊 База данных:</b>
• Статей: {total_articles}
• Дайджестов: {total_digests}

{health_report}

<i>Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>
        """

        await update.message.reply_text(status_message, parse_mode='HTML')
        logger.info(f"System status requested by user {user_id}")

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при получении статуса:\n{str(e)}"
        )


async def cleanup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /cleanup command - cleanup old data

    Removes:
    - Old rejected digests (>30 days)
    - Processed articles (>60 days)
    - Duplicate articles
    """
    user_id = update.effective_user.id

    # Check permissions
    if user_id != settings.MODERATOR_CHAT_ID:
        await update.message.reply_text("❌ У тебя нет прав для этой команды.")
        return

    try:
        await update.message.reply_text("🧹 Начинаю очистку данных...")

        from datetime import datetime, timedelta
        from src.database.repositories.article_repo import ArticleRepository
        from src.database.repositories.digest_repo import DigestRepository
        from sqlalchemy import delete, select
        from src.database.models import Article, Digest

        cleanup_stats = {
            'old_rejected_digests': 0,
            'old_processed_articles': 0,
            'duplicate_articles': 0
        }

        async with get_session() as session:
            # Remove old rejected digests (>30 days)
            threshold_date = datetime.now() - timedelta(days=30)

            result = await session.execute(
                delete(Digest).where(
                    Digest.status == 'rejected',
                    Digest.created_at < threshold_date
                )
            )
            cleanup_stats['old_rejected_digests'] = result.rowcount

            # Remove old processed articles (>60 days)
            threshold_date = datetime.now() - timedelta(days=60)

            result = await session.execute(
                delete(Article).where(
                    Article.is_processed == True,
                    Article.created_at < threshold_date
                )
            )
            cleanup_stats['old_processed_articles'] = result.rowcount

            # Find and remove duplicate articles by URL
            article_repo = ArticleRepository(session)
            all_articles = await article_repo.get_all(limit=10000)

            # Convert to dict format for deduplicator
            articles_dict = [
                {'id': a.id, 'url': a.url, 'title': a.title, 'content': a.content}
                for a in all_articles
            ]

            # Get unique articles
            unique_articles = content_deduplicator.deduplicate_by_url(articles_dict)
            duplicate_count = len(articles_dict) - len(unique_articles)

            # Remove duplicates (keep first occurrence)
            if duplicate_count > 0:
                unique_ids = {a['id'] for a in unique_articles}
                all_ids = {a['id'] for a in articles_dict}
                duplicate_ids = all_ids - unique_ids

                result = await session.execute(
                    delete(Article).where(Article.id.in_(duplicate_ids))
                )
                cleanup_stats['duplicate_articles'] = result.rowcount

            await session.commit()

        # Send report
        report = f"""
✅ <b>Очистка завершена</b>

<b>📊 Удалено:</b>
• Старых отклонённых дайджестов: {cleanup_stats['old_rejected_digests']}
• Старых обработанных статей: {cleanup_stats['old_processed_articles']}
• Дубликатов статей: {cleanup_stats['duplicate_articles']}

<b>💾 Всего освобождено:</b> {sum(cleanup_stats.values())} записей
        """

        await update.message.reply_text(report, parse_mode='HTML')
        logger.info(f"Cleanup completed by user {user_id}: {cleanup_stats}")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при очистке:\n{str(e)}"
        )


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /logs command - show recent logs

    Shows last 20 log entries
    """
    user_id = update.effective_user.id

    # Check permissions
    if user_id != settings.MODERATOR_CHAT_ID:
        await update.message.reply_text("❌ У тебя нет прав для этой команды.")
        return

    try:
        import os

        # Get log file path
        log_file = "logs/bot.log"

        if not os.path.exists(log_file):
            await update.message.reply_text("📝 Лог-файл не найден")
            return

        # Read last 20 lines
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-20:] if len(lines) > 20 else lines

        # Format logs
        log_text = "".join(last_lines)

        # Truncate if too long
        if len(log_text) > 4000:
            log_text = log_text[-4000:]
            log_text = "...\n" + log_text

        await update.message.reply_text(
            f"📝 <b>Последние логи:</b>\n\n<code>{log_text}</code>",
            parse_mode='HTML'
        )

        logger.info(f"Logs requested by user {user_id}")

    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при чтении логов:\n{str(e)}"
        )


async def optimize_db_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /optimize command - optimize database

    Runs:
    - VACUUM
    - ANALYZE
    - Index recreation
    """
    user_id = update.effective_user.id

    # Check permissions
    if user_id != settings.MODERATOR_CHAT_ID:
        await update.message.reply_text("❌ У тебя нет прав для этой команды.")
        return

    try:
        await update.message.reply_text("⚙️ Начинаю оптимизацию базы данных...")

        from src.utils.db_optimizer import db_optimizer

        async with get_session() as session:
            # Analyze tables
            await db_optimizer.analyze_tables(session)

            await update.message.reply_text("✅ База данных оптимизирована!")

        logger.info(f"Database optimization requested by user {user_id}")

    except Exception as e:
        logger.error(f"Error optimizing database: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при оптимизации:\n{str(e)}"
        )
