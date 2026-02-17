"""Callback handlers for inline buttons"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from loguru import logger

from src.config import settings
from src.database.connection import get_session
from src.database.repositories.digest_repo import DigestRepository
from src.bot.keyboards.post_actions import (
    get_digest_keyboard,
    get_schedule_keyboard,
    get_confirm_keyboard
)
from src.bot.handlers import admin_callbacks
from src.utils.rate_limiter import rate_limiter
from src.utils.exceptions import (
    DigestNotFoundError,
    DigestAlreadyPublishedError,
    ImageGenerationError,
    PublicationFailedError,
    BotException
)
from src.utils.image_helpers import prepare_photo


async def safe_edit_message(query, text: str, reply_markup=None, parse_mode=None):
    """
    Safely edit a message regardless of whether it has a photo or not.

    Args:
        query: CallbackQuery object
        text: Text or caption to set
        reply_markup: Optional keyboard markup
        parse_mode: Optional parse mode (HTML, Markdown)
    """
    try:
        # Check if message has photo
        has_photo = query.message.photo is not None and len(query.message.photo) > 0

        if has_photo:
            # Edit caption for photo messages
            await query.edit_message_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            # Edit text for text-only messages
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
    except Exception as e:
        # If editing fails, try to delete and send new message
        logger.warning(f"Failed to edit message, trying delete+send: {e}")
        try:
            await query.message.delete()
        except:
            pass

        await query.message.chat.send_message(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )


async def handle_post_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback handler for post action buttons"""
    query = update.callback_query

    callback_data = query.data

    # Route admin callbacks to admin handler
    if callback_data.startswith('admin_'):
        await admin_callbacks.handle_admin_callbacks(update, context)
        return

    await query.answer()

    parts = callback_data.split('_')

    if not parts:
        return

    action = parts[0]

    # Handle individual post actions (post_publish, post_edit, etc.)
    if action == 'post':
        post_action = parts[1] if len(parts) > 1 else None
        if post_action == 'publish':
            await handle_post_publish(query, context)
        elif post_action == 'edit':
            await handle_post_edit(query, context)
        elif post_action == 'image':
            await handle_post_image(query, context)
        elif post_action == 'schedule':
            # Check if it's schedule options or specific time
            if len(parts) > 2 and parts[2] == 'time':
                # post_schedule_time_{post_id}_{when}_{hour}
                await handle_post_schedule_time(query, context)
            else:
                # post_schedule_{post_id}
                await handle_post_schedule(query, context)
        elif post_action == 'reject':
            await handle_post_reject(query, context)
        elif post_action == 'original':
            await handle_post_original(query, context)
        elif post_action == 'custom' and len(parts) > 2 and parts[2] == 'schedule':
            # post_custom_schedule_{post_id}
            await handle_post_custom_schedule(query, context)
        return

    # Route to appropriate handler for digest actions
    if action == 'approve':
        await handle_approve(query, context)
    elif action == 'reject':
        await handle_reject(query, context)
    elif callback_data.startswith('regenerate_image'):
        await handle_regenerate_image(query, context)
    elif action == 'regenerate':
        await handle_regenerate(query, context)
    elif action == 'edit':
        await handle_edit(query, context)
    elif action == 'schedule':
        await handle_schedule(query, context)
    elif action == 'publish':
        await handle_publish(query, context)
    elif action == 'confirm':
        await handle_confirm(query, context)
    elif action == 'back':
        await handle_back(query, context)
    elif callback_data.startswith('schedule_time'):
        await handle_schedule_time(query, context)
    elif action == 'custom':
        await handle_custom_schedule(query, context)


