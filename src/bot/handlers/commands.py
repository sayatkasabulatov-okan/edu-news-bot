"""Command handlers for the bot"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from src.config import settings
from src.database.connection import get_session
from src.database.repositories.digest_repo import DigestRepository
from src.database.repositories.post_repo import PostRepository
from src.database.repositories.article_repo import ArticleRepository
from src.database.models import Source, Article
from sqlalchemy import select, desc


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "друг"

    if not settings.is_moderator(user_id):
        await update.message.reply_text(
            "🚫 <b>Доступ ограничен</b>\n\n"
            "К сожалению, этот бот доступен только для администратора.\n\n"
            "📢 Подпишись на наш канал: @eksperimentysayata",
            parse_mode='HTML'
        )
        return

    welcome_message = f"""
🎓 <b>Добро пожаловать, {user_name}!</b>

Я — твой личный помощник для управления образовательным каналом.

<b>🤖 Что я умею:</b>
✅ Автоматически собираю новости про образование за рубежом
✅ Создаю AI-выжимки из 10+ источников
✅ Генерирую изображения к постам
✅ Проверяю контент на точность
✅ Публикую по расписанию

<b>📊 Мои источники:</b>
• Стипендии и гранты
• Программы обмена
• Онлайн-курсы
• Образовательные реформы
• Международные программы

<b>🎯 Что дальше?</b>
Когда будет готов новый дайджест, я отправлю его тебе с кнопками для:
• ✏️ Редактирования
• 🖼️ Смены изображения
• 📅 Планирования публикации
• 🚀 Мгновенной публикации

<i>Используй меню ниже для навигации 👇</i>
    """

    from src.bot.keyboards.main_menu import get_main_menu_keyboard, get_main_menu_reply_keyboard

    await update.message.reply_text(
        welcome_message,
        parse_mode='HTML',
        reply_markup=get_main_menu_reply_keyboard()
    )

    # Send inline menu as well
    await update.message.reply_text(
        "⚙️ <b>Быстрое меню:</b>",
        parse_mode='HTML',
        reply_markup=get_main_menu_keyboard()
    )

    logger.info(f"User {user_id} started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = """
📚 <b>Справка по боту</b>

<b>🤖 Автоматические функции:</b>
• Сбор новостей каждый день в {hour}:00
• Создание AI-выжимок из {min_articles}+ статей
• Генерация изображений через DALL-E
• Проверка контента на галлюцинации
• Отправка дайджестов модератору

<b>✨ Кнопки модерации:</b>
✅ <b>Утвердить</b> — одобрить дайджест
✏️ <b>Редактировать</b> — изменить текст
🖼️ <b>Новое изображение</b> — сгенерировать другую картинку
🔄 <b>Сгенерировать заново</b> — создать новый дайджест
📅 <b>Запланировать</b> — выбрать время публикации
🚀 <b>Опубликовать</b> — опубликовать сразу
❌ <b>Отклонить</b> — отклонить дайджест

<b>🔧 Админ-панель (/admin):</b>
• 📚 Разделы образования
• 🌐 Источники
• ⏰ Время публикаций
• 🌍 Язык контента
• 📏 Длина постов
• 🖼️ Изображения (вкл/выкл)
• 🔍 Запустить ресерч
• 📜 История постов
• 📊 Аналитика

<b>📋 Команды:</b>
/start — главное меню
/help — эта справка
/stats — статистика
/admin — админ-панель
/collect — собрать новости вручную

<b>⚙️ Текущие настройки:</b>
• Парсинг: каждый день в {hour}:00
• Минимум статей для дайджеста: {min_articles}
• Источников активно: 10
• Канал: @eksperimentysayata

<i>💡 Совет: используй кнопочное меню для быстрой навигации!</i>
    """.format(
        hour=settings.SCRAPING_SCHEDULE_HOUR,
        min_articles=settings.MIN_ARTICLES_FOR_DIGEST
    )

    from src.bot.keyboards.main_menu import get_main_menu_keyboard

    await update.message.reply_text(
        help_message,
        parse_mode='HTML',
        reply_markup=get_main_menu_keyboard()
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - show statistics"""
    user_id = update.effective_user.id

    if not settings.is_moderator(user_id):
        await update.message.reply_text(
            "У вас нет доступа к этому боту."
        )
        return

    try:
        async with get_session() as session:
            from sqlalchemy import select, func
            from src.database.models import Post

            digest_repo = DigestRepository(session)
            post_repo = PostRepository(session)

            # Get statistics
            all_digests = await digest_repo.get_all(limit=1000)
            draft_digests = await digest_repo.get_by_status('draft')
            all_posts = await post_repo.get_all(limit=1000)

            # Count posts by type
            digest_posts_count = len([p for p in all_posts if p.digest_id is not None])
            article_posts_count = len([p for p in all_posts if p.article_id is not None])
            published_digest_posts = len([p for p in all_posts if p.digest_id and p.status == 'published'])
            published_article_posts = len([p for p in all_posts if p.article_id and p.status == 'published'])

            stats_message = f"""
📊 Статистика бота

📰 Дайджесты:
- Всего создано: {len(all_digests)}
- Черновики: {len([d for d in all_digests if d.status == 'draft'])}
- Запланированные: {len([d for d in all_digests if d.status == 'scheduled'])}
- Опубликованные: {len([d for d in all_digests if d.status == 'published'])}

📄 Посты:
- Из дайджестов: {digest_posts_count} (опубликовано: {published_digest_posts})
- Индивидуальные статьи: {article_posts_count} (опубликовано: {published_article_posts})
- Всего опубликовано: {published_digest_posts + published_article_posts}

📈 Режим работы: {'📄 Индивидуальные статьи' if settings.ENABLE_ARTICLE_MODE else '📰 Дайджесты'}
            """

            await update.message.reply_text(stats_message)

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await update.message.reply_text(
            "Ошибка при получении статистики. Проверь логи."
        )


