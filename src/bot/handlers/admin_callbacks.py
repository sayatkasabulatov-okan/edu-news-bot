"""Admin panel callback handlers"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime

from src.config import settings
from src.database.connection import get_session
from src.database.repositories.settings_repo import SettingsRepository
from src.database.repositories.source_repo import SourceRepository
from src.database.repositories.post_repo import PostRepository
from src.bot.keyboards.admin_keyboards import (
    get_admin_main_menu,
    get_back_to_admin_menu,
    get_education_sections_keyboard,
    get_sources_keyboard,
    get_schedule_settings_keyboard,
    get_language_keyboard,
    get_post_length_keyboard
)


async def handle_admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    # Check authorization
    if not update.effective_user or not settings.is_moderator(update.effective_user.id):
        await query.answer("❌ Доступ запрещен", show_alert=True)
        return

    # Route to handlers
    if callback_data == "admin_back" or callback_data == "admin_menu":
        await handle_back_to_admin(query, context)
    elif callback_data == "admin_sections":
        await handle_sections(query, context)
    elif callback_data.startswith("section_toggle_"):
        await handle_section_toggle(query, context)
    elif callback_data == "admin_sources":
        await handle_sources(query, context)
    elif callback_data.startswith("source_toggle_"):
        await handle_source_toggle(query, context)
    elif callback_data == "admin_schedule":
        await handle_schedule_settings(query, context)
    elif callback_data.startswith("schedule_hour_"):
        await handle_schedule_hour(query, context)
    elif callback_data == "admin_language":
        await handle_language(query, context)
    elif callback_data.startswith("language_set_"):
        await handle_language_set(query, context)
    elif callback_data == "admin_length":
        await handle_post_length(query, context)
    elif callback_data.startswith("length_set_"):
        await handle_length_set(query, context)
    elif callback_data == "admin_images":
        await handle_images(query, context)
    elif callback_data.startswith("admin_images_"):
        await handle_set_images(query, context)
    elif callback_data == "admin_run_research":
        await handle_run_research(query, context)
    elif callback_data == "admin_history":
        await handle_history(query, context)
    # Временно скрыто
    # elif callback_data == "admin_analytics":
    #     await handle_analytics(query, context)


async def handle_back_to_admin(query, context: ContextTypes.DEFAULT_TYPE):
    """Return to main admin menu"""
    await query.edit_message_text(
        "🔧 **Админ-панель**\n\n"
        "Выбери нужный раздел:",
        reply_markup=get_admin_main_menu(),
        parse_mode='Markdown'
    )


async def handle_sections(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle education sections management"""
    try:
        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            settings = await settings_repo.get_settings()

            await query.edit_message_text(
                "📚 **Разделы образования**\n\n"
                "Выбери разделы, которые будут использоваться при сборе новостей:\n\n"
                "✅ - включен\n"
                "⬜️ - выключен",
                reply_markup=get_education_sections_keyboard(settings.education_sections or []),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing education sections: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_section_toggle(query, context: ContextTypes.DEFAULT_TYPE):
    """Toggle education section on/off"""
    section_id = query.data.replace("section_toggle_", "")

    try:
        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            settings = await settings_repo.get_settings()

            # Toggle section
            current_sections = settings.education_sections or []
            if section_id in current_sections:
                current_sections.remove(section_id)
            else:
                current_sections.append(section_id)

            # Update settings
            await settings_repo.update_education_sections(current_sections)

            # Update keyboard
            await query.edit_message_reply_markup(
                reply_markup=get_education_sections_keyboard(current_sections)
            )

            await query.answer("✅ Настройки обновлены")

    except Exception as e:
        logger.error(f"Error toggling section {section_id}: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_sources(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle sources management"""
    try:
        async with get_session() as session:
            source_repo = SourceRepository(session)
            sources = await source_repo.get_all()

            if not sources:
                await query.edit_message_text(
                    "🌐 **Управление источниками**\n\n"
                    "❌ Источники не найдены.\n"
                    "Добавь источники через скрипт scripts/add_source.py",
                    reply_markup=get_back_to_admin_menu(),
                    parse_mode='Markdown'
                )
                return

            active_count = sum(1 for s in sources if s.is_active)

            await query.edit_message_text(
                f"🌐 **Управление источниками**\n\n"
                f"Всего источников: {len(sources)}\n"
                f"Активных: {active_count}\n\n"
                f"✅ - включен\n"
                f"⬜️ - выключен",
                reply_markup=get_sources_keyboard(sources),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing sources: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_source_toggle(query, context: ContextTypes.DEFAULT_TYPE):
    """Toggle source on/off"""
    source_id = int(query.data.replace("source_toggle_", ""))

    try:
        async with get_session() as session:
            source_repo = SourceRepository(session)

            # Toggle source
            await source_repo.toggle_active(source_id)

            # Reload all sources
            sources = await source_repo.get_all()
            active_count = sum(1 for s in sources if s.is_active)

            # Update keyboard
            await query.edit_message_text(
                f"🌐 **Управление источниками**\n\n"
                f"Всего источников: {len(sources)}\n"
                f"Активных: {active_count}\n\n"
                f"✅ - включен\n"
                f"⬜️ - выключен",
                reply_markup=get_sources_keyboard(sources),
                parse_mode='Markdown'
            )

            await query.answer("✅ Источник обновлен")

    except Exception as e:
        logger.error(f"Error toggling source {source_id}: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_schedule_settings(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle publication schedule settings"""
    try:
        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            settings = await settings_repo.get_settings()

            await query.edit_message_text(
                f"⏰ **Настройка времени публикаций**\n\n"
                f"Текущее время: {settings.publication_hour:02d}:00\n"
                f"Публикаций в день: {settings.publication_frequency}\n\n"
                f"Выбери час для публикации:",
                reply_markup=get_schedule_settings_keyboard(settings.publication_hour),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing schedule settings: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_schedule_hour(query, context: ContextTypes.DEFAULT_TYPE):
    """Set publication hour"""
    hour = int(query.data.replace("schedule_hour_", ""))

    try:
        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            settings = await settings_repo.get_settings()

            # Update hour
            await settings_repo.update_publication_schedule(hour, settings.publication_frequency)

            # Update keyboard
            await query.edit_message_text(
                f"⏰ **Настройка времени публикаций**\n\n"
                f"Текущее время: {hour:02d}:00\n"
                f"Публикаций в день: {settings.publication_frequency}\n\n"
                f"Выбери час для публикации:",
                reply_markup=get_schedule_settings_keyboard(hour),
                parse_mode='Markdown'
            )

            await query.answer(f"✅ Время обновлено: {hour:02d}:00")

    except Exception as e:
        logger.error(f"Error setting schedule hour: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_language(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    try:
        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            settings = await settings_repo.get_settings()

            await query.edit_message_text(
                f"🌍 **Язык контента**\n\n"
                f"Выбери язык для генерации контента:",
                reply_markup=get_language_keyboard(settings.language),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing language settings: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_language_set(query, context: ContextTypes.DEFAULT_TYPE):
    """Set content language"""
    language = query.data.replace("language_set_", "")

    try:
        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            await settings_repo.update_language(language)

            lang_names = {'ru': 'Русский', 'kz': 'Казахский', 'en': 'English'}

            await query.edit_message_text(
                f"🌍 **Язык контента**\n\n"
                f"Выбери язык для генерации контента:",
                reply_markup=get_language_keyboard(language),
                parse_mode='Markdown'
            )

            await query.answer(f"✅ Язык изменен: {lang_names.get(language, language)}")

    except Exception as e:
        logger.error(f"Error setting language: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_post_length(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle post length settings"""
    try:
        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            settings = await settings_repo.get_settings()

            await query.edit_message_text(
                f"📏 **Настройка длины постов**\n\n"
                f"Выбери желаемую длину для постов:",
                reply_markup=get_post_length_keyboard(settings.post_length),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing post length settings: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_length_set(query, context: ContextTypes.DEFAULT_TYPE):
    """Set post length"""
    length = query.data.replace("length_set_", "")

    try:
        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            await settings_repo.update_post_length(length)

            length_names = {
                'short': 'Короткий',
                'medium': 'Средний',
                'long': 'Длинный'
            }

            await query.edit_message_text(
                f"📏 **Настройка длины постов**\n\n"
                f"Выбери желаемую длину для постов:",
                reply_markup=get_post_length_keyboard(length),
                parse_mode='Markdown'
            )

            await query.answer(f"✅ Длина изменена: {length_names.get(length, length)}")

    except Exception as e:
        logger.error(f"Error setting post length: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_images(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle images settings"""
    try:
        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            settings = await settings_repo.get_settings()

            # Create keyboard with toggle button
            current_status = "✅ Включены" if settings.images_enabled else "❌ Выключены"
            toggle_action = "disable" if settings.images_enabled else "enable"
            toggle_text = "🚫 Выключить" if settings.images_enabled else "✅ Включить"

            keyboard = [
                [
                    InlineKeyboardButton(
                        f"{toggle_text} изображения",
                        callback_data=f"admin_images_{toggle_action}"
                    )
                ],
                [InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")]
            ]

            await query.edit_message_text(
                f"🖼️ **Настройка изображений**\n\n"
                f"Текущий статус: {current_status}\n\n"
                f"Когда изображения включены, бот будет:\n"
                f"• Использовать картинки из статей\n"
                f"• Генерировать изображения через DALL-E\n\n"
                f"Когда выключены:\n"
                f"• Посты будут только с текстом",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing images settings: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_set_images(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle images enable/disable"""
    try:
        action = query.data.split('_')[-1]  # 'enable' or 'disable'
        enabled = action == 'enable'

        async with get_session() as session:
            settings_repo = SettingsRepository(session)
            settings = await settings_repo.get_settings()

            settings.images_enabled = enabled
            await session.commit()

            status_text = "включены" if enabled else "выключены"
            await query.answer(f"✅ Изображения {status_text}")

            # Refresh the images settings page
            await handle_images(query, context)

    except Exception as e:
        logger.error(f"Error setting images: {e}")
        await query.answer(f"❌ Ошибка: {e}", show_alert=True)


async def handle_run_research(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual research trigger"""
    try:
        await query.edit_message_text(
            "🔍 **Запуск ресерча**\n\n"
            "⏳ Запускаю сбор новостей из источников...\n"
            "Это может занять несколько минут.",
            reply_markup=get_back_to_admin_menu(),
            parse_mode='Markdown'
        )

        # Import and run scraper
        from src.scraper.scheduler import ScraperScheduler

        async with get_session() as session:
            source_repo = SourceRepository(session)
            sources = await source_repo.get_active_sources()

            if not sources:
                await query.edit_message_text(
                    "🔍 **Запуск ресерча**\n\n"
                    "❌ Нет активных источников.\n"
                    "Сначала добавь и активируй источники.",
                    reply_markup=get_back_to_admin_menu(),
                    parse_mode='Markdown'
                )
                return

        # Run scraping
        scheduler = ScraperScheduler()
        await scheduler.run_daily_scraping()

        # Get results
        async with get_session() as session:
            from sqlalchemy import select, func
            from src.database.models import Article
            from datetime import datetime, timedelta

            # Count articles created in last 5 minutes
            recent_time = datetime.now() - timedelta(minutes=5)
            result = await session.execute(
                select(func.count(Article.id)).where(Article.created_at >= recent_time)
            )
            total_articles = result.scalar() or 0

            await query.edit_message_text(
                f"🔍 **Запуск ресерча**\n\n"
                f"✅ Ресерч завершен!\n\n"
                f"Обработано источников: {len(sources)}\n"
                f"Найдено новых статей: {total_articles}",
                reply_markup=get_back_to_admin_menu(),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error running research: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await query.edit_message_text(
            f"🔍 **Запуск ресерча**\n\n"
            f"❌ Ошибка при запуске: {str(e)}",
            reply_markup=get_back_to_admin_menu(),
            parse_mode='Markdown'
        )


async def handle_history(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle post history view"""
    try:
        async with get_session() as session:
            post_repo = PostRepository(session)

            # Get last 10 published posts
            posts = await post_repo.get_published_posts(limit=10)

            if not posts:
                await query.edit_message_text(
                    "📜 **История опубликованных постов**\n\n"
                    "❌ Нет опубликованных постов.",
                    reply_markup=get_back_to_admin_menu(),
                    parse_mode='Markdown'
                )
                return

            # Format post history
            history_text = "📜 **История опубликованных постов**\n\n"
            history_text += f"Всего постов: {len(posts)}\n\n"

            for i, post in enumerate(posts[:10], 1):
                pub_date = post.published_at.strftime('%d.%m.%Y %H:%M') if post.published_at else 'N/A'
                # Truncate content to 50 chars
                content_preview = post.content[:50] + "..." if len(post.content) > 50 else post.content
                history_text += f"{i}. {pub_date}\n   {content_preview}\n\n"

            await query.edit_message_text(
                history_text,
                reply_markup=get_back_to_admin_menu(),
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error showing history: {e}")
        await query.edit_message_text(
            f"📜 **История постов**\n\n"
            f"❌ Ошибка: {e}",
            reply_markup=get_back_to_admin_menu(),
            parse_mode='Markdown'
        )


async def handle_analytics(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle analytics view - show charts and statistics"""
    try:
        await query.edit_message_text(
            "📊 **Аналитика постов**\n\n"
            "⏳ Собираю данные и генерирую диаграммы...",
            reply_markup=get_back_to_admin_menu(),
            parse_mode='Markdown'
        )

        async with get_session() as session:
            post_repo = PostRepository(session)

            # Get last 5 published posts
            posts = await post_repo.get_published_posts(limit=5)

            if not posts:
                await query.edit_message_text(
                    "📊 **Аналитика постов**\n\n"
                    "❌ Нет опубликованных постов для анализа.",
                    reply_markup=get_back_to_admin_menu(),
                    parse_mode='Markdown'
                )
                return

            # Get analytics service
            from src.services.analytics_service import AnalyticsService
            from src.services.telegram_stats_service import TelegramStatsService

            analytics_service = AnalyticsService(context.bot)
            stats_service = TelegramStatsService(context.bot)

            # Update statistics from Telegram if posts have real channel/message IDs
            has_real_data = any(post.channel_id and post.message_id for post in posts)

            if has_real_data:
                await query.edit_message_text(
                    "📊 **Аналитика постов**\n\n"
                    "📡 Обновляю статистику из Telegram...",
                    reply_markup=get_back_to_admin_menu(),
                    parse_mode='Markdown'
                )

                # Update stats for all posts
                update_results = await stats_service.bulk_update_statistics(posts)
                await session.commit()

                logger.info(f"Stats update: {update_results}")

            # Check if we have real data or should use mock
            use_mock = not has_real_data or all(
                post.views_count == 0 and post.reactions_count == 0
                for post in posts
            )

            if use_mock:
                # Use mock data for demonstration
                statistics = await analytics_service.get_mock_statistics(posts)
            else:
                # Use real data from DB
                statistics = await analytics_service.get_post_statistics(posts, use_real_data=True)

            # Generate chart
            chart_image = analytics_service.generate_analytics_chart(statistics)

            # Generate text summary
            text_summary = analytics_service.generate_text_analytics(statistics)

            # Send chart as photo
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=chart_image,
                caption=text_summary,
                parse_mode='Markdown'
            )

            # Update original message
            await query.edit_message_text(
                "📊 **Аналитика отправлена!**\n\n"
                "Диаграмма и статистика выше ⬆️",
                reply_markup=get_back_to_admin_menu(),
                parse_mode='Markdown'
            )

            logger.info("Analytics chart sent successfully")

    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        await query.edit_message_text(
            f"📊 **Аналитика**\n\n"
            f"❌ Ошибка при генерации аналитики: {e}",
            reply_markup=get_back_to_admin_menu(),
            parse_mode='Markdown'
        )