@rate_limiter.limit(seconds=3.0, message="⏰ Подожди немного перед следующим действием")
async def handle_approve(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle approve button click"""
    digest_id = int(query.data.split('_')[1])

    try:
        async with get_session() as session:
            digest_repo = DigestRepository(session)

            # Get digest content
            digest = await digest_repo.get_by_id(digest_id)
            if not digest:
                raise DigestNotFoundError(f"Digest {digest_id} not found")

            # Check if already published
            if digest.status == 'published':
                raise DigestAlreadyPublishedError(f"Digest {digest_id} already published")

            # Update digest status to 'approved'
            await digest_repo.update_status(digest_id, 'approved')
            await session.commit()

        await safe_edit_message(
            query,
            f"✅ Дайджест #{digest_id} утвержден!\n\n{digest.content}\n\n"
            f"_Теперь можешь запланировать или опубликовать его._",
            reply_markup=get_digest_keyboard(digest_id, 'approved'),
            parse_mode='Markdown'
        )

        logger.info(f"Digest {digest_id} approved by user")

    except DigestNotFoundError as e:
        logger.warning(f"Digest not found: {digest_id}")
        await query.answer(e.user_message, show_alert=True)
    except DigestAlreadyPublishedError as e:
        logger.warning(f"Digest already published: {digest_id}")
        await query.answer(e.user_message, show_alert=True)
    except BotException as e:
        logger.error(f"Bot error approving digest {digest_id}: {e}")
        await query.answer(e.user_message, show_alert=True)
    except Exception as e:
        logger.error(f"Unexpected error approving digest {digest_id}: {e}")
        await query.answer("❌ Произошла ошибка. Попробуй позже", show_alert=True)


async def handle_reject(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle reject button click"""
    digest_id = int(query.data.split('_')[1])

    await query.edit_message_reply_markup(
        reply_markup=get_confirm_keyboard(digest_id, 'reject')
    )

    logger.info(f"User requested confirmation for rejecting digest {digest_id}")


@rate_limiter.limit(seconds=5.0, message="⏰ Генерация требует времени, подожди")
async def handle_regenerate(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle regenerate button click - create new digest from same articles"""
    digest_id = int(query.data.split('_')[1])

    try:
        await safe_edit_message(query, "🔄 Генерирую новый дайджест...\n\nПодожди минуту.")

        async with get_session() as session:
            digest_repo = DigestRepository(session)

            # Get old digest
            old_digest = await digest_repo.get_by_id(digest_id)
            if not old_digest:
                await safe_edit_message(query, "❌ Дайджест не найден")
                return

            # Mark old digest as rejected
            await digest_repo.update_status(digest_id, 'rejected')

            # Get articles from old digest
            from src.database.repositories.article_repo import ArticleRepository
            article_repo = ArticleRepository(session)

            # Get articles that were used in this digest
            # (We'll get unprocessed articles instead for simplicity)
            from src.services.digest_service import DigestService
            digest_service = DigestService(session)

            # Create new digest
            new_digest_id = await digest_service.create_digest_if_ready()

            await session.commit()

        if new_digest_id:
            await safe_edit_message(
                query,
                f"✅ Новый дайджест создан!\n\n"
                f"Старый дайджест #{digest_id} отклонен.\n"
                f"Новый дайджест #{new_digest_id} будет отправлен тебе отдельным сообщением."
            )

            # Send new digest
            async with get_session() as session:
                digest_repo = DigestRepository(session)
                new_digest = await digest_repo.get_by_id(new_digest_id)

            from src.bot.keyboards.post_actions import get_digest_keyboard
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"📝 **Дайджест #{new_digest_id}**\n\n{new_digest.content}\n\n_Что хочешь сделать с этим дайджестом?_",
                reply_markup=get_digest_keyboard(new_digest_id),
                parse_mode='Markdown'
            )

            logger.info(f"Digest {digest_id} rejected, new digest {new_digest_id} created")
        else:
            await safe_edit_message(
                query,
                f"❌ Не удалось создать новый дайджест.\n"
                f"Возможно, недостаточно новых статей."
            )

    except Exception as e:
        logger.error(f"Error regenerating digest {digest_id}: {e}")
        await safe_edit_message(query, f"❌ Ошибка: {e}")


async def handle_edit(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle edit button click"""
    digest_id = int(query.data.split('_')[1])

    try:
        # Get current digest content
        async with get_session() as session:
            digest_repo = DigestRepository(session)
            digest = await digest_repo.get_by_id(digest_id)

            if not digest:
                await query.message.reply_text("❌ Дайджест не найден")
                return

        # Send current text for copying and editing
        await query.message.reply_text(
            "📝 **Редактирование дайджеста**\n\n"
            "Текущий текст ниже. Скопируй его, отредактируй и отправь обратно.\n\n"
            "Используй форматирование:\n"
            "- <b>жирный текст</b>\n"
            "- <i>курсив</i>\n"
            "- <code>код</code>\n\n"
            "Отправь /cancel для отмены.",
            parse_mode='HTML'
        )

        # Send current content in separate message for easy copying
        await query.message.reply_text(
            digest.content,
            parse_mode='HTML'
        )

        # Store context for text handler with TTL
        import time
        context.user_data['editing_digest_id'] = digest_id
        context.user_data['awaiting_edit'] = True
        context.user_data['edit_started_at'] = time.time()

        logger.info(f"User started editing digest {digest_id}")

    except Exception as e:
        logger.error(f"Error in handle_edit: {e}")
        await query.message.reply_text(f"❌ Ошибка: {e}")


async def handle_schedule(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle schedule button click"""
    digest_id = int(query.data.split('_')[1])

    await query.edit_message_reply_markup(
        reply_markup=get_schedule_keyboard(digest_id)
    )

    logger.info(f"User opened schedule menu for digest {digest_id}")


async def handle_schedule_time(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle specific schedule time selection"""
    parts = query.data.split('_')
    digest_id = int(parts[2])
    when = parts[3]  # 'tomorrow' or 'day_after'
    hour = int(parts[4])

    # Calculate schedule time
    now = datetime.now()
    days_to_add = 1 if when == 'tomorrow' else 2
    scheduled_time = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days_to_add)

    # Save scheduled time
    try:
        from src.services.post_service import PostService

        async with get_session() as session:
            post_service = PostService(session, context.bot)
            await post_service.schedule_post(digest_id, scheduled_time)

        formatted_time = scheduled_time.strftime('%d.%m.%Y в %H:%M')
        await safe_edit_message(
            query,
            f"✅ Дайджест #{digest_id} запланирован на {formatted_time}",
            reply_markup=None
        )

        logger.info(f"Digest {digest_id} scheduled for {scheduled_time}")

    except Exception as e:
        logger.error(f"Error scheduling digest {digest_id}: {e}")
        await safe_edit_message(
            query,
            f"❌ Ошибка при планировании: {e}",
            reply_markup=get_digest_keyboard(digest_id)
        )


async def handle_custom_schedule(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom schedule input request"""
    digest_id = int(query.data.split('_')[2])

    await query.message.reply_text(
        "📅 Введи дату и время публикации в формате:\n"
        "<code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n\n"
        "Например: <code>15.03.2024 14:30</code>\n\n"
        "Отправь /cancel для отмены.",
        parse_mode='HTML'
    )

    import time
    context.user_data['scheduling_digest_id'] = digest_id
    context.user_data['awaiting_schedule'] = True
    context.user_data['schedule_started_at'] = time.time()

    logger.info(f"User requested custom schedule for digest {digest_id}")


async def handle_publish(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle immediate publish button click"""
    digest_id = int(query.data.split('_')[1])

    await query.edit_message_reply_markup(
        reply_markup=get_confirm_keyboard(digest_id, 'publish')
    )

    logger.info(f"User requested confirmation for publishing digest {digest_id}")


async def handle_confirm(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle confirmation actions"""
    parts = query.data.split('_')
    action = parts[1]  # 'publish', 'reject', etc.
    digest_id = int(parts[2])

    if action == 'publish':
        await confirm_publish(query, context, digest_id)
    elif action == 'reject':
        await confirm_reject(query, context, digest_id)


@rate_limiter.limit(seconds=5.0, message="⏰ Дождись завершения публикации")
async def confirm_publish(query, context: ContextTypes.DEFAULT_TYPE, digest_id: int):
    """Confirm and execute publish action"""
    try:
        from src.services.post_service import PostService

        await safe_edit_message(query, "⏳ Публикую дайджест...")

        async with get_session() as session:
            post_service = PostService(session, context.bot)
            success = await post_service.publish_now(digest_id)

        if success:
            await safe_edit_message(
                query,
                f"✅ Дайджест #{digest_id} успешно опубликован в канале!",
                reply_markup=None
            )
            logger.info(f"Digest {digest_id} published successfully")
        else:
            await safe_edit_message(
                query,
                f"❌ Ошибка при публикации дайджеста #{digest_id}. Проверь логи.",
                reply_markup=get_digest_keyboard(digest_id)
            )

    except Exception as e:
        logger.error(f"Error publishing digest {digest_id}: {e}")
        await safe_edit_message(
            query,
            f"❌ Ошибка: {e}",
            reply_markup=get_digest_keyboard(digest_id)
        )


async def confirm_reject(query, context: ContextTypes.DEFAULT_TYPE, digest_id: int):
    """Confirm and execute reject action"""
    try:
        async with get_session() as session:
            digest_repo = DigestRepository(session)
            await digest_repo.update_status(digest_id, 'rejected')
            await session.commit()

        await safe_edit_message(
            query,
            f"❌ Дайджест #{digest_id} отклонен.",
            reply_markup=None
        )

        logger.info(f"Digest {digest_id} rejected by user")

    except Exception as e:
        logger.error(f"Error rejecting digest {digest_id}: {e}")
        await safe_edit_message(
            query,
            f"❌ Ошибка: {e}",
            reply_markup=get_digest_keyboard(digest_id)
        )


async def handle_back(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button - return to digest keyboard"""
    parts = query.data.split('_')
    digest_id = int(parts[3])  # back_to_digest_{digest_id}

    try:
        async with get_session() as session:
            digest_repo = DigestRepository(session)
            digest = await digest_repo.get_by_id(digest_id)

        if digest:
            await safe_edit_message(
                query,
                digest.content,
                reply_markup=get_digest_keyboard(digest_id, digest.status),
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Error handling back button: {e}")
        await query.answer("Ошибка при возврате")


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for editing or custom scheduling"""
    if not update.effective_user:
        return

    user_id = update.effective_user.id

    if not settings.is_moderator(user_id):
        return

    # Check TTL for edit context (1 hour)
    import time
    if context.user_data.get('awaiting_edit'):
        started_at = context.user_data.get('edit_started_at', 0)
        if time.time() - started_at > 3600:  # 1 hour timeout
            context.user_data.clear()
            await update.message.reply_text(
                "⏰ Время редактирования истекло. Начни заново."
            )
            return
        await process_edit_text(update, context)
        return

    # Check TTL for post edit context (1 hour)
    if context.user_data.get('awaiting_post_edit'):
        started_at = context.user_data.get('post_edit_started_at', 0)
        if time.time() - started_at > 3600:  # 1 hour timeout
            context.user_data.clear()
            await update.message.reply_text(
                "⏰ Время редактирования истекло. Начни заново."
            )
            return
        await process_post_edit_text(update, context)
        return

    # Check TTL for schedule context (1 hour) - digest
    if context.user_data.get('awaiting_schedule'):
        started_at = context.user_data.get('schedule_started_at', 0)
        if time.time() - started_at > 3600:  # 1 hour timeout
            context.user_data.clear()
            await update.message.reply_text(
                "⏰ Время планирования истекло. Начни заново."
            )
            return
        await process_schedule_text(update, context)
        return

    # Check TTL for schedule context (1 hour) - individual post
    if context.user_data.get('awaiting_schedule_time'):
        started_at = context.user_data.get('schedule_time_started_at', 0)
        if time.time() - started_at > 3600:  # 1 hour timeout
            context.user_data.clear()
            await update.message.reply_text(
                "⏰ Время планирования истекло. Начни заново."
            )
            return
        await process_schedule_text(update, context)
        return


async def process_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited text from user"""
    digest_id = context.user_data.get('editing_digest_id')
    new_text = update.message.text

    if new_text == '/cancel':
        context.user_data.clear()
        await update.message.reply_text("❌ Редактирование отменено.")
        return

    try:
        async with get_session() as session:
            digest_repo = DigestRepository(session)
            await digest_repo.update_content(digest_id, new_text)

        await update.message.reply_text(
            "✅ Текст дайджеста обновлен!",
            reply_markup=get_digest_keyboard(digest_id)
        )

        # Clear context
        context.user_data.clear()

        logger.info(f"Digest {digest_id} content updated")

    except Exception as e:
        logger.error(f"Error updating digest {digest_id}: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def process_post_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process edited text for post from user"""
    post_id = context.user_data.get('editing_post_id')
    new_text = update.message.text

    if new_text == '/cancel':
        context.user_data.clear()
        await update.message.reply_text("❌ Редактирование отменено.")
        return

    try:
        async with get_session() as session:
            from src.database.repositories.post_repo import PostRepository
            post_repo = PostRepository(session)
            await post_repo.update_content(post_id, new_text)
            await session.commit()

        from src.bot.keyboards.post_actions import get_post_actions_keyboard
        await update.message.reply_text(
            "✅ Текст поста обновлен!",
            reply_markup=get_post_actions_keyboard(post_id, has_digest=False)
        )

        # Clear context
        context.user_data.clear()

        logger.info(f"Post {post_id} content updated")

    except Exception as e:
        logger.error(f"Error updating post {post_id}: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def process_schedule_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process custom schedule datetime from user (for digest or individual post)"""
    digest_id = context.user_data.get('scheduling_digest_id')
    post_id = context.user_data.get('scheduling_post_id')
    datetime_str = update.message.text.strip()

    if datetime_str == '/cancel':
        context.user_data.clear()
        await update.message.reply_text("❌ Планирование отменено.")
        return

    try:
        # Parse datetime
        scheduled_time = datetime.strptime(datetime_str, '%d.%m.%Y %H:%M')

        # Check if time is in future
        if scheduled_time <= datetime.now():
            await update.message.reply_text(
                "❌ Время должно быть в будущем. Попробуй снова."
            )
            return

        from src.services.post_service import PostService

        async with get_session() as session:
            post_service = PostService(session, context.bot)

            # Check if scheduling digest or individual post
            if digest_id:
                await post_service.schedule_post(digest_id, scheduled_time)
                formatted_time = scheduled_time.strftime('%d.%m.%Y в %H:%M')
                await update.message.reply_text(
                    f"✅ Дайджест #{digest_id} запланирован на {formatted_time}"
                )
                logger.info(f"Digest {digest_id} scheduled for {scheduled_time}")
            elif post_id:
                await post_service.schedule_individual_post(post_id, scheduled_time)
                formatted_time = scheduled_time.strftime('%d.%m.%Y в %H:%M')
                await update.message.reply_text(
                    f"✅ Пост #{post_id} запланирован на {formatted_time}"
                )
                logger.info(f"Post {post_id} scheduled for {scheduled_time}")
            else:
                await update.message.reply_text("❌ Ошибка: не указан ID")
                return

        context.user_data.clear()

    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат. Используй: ДД.ММ.ГГГГ ЧЧ:ММ\n"
            "Например: 15.03.2024 14:30"
        )
    except Exception as e:
        logger.error(f"Error scheduling: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


@rate_limiter.limit(seconds=10.0, message="⏰ Генерация изображения занимает время, подожди")
async def handle_regenerate_image(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle image regeneration for digest"""
    digest_id = int(query.data.split('_')[2])

    try:
        await safe_edit_message(
            query,
            "🖼️ Генерирую новое изображение...\n\n"
            "⏳ Это займет около 20 секунд."
        )

        async with get_session() as session:
            digest_repo = DigestRepository(session)

            # Get digest
            digest = await digest_repo.get_by_id(digest_id)
            if not digest:
                await safe_edit_message(query, "❌ Дайджест не найден")
                return

            # Get articles for this digest
            from src.database.repositories.article_repo import ArticleRepository
            from sqlalchemy import select
            from src.database.models import Article

            result = await session.execute(
                select(Article).where(Article.id.in_(digest.article_ids))
            )
            articles = result.scalars().all()

            if not articles:
                await safe_edit_message(query, "❌ Статьи не найдены")
                return

            # Generate new image from all articles
            from src.services.image_generation_service import ImageGenerationService
            image_service = ImageGenerationService()

            articles_info = [
                {'title': article.title, 'content': article.content or ''}
                for article in articles
            ]
            new_image_url = await image_service.generate_digest_image(articles_info)

            if not new_image_url:
                await safe_edit_message(
                    query,
                    "❌ Не удалось сгенерировать изображение.\nПопробуй еще раз.",
                    reply_markup=get_digest_keyboard(digest_id, digest.status)
                )
                return

            # Update digest with new image
            digest.image_url = new_image_url
            await session.commit()

            logger.info(f"New image generated for digest {digest_id}")

            # Resend digest to moderator with new image
            from src.database.repositories.source_repo import SourceRepository
            from src.database.models import Source

            # Get articles and sources for display
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

            articles_data = [
                {'url': article.url, 'content': article.content or ''}
                for article, _ in articles_with_sources
            ]

            check_result = checker.check_digest(digest.content, articles_data)

            hallucination_warning = ""
            if check_result['has_issues'] or check_result['warnings']:
                hallucination_warning = "\n\n" + checker.format_warnings(check_result)

            full_message = digest.content + sources_info + hallucination_warning

            # Send message with new image
            if new_image_url:
                # Delete old message
                try:
                    await query.message.delete()
                except:
                    pass

                # Check caption length (Telegram limit is 1024 chars)
                if len(full_message) > 1024:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=prepare_photo(new_image_url)
                    )
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=full_message,
                        reply_markup=get_digest_keyboard(digest_id, digest.status),
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                else:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=prepare_photo(new_image_url),
                        caption=full_message,
                        reply_markup=get_digest_keyboard(digest_id, digest.status),
                        parse_mode='HTML'
                    )

                logger.info(f"Digest {digest_id} resent with new image")
            else:
                # Just update text without image
                await safe_edit_message(
                    query,
                    full_message,
                    reply_markup=get_digest_keyboard(digest_id, digest.status),
                    parse_mode='HTML'
                )

    except Exception as e:
        logger.error(f"Error regenerating image for digest {digest_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

        await safe_edit_message(
            query,
            f"❌ Ошибка при генерации изображения: {str(e)}\n\nПопробуй еще раз.",
            reply_markup=get_digest_keyboard(digest_id, 'draft')
        )


@rate_limiter.limit(seconds=2.0, message="⏰ Подожди немного")
async def handle_post_original(query, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Оригинал статьи" button click
    Shows link to the original article for individual article posts
    """
    post_id = int(query.data.split('_')[-1])

    try:
        async with get_session() as session:
            from sqlalchemy import select
            from sqlalchemy.orm import joinedload
            from src.database.models import Post

            # Get post with article relationship
            result = await session.execute(
                select(Post)
                .options(joinedload(Post.article))
                .where(Post.id == post_id)
            )
            post = result.scalar_one_or_none()

            if not post:
                await query.answer("❌ Пост не найден", show_alert=True)
                return

            if not post.article:
                await query.answer("❌ Оригинальная статья не найдена", show_alert=True)
                return

            # Show article URL in an alert
            await query.answer(
                f"🔗 Оригинал статьи:\n{post.article.url}",
                show_alert=True
            )

            logger.info(f"Showed original article link for post {post_id}")

    except Exception as e:
        logger.error(f"Error showing original article for post {post_id}: {e}")
        await query.answer("❌ Произошла ошибка", show_alert=True)


# ===== Individual Post Action Handlers =====

async def handle_post_publish(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle publish button for individual post"""
    post_id = int(query.data.split('_')[-1])

    try:
        # Check if post is already published
        async with get_session() as session:
            from sqlalchemy import select
            from src.database.models import Post

            result = await session.execute(
                select(Post).where(Post.id == post_id)
            )
            post = result.scalar_one_or_none()

            if not post:
                await query.answer("❌ Пост не найден", show_alert=True)
                return

            if post.status == 'published':
                # Post already published
                published_time = post.published_at.strftime('%d.%m.%Y в %H:%M') if post.published_at else 'неизвестно когда'
                await safe_edit_message(
                    query,
                    f"ℹ️ Статья #{post_id} уже была ранее опубликована ({published_time}).\n\nСсылка на сообщение: https://t.me/c/{str(abs(post.channel_id))[4:]}/{post.message_id}",
                    reply_markup=None
                )
                logger.info(f"User tried to publish already published post {post_id}")
                return

        # Post not published yet, proceed with publishing
        from src.services.post_service import PostService

        await safe_edit_message(query, "⏳ Публикую пост...")

        async with get_session() as session:
            post_service = PostService(session, context.bot)
            success = await post_service.publish_post(post_id)

        if success:
            await safe_edit_message(
                query,
                f"✅ Пост #{post_id} успешно опубликован в канале!",
                reply_markup=None
            )
            logger.info(f"Post {post_id} published successfully")
        else:
            from src.bot.keyboards.post_actions import get_post_actions_keyboard
            await safe_edit_message(
                query,
                f"❌ Ошибка при публикации поста #{post_id}. Проверь логи.",
                reply_markup=get_post_actions_keyboard(post_id, has_digest=False)
            )

    except Exception as e:
        logger.error(f"Error publishing post {post_id}: {e}")
        from src.bot.keyboards.post_actions import get_post_actions_keyboard
        await safe_edit_message(
            query,
            f"❌ Ошибка: {e}",
            reply_markup=get_post_actions_keyboard(post_id, has_digest=False)
        )


async def handle_post_edit(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle edit button for individual post"""
    post_id = int(query.data.split('_')[-1])

    try:
        async with get_session() as session:
            from sqlalchemy import select
            from src.database.models import Post

            result = await session.execute(
                select(Post).where(Post.id == post_id)
            )
            post = result.scalar_one_or_none()

            if not post:
                await query.message.reply_text("❌ Пост не найден")
                return

        # Send current text for editing
        await query.message.reply_text(
            "📝 <b>Редактирование поста</b>\n\n"
            "Текущий текст ниже. Скопируй его, отредактируй и отправь обратно.\n\n"
            "Отправь /cancel для отмены.",
            parse_mode='HTML'
        )

        await query.message.reply_text(
            post.content,
            parse_mode='HTML'
        )

        # Store context
        import time
        context.user_data['editing_post_id'] = post_id
        context.user_data['awaiting_post_edit'] = True
        context.user_data['post_edit_started_at'] = time.time()

        logger.info(f"User started editing post {post_id}")

    except Exception as e:
        logger.error(f"Error in handle_post_edit: {e}")
        await query.message.reply_text(f"❌ Ошибка: {e}")


@rate_limiter.limit(seconds=10.0, message="⏰ Генерация изображения занимает время, подожди")
async def handle_post_image(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle image button for individual post - generate image with DALL-E"""
    post_id = int(query.data.split('_')[-1])

    try:
        await safe_edit_message(
            query,
            "🖼️ Генерирую изображение...\n\n"
            "⏳ Это займет около 20 секунд."
        )

        async with get_session() as session:
            from sqlalchemy import select, update
            from sqlalchemy.orm import joinedload
            from src.database.models import Post, Article

            # Get post with article
            result = await session.execute(
                select(Post)
                .options(joinedload(Post.article))
                .where(Post.id == post_id)
            )
            post = result.scalar_one_or_none()

            if not post:
                await safe_edit_message(query, "❌ Пост не найден")
                return

            if not post.article:
                await safe_edit_message(query, "❌ Статья не найдена")
                return

            # Generate image using DALL-E
            from src.services.image_generation_service import ImageGenerationService
            image_service = ImageGenerationService()

            new_image_url = await image_service.generate_image(
                post.article.title,
                post.article.content
            )

            if not new_image_url:
                from src.bot.keyboards.post_actions import get_post_actions_keyboard
                await safe_edit_message(
                    query,
                    "❌ Не удалось сгенерировать изображение.\nПопробуй еще раз.",
                    reply_markup=get_post_actions_keyboard(post_id, has_digest=False)
                )
                return

            # Update article with new image
            await session.execute(
                update(Article)
                .where(Article.id == post.article.id)
                .values(image_url=new_image_url)
            )
            await session.commit()

            logger.info(f"New image generated for post {post_id}, article {post.article.id}")

            # Resend post to moderator with new image
            from src.bot.keyboards.post_actions import get_post_actions_keyboard

            # Delete old message
            try:
                await query.message.delete()
            except:
                pass

            # Get updated article info
            result = await session.execute(
                select(Post)
                .options(joinedload(Post.article).joinedload(Article.source))
                .where(Post.id == post_id)
            )
            updated_post = result.scalar_one_or_none()

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

            # Format message
            created_str = updated_post.created_at.strftime('%d.%m.%Y %H:%M') if updated_post.created_at else 'Неизвестно'
            source_name = updated_post.article.source.name if updated_post.article and updated_post.article.source else "Неизвестный источник"
            article_url = updated_post.article.url if updated_post.article else None

            message_text = f"""
{status_emoji.get(updated_post.status, '📄')} <b>Статья #{updated_post.id}</b>

<b>Статус:</b> {status_text.get(updated_post.status, updated_post.status)}
<b>Источник:</b> {source_name}
<b>Создана:</b> {created_str}

{updated_post.content}
"""

            if article_url:
                message_text += f"\n\n🔗 <a href='{article_url}'>Оригинал статьи</a>"

            message_text += "\n\n<i>👇 Выбери действие:</i>"

            # Send new message with image (check caption length)
            if len(message_text) > 1024:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=prepare_photo(new_image_url)
                )
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=message_text,
                    reply_markup=get_post_actions_keyboard(post_id, has_digest=False),
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            else:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=prepare_photo(new_image_url),
                    caption=message_text,
                    reply_markup=get_post_actions_keyboard(post_id, has_digest=False),
                    parse_mode='HTML'
                )

            logger.info(f"Post {post_id} resent with new image")

    except Exception as e:
        logger.error(f"Error generating image for post {post_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

        from src.bot.keyboards.post_actions import get_post_actions_keyboard
        await safe_edit_message(
            query,
            f"❌ Ошибка при генерации изображения: {str(e)}\n\nПопробуй еще раз.",
            reply_markup=get_post_actions_keyboard(post_id, has_digest=False)
        )


async def handle_post_schedule(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle schedule button for individual post"""
    post_id = int(query.data.split('_')[-1])

    from src.bot.keyboards.post_actions import get_post_schedule_keyboard

    await query.answer("📅 Выбери время публикации", show_alert=False)

    # Check if message has caption (photo message) or text (text message)
    if query.message.caption:
        # Photo message - edit caption
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n📅 <b>Когда опубликовать?</b>",
            parse_mode='HTML',
            reply_markup=get_post_schedule_keyboard(post_id)
        )
    else:
        # Text message - edit text
        await query.edit_message_text(
            text=query.message.text + "\n\n📅 <b>Когда опубликовать?</b>",
            parse_mode='HTML',
            reply_markup=get_post_schedule_keyboard(post_id),
            disable_web_page_preview=True
        )

    logger.info(f"User opened schedule options for post {post_id}")


async def handle_post_reject(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle reject button for individual post"""
    post_id = int(query.data.split('_')[-1])

    try:
        async with get_session() as session:
            from src.database.repositories.post_repo import PostRepository

            post_repo = PostRepository(session)
            await post_repo.update_status(post_id, 'rejected')
            await session.commit()

        await safe_edit_message(
            query,
            f"❌ Пост #{post_id} отклонен.",
            reply_markup=None
        )

        logger.info(f"Post {post_id} rejected by user")

    except Exception as e:
        logger.error(f"Error rejecting post {post_id}: {e}")
        from src.bot.keyboards.post_actions import get_post_actions_keyboard
        await safe_edit_message(
            query,
            f"❌ Ошибка: {e}",
            reply_markup=get_post_actions_keyboard(post_id, has_digest=False)
        )


async def handle_post_schedule_time(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle specific schedule time selection for individual post"""
    parts = query.data.split('_')
    # post_schedule_time_{post_id}_{when}_{hour}
    post_id = int(parts[3])
    when = parts[4]  # 'tomorrow' or 'day_after'
    hour = int(parts[5])

    # Calculate schedule time
    from datetime import datetime, timedelta
    now = datetime.now()
    days_to_add = 1 if when == 'tomorrow' else 2
    scheduled_time = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days_to_add)

    # Save scheduled time
    try:
        from src.services.post_service import PostService

        async with get_session() as session:
            post_service = PostService(session, context.bot)
            await post_service.schedule_individual_post(post_id, scheduled_time)

        formatted_time = scheduled_time.strftime('%d.%m.%Y в %H:%M')
        await safe_edit_message(
            query,
            f"✅ Пост #{post_id} запланирован на {formatted_time}",
            reply_markup=None
        )

        logger.info(f"Post {post_id} scheduled for {scheduled_time}")

    except Exception as e:
        logger.error(f"Error scheduling post {post_id}: {e}")
        from src.bot.keyboards.post_actions import get_post_actions_keyboard
        await safe_edit_message(
            query,
            f"❌ Ошибка при планировании: {e}",
            reply_markup=get_post_actions_keyboard(post_id, has_digest=False)
        )


async def handle_post_custom_schedule(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom schedule button for individual post - request manual datetime input"""
    parts = query.data.split('_')
    # post_custom_schedule_{post_id}
    post_id = int(parts[3])

    # Save post_id in context for later
    import time
    context.user_data['scheduling_post_id'] = post_id
    context.user_data['awaiting_schedule_time'] = True
    context.user_data['schedule_time_started_at'] = time.time()

    await query.answer("✅ Введи дату и время", show_alert=False)
    await query.edit_message_caption(
        caption=query.message.caption + "\n\n📅 <b>Введи дату и время публикации</b>\nФормат: ДД.ММ.ГГГГ ЧЧ:ММ\nПример: 05.02.2026 14:30\n\nОтправь /cancel для отмены",
        parse_mode='HTML',
        reply_markup=None
    )

    logger.info(f"User requested custom scheduling for post {post_id}")