async def collect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /collect command - manually run news collection"""
    user_id = update.effective_user.id

    if not settings.is_moderator(user_id):
        await update.message.reply_text(
            "У вас нет доступа к этому боту."
        )
        return

    try:
        # Send initial message
        status_message = await update.message.reply_text(
            "🔄 Запускаю сбор новостей...\n\nЭто может занять несколько минут."
        )

        # Import scraper scheduler
        from src.scraper.scheduler import ScraperScheduler

        # Create scheduler instance and run scraping
        scheduler = ScraperScheduler()

        # Get all active sources
        async with get_session() as session:
            result = await session.execute(
                select(Source).where(Source.is_active == True)
            )
            sources = result.scalars().all()

            if not sources:
                await status_message.edit_text(
                    "❌ Нет активных источников для парсинга.\n"
                    "Добавьте источники через скрипт add_sources.py"
                )
                return

            article_repo = ArticleRepository(session)
            total_new_articles = 0
            results_by_source = []

            # Run scraping for each source
            for source in sources:
                try:
                    await status_message.edit_text(
                        f"🔄 Собираю новости из:\n{source.name}..."
                    )

                    new_count = await scheduler._scrape_source(source, article_repo)
                    total_new_articles += new_count

                    results_by_source.append(f"• {source.name}: {new_count} новых")

                    # Update last_checked_at
                    from datetime import datetime
                    source.last_checked_at = datetime.now()

                    logger.info(f"Manually scraped {new_count} articles from {source.name}")

                except Exception as e:
                    logger.error(f"Error scraping {source.name}: {e}")
                    results_by_source.append(f"• {source.name}: ошибка")
                    continue

            await session.commit()

        # Prepare results message
        results_text = "\n".join(results_by_source)

        # Ensure settings is available (fix for shadowing issue)
        from src.config import settings as config_settings

        if total_new_articles > 0:
            final_message = f"""
✅ Сбор новостей завершен!

Результаты:
{results_text}

📊 Всего новых статей: {total_new_articles}

{'✨ Достаточно для создания дайджеста!' if total_new_articles >= settings.MIN_ARTICLES_FOR_DIGEST else f'⏳ Нужно еще {settings.MIN_ARTICLES_FOR_DIGEST - total_new_articles} статей для дайджеста'}
            """
        else:
            final_message = f"""
✅ Сбор новостей завершен.

Результаты:
{results_text}

ℹ️ Новых статей не найдено.
Все статьи уже были собраны ранее.
            """

        await status_message.edit_text(final_message)

        # Show last collected articles if no new ones
        if total_new_articles == 0:
            async with get_session() as session:
                article_repo = ArticleRepository(session)

                # Get last 5 articles from database
                result = await session.execute(
                    select(Article)
                    .order_by(desc(Article.scraped_at))
                    .limit(5)
                )
                last_articles = result.scalars().all()

                if last_articles:
                    articles_list = []
                    for i, article in enumerate(last_articles, 1):
                        # Format date
                        date_str = article.scraped_at.strftime('%d.%m.%Y %H:%M') if article.scraped_at else 'Дата неизвестна'

                        # Truncate title if too long
                        title = article.title[:80] + '...' if len(article.title) > 80 else article.title

                        articles_list.append(f"{i}. {title}\n   📅 {date_str}")

                    last_articles_text = "\n\n".join(articles_list)

                    await update.message.reply_text(
                        f"📚 Последние 5 собранных статей:\n\n{last_articles_text}"
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ В базе данных пока нет ни одной статьи.\n"
                        "Парсеры могут не находить статьи, или нужно настроить CSS-селекторы."
                    )

        # If enough articles, trigger digest creation
        if total_new_articles >= settings.MIN_ARTICLES_FOR_DIGEST:
            await update.message.reply_text(
                "🤖 Создаю AI-выжимку из новых статей...\n"
                "Это может занять минуту."
            )

            # Trigger digest creation
            from src.services.digest_service import DigestService
            from src.bot.keyboards.post_actions import get_digest_keyboard

            async with get_session() as session:
                digest_service = DigestService(session)
                digest_id = await digest_service.create_digest_if_ready()

                if digest_id:
                    # Get the digest content
                    digest = await digest_service.get_digest(digest_id)

                    # Send digest to moderator with action buttons
                    keyboard = get_digest_keyboard(digest_id)

                    message_text = f"📝 **Дайджест #{digest_id}**\n\n{digest.content}\n\n_Что хочешь сделать с этим дайджестом?_"

                    for mod_id in settings.moderator_ids:
                        try:
                            await context.bot.send_message(
                                chat_id=mod_id,
                                text=message_text,
                                reply_markup=keyboard,
                                parse_mode='Markdown'
                            )
                        except Exception as e:
                            logger.error(f"Failed to send digest to moderator {mod_id}: {e}")

                    await update.message.reply_text(
                        f"✨ Дайджест #{digest_id} создан и отправлен тебе!"
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ Не удалось создать дайджест. Проверь логи."
                    )

    except Exception as e:
        logger.error(f"Error in manual collection: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при сборе новостей:\n{str(e)}\n\nПроверь логи для деталей."
        )


async def health_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /health command - show background tasks status"""
    user_id = update.effective_user.id

    # Check if user is moderator
    if not settings.is_moderator(user_id):
        await update.message.reply_text("❌ У тебя нет прав для этой команды.")
        return

    from src.utils.task_monitor import task_monitor

    # Get health report
    health_report = task_monitor.get_health_report()

    await update.message.reply_text(
        health_report,
        parse_mode='HTML'
    )

    logger.info(f"Health check requested by user {user_id}")


