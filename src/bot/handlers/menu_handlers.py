"""Handlers for main menu interactions"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from sqlalchemy import select, desc

from src.bot.handlers import commands, admin_commands
from src.database.connection import get_session
from src.database.repositories.digest_repo import DigestRepository
from src.database.repositories.post_repo import PostRepository
from src.database.models import Digest, Post, Article, Source
from src.bot.keyboards.post_actions import get_digest_keyboard, get_post_actions_keyboard
from sqlalchemy.orm import joinedload


async def show_last_digest(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback: bool = False):
    """Show the last digest with action buttons"""
    from src.config import settings

    user_id = update.effective_user.id if is_callback else update.message.from_user.id

    # Check if user is moderator
    if not settings.is_moderator(user_id):
        error_msg = "❌ У тебя нет прав для просмотра дайджестов."
        if is_callback:
            await update.callback_query.answer(error_msg, show_alert=True)
        else:
            await update.message.reply_text(error_msg)
        return

    try:
        async with get_session() as session:
            digest_repo = DigestRepository(session)

            # Find last digest (draft, approved, or sent_to_moderator)
            # Order by created_at DESC to get the most recent one
            result = await session.execute(
                select(Digest)
                .where(Digest.status.in_(['draft', 'approved', 'sent_to_moderator']))
                .order_by(desc(Digest.created_at))
                .limit(1)
            )
            last_digest = result.scalars().first()

            if not last_digest:
                no_digest_msg = """
📭 <b>Нет доступных дайджестов</b>

Пока нет ни одного дайджеста для модерации.

💡 <b>Что можно сделать:</b>
• Используй <b>🔄 Собрать новости</b> для сбора статей
• Бот автоматически создаст дайджест когда будет достаточно материала

<i>Дайджесты создаются автоматически каждый день в {hour}:00</i>
                """.format(hour=settings.SCRAPING_SCHEDULE_HOUR)

                if is_callback:
                    await update.callback_query.message.reply_text(
                        no_digest_msg,
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        no_digest_msg,
                        parse_mode='HTML'
                    )
                return

            # Show digest with action buttons
            keyboard = get_digest_keyboard(last_digest.id, last_digest.status)

            # Status emoji
            status_emoji = {
                'draft': '📝',
                'approved': '✅',
                'sent_to_moderator': '👀'
            }

            status_text = {
                'draft': 'Черновик',
                'approved': 'Утверждён',
                'sent_to_moderator': 'На модерации'
            }

            # Format created date
            created_str = last_digest.created_at.strftime('%d.%m.%Y %H:%M') if last_digest.created_at else 'Неизвестно'

            message_text = f"""
{status_emoji.get(last_digest.status, '📝')} <b>Дайджест #{last_digest.id}</b>

<b>Статус:</b> {status_text.get(last_digest.status, last_digest.status)}
<b>Создан:</b> {created_str}

{last_digest.content}

<i>👇 Выбери действие:</i>
            """

            if is_callback:
                await update.callback_query.message.reply_text(
                    message_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    message_text,
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )

            logger.info(f"User {user_id} viewed last digest #{last_digest.id}")

    except Exception as e:
        logger.error(f"Error showing last digest: {e}")
        error_text = f"❌ Ошибка при загрузке дайджеста:\n{str(e)}"

        if is_callback:
            await update.callback_query.message.reply_text(error_text)
        else:
            await update.message.reply_text(error_text)


async def show_last_article(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback: bool = False):
    """Show the last article post with action buttons"""
    from src.config import settings

    user_id = update.effective_user.id if is_callback else update.message.from_user.id

    # Check if user is moderator
    if not settings.is_moderator(user_id):
        error_msg = "❌ У тебя нет прав для просмотра статей."
        if is_callback:
            await update.callback_query.answer(error_msg, show_alert=True)
        else:
            await update.message.reply_text(error_msg)
        return

    try:
        async with get_session() as session:
            # Find last article post (sent_to_moderator, approved, scheduled, or published)
            # Order by created_at DESC to get the most recent one
            result = await session.execute(
                select(Post)
                .options(joinedload(Post.article).joinedload(Article.source))
                .where(Post.article_id.isnot(None))
                .where(Post.status.in_(['sent_to_moderator', 'approved', 'scheduled', 'published']))
                .order_by(desc(Post.created_at))
                .limit(1)
            )
            last_post = result.scalars().first()

            if not last_post:
                no_article_msg = f"""
📭 <b>Нет доступных статей</b>

Пока нет ни одной обработанной статьи.

💡 <b>Что можно сделать:</b>
• Используй <b>🔄 Собрать новости</b> для сбора статей
• Бот автоматически обрабатывает статьи каждые {settings.SCRAPING_INTERVAL_HOURS} часа

<i>Статьи обрабатываются автоматически каждые {settings.SCRAPING_INTERVAL_HOURS} часа</i>
                """

                if is_callback:
                    await update.callback_query.message.reply_text(
                        no_article_msg,
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        no_article_msg,
                        parse_mode='HTML'
                    )
                return

            # Show article post with action buttons
            keyboard = get_post_actions_keyboard(last_post.id, has_digest=False)

            # Status emoji
            status_emoji = {
                'sent_to_moderator': '👀',
                'approved': '✅',
                'scheduled': '📅',
                'published': '🚀'
            }

            status_text = {
                'sent_to_moderator': 'На модерации',
                'approved': 'Утверждена',
                'scheduled': 'Запланирована',
                'published': 'Опубликована'
            }

            # Format dates
            created_str = last_post.created_at.strftime('%d.%m.%Y %H:%M') if last_post.created_at else 'Неизвестно'

            # Get source info
            source_name = last_post.article.source.name if last_post.article and last_post.article.source else "Неизвестный источник"
            article_url = last_post.article.url if last_post.article else None

            message_text = f"""
{status_emoji.get(last_post.status, '📄')} <b>Статья #{last_post.id}</b>