async def init_sources_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /init_sources command - add default sources to empty database"""
    user_id = update.effective_user.id

    if not settings.is_moderator(user_id):
        await update.message.reply_text("У вас нет доступа к этому боту.")
        return

    try:
        async with get_session() as session:
            # Check if sources already exist
            result = await session.execute(select(Source))
            existing = result.scalars().all()

            if existing:
                sources_list = "\n".join(
                    f"{'✅' if s.is_active else '❌'} {s.name}"
                    for s in existing
                )
                await update.message.reply_text(
                    f"Источники уже есть в базе ({len(existing)}):\n\n{sources_list}"
                )
                return

            # Add all sources (from add_sources + add_new_sources + add_excel_sources)
            sources_data = [
                # Original sources
                {'name': 'Bolashak International Scholarship', 'url': 'https://bolashak.gov.kz/ru/news/', 'parser_class': 'BolashakParser', 'is_active': True},
                {'name': 'Opportunities Circle', 'url': 'https://www.opportunitiescircle.com/scholarships/', 'parser_class': 'OpportunitiesCircleParser', 'is_active': True},
                {'name': 'Opportunities Corners', 'url': 'https://opportunitiescorners.com/category/internships/', 'parser_class': 'OpportunitiesCornersParser', 'is_active': True},
                # New sources
                {'name': 'Bright Scholarship', 'url': 'https://brightscholarship.com/', 'parser_class': 'BrightScholarshipParser', 'is_active': True},
                {'name': 'Global Scholarships (Kazakhstan)', 'url': 'https://globalscholarships.com/scholarship-search/nationality-kazakhstan/', 'parser_class': 'GlobalScholarshipsParser', 'is_active': True},
                {'name': 'SPUBL.kz - Scientific Publications', 'url': 'https://spubl.kz/ru/blog/', 'parser_class': 'SpublParser', 'is_active': True},
                # Excel sources
                {'name': 'ST-GR - Гранты и стипендии', 'url': 'https://st-gr.com/?cat=4', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': 'SICA Grants - Social Innovation', 'url': 'https://socialinnovationca.org/ru/grants-ru/sica-grants/', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': 'Grantist - База грантов', 'url': 'https://grantist.com/', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': 'The Village KZ - Образование', 'url': 'https://www.the-village-kz.com/village/city/education', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': 'Scholars4Dev - Стипендии', 'url': 'https://www.scholars4dev.com/', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': 'Opportunities For Youth', 'url': 'https://opportunitiesforyouth.org/', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': 'Great YOP - Образовательные возможности', 'url': 'https://greatyop.com/fully-funded-scholarships-for-international-students/', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': 'Inform.kz - Новости образования', 'url': 'https://www.inform.kz/', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': 'МОН РК - Министерство образования', 'url': 'https://www.gov.kz/memleket/entities/sci?lang=ru', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': '24.kz - Новости Казахстана', 'url': 'https://24.kz/ru', 'parser_class': 'GenericParser', 'is_active': True},
                {'name': 'Zakon.kz - Законодательство об образовании', 'url': 'https://www.zakon.kz/', 'parser_class': 'GenericParser', 'is_active': True},
            ]

            for sd in sources_data:
                session.add(Source(**sd))

            await session.commit()

            await update.message.reply_text(
                f"✅ Добавлено {len(sources_data)} источников!\n\n"
                + "\n".join(f"• {s['name']}" for s in sources_data)
                + "\n\nТеперь можешь нажать 🔄 Собрать новости"
            )
            logger.info(f"Sources initialized by user {user_id}")

    except Exception as e:
        logger.error(f"Error initializing sources: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")