<b>Статус:</b> {status_text.get(last_post.status, last_post.status)}
<b>Источник:</b> {source_name}
<b>Создана:</b> {created_str}

{last_post.content}
"""

            # Add original article link if available
            if article_url:
                message_text += f"\n\n🔗 <a href='{article_url}'>Оригинал статьи</a>"

            message_text += "\n\n<i>👇 Выбери действие:</i>"

            if is_callback:
                await update.callback_query.message.reply_text(
                    message_text,
                    reply_markup=keyboard,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            else:
                await update.message.reply_text(
                    message_text,
                    reply_markup=keyboard,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )

            logger.info(f"User {user_id} viewed last article post #{last_post.id}")

    except Exception as e:
        logger.error(f"Error showing last article: {e}")
        error_text = f"❌ Ошибка при загрузке статьи:\n{str(e)}"

        if is_callback:
            await update.callback_query.message.reply_text(error_text)
        else:
            await update.message.reply_text(error_text)


async def handle_menu_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reply keyboard button presses"""
    text = update.message.text

    if text == "📊 Статистика":
        await commands.stats_command(update, context)
    elif text == "ℹ️ Справка":
        await commands.help_command(update, context)
    elif text == "🔧 Админ-панель":
        await admin_commands.admin_command(update, context)
    elif text == "🔄 Собрать новости":
        await commands.collect_command(update, context)
    elif text == "📰 Последняя статья":
        await show_last_article(update, context, is_callback=False)


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline menu button presses"""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "menu_stats":
        # Create fake update for stats command
        await query.message.reply_text("📊 Загружаю статистику...")
        # Call stats command logic
        from src.config import settings
        from src.database.connection import get_session
        from src.database.repositories.digest_repo import DigestRepository
        from src.database.repositories.post_repo import PostRepository

        try:
            async with get_session() as session:
                digest_repo = DigestRepository(session)
                post_repo = PostRepository(session)

                all_digests = await digest_repo.get_all(limit=1000)
                draft_digests = await digest_repo.get_by_status('draft')
                published_posts = [p for p in await post_repo.get_all(limit=1000) if p.status == 'published']

                stats_message = f"""
📊 <b>Статистика</b>

<b>📈 Общая информация:</b>
• Всего дайджестов: {len(all_digests)}
• Черновиков: {len(draft_digests)}
• Опубликовано: {len(published_posts)}

<b>📋 По статусам:</b>
• Черновики: {len([d for d in all_digests if d.status == 'draft'])}
• Утверждённые: {len([d for d in all_digests if d.status == 'approved'])}
• Запланированные: {len([d for d in all_digests if d.status == 'scheduled'])}
• Опубликованные: {len([d for d in all_digests if d.status == 'published'])}
• Отклонённые: {len([d for d in all_digests if d.status == 'rejected'])}

<i>💡 Используй /admin для управления контентом</i>
                """

                await query.message.reply_text(stats_message, parse_mode='HTML')

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await query.message.reply_text(
                "❌ Ошибка при получении статистики. Проверь логи."
            )

    elif callback_data == "menu_help":
        # Show help
        help_message = """
ℹ️ <b>Справка по командам</b>

<b>📊 Основные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку
/stats - Показать статистику

<b>🔧 Админ-команды:</b>
/admin - Открыть админ-панель
/collect - Запустить сбор новостей

<b>📝 Как работает бот:</b>
1. Собирает новости об образовании
2. Формирует дайджесты
3. Отправляет тебе на модерацию
4. Публикует в канал по расписанию

<i>💡 Используй кнопки меню для быстрого доступа!</i>
        """

        await query.message.reply_text(
            help_message,
            parse_mode='HTML'
        )

    elif callback_data == "menu_last_article":
        # Show last article
        await show_last_article(update, context, is_callback=True)

    elif callback_data == "menu_admin":
        # Show admin panel
        user_id = query.from_user.id

        # Check if user is moderator
        from src.config import settings
        if not settings.is_moderator(user_id):
            await query.answer(
                "❌ У тебя нет прав доступа к админ-панели.",
                show_alert=True
            )
            logger.warning(f"Unauthorized admin access attempt by user {user_id}")
            return

        from src.bot.keyboards.admin_keyboards import get_admin_main_menu

        admin_message = """
🔧 <b>Админ-панель управления</b>

<b>🎯 Настройки контента:</b>
• Разделы образования
• Источники новостей
• Язык и стиль постов

<b>⚙️ Автоматизация:</b>
• Расписание публикаций
• Запуск сбора новостей

<b>📊 Мониторинг:</b>
• История публикаций
• Аналитика канала

<i>Выбери раздел для настройки:</i>
        """

        await query.message.reply_text(
            admin_message,
            reply_markup=get_admin_main_menu(),
            parse_mode='HTML'
        )

        logger.info(f"Admin panel opened by user {user_id}")
