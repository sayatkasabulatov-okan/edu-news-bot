"""Admin panel command handlers"""
from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from src.config import settings
from src.bot.keyboards.admin_keyboards import get_admin_main_menu


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - show admin panel"""
    if not update.effective_user:
        return

    user_id = update.effective_user.id

    # Check if user is moderator
    if user_id != settings.MODERATOR_CHAT_ID:
        await update.message.reply_text(
            "❌ У вас нет прав доступа к админ-панели."
        )
        logger.warning(f"Unauthorized admin access attempt by user {user_id}")
        return

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

    await update.message.reply_text(
        admin_message,
        reply_markup=get_admin_main_menu(),
        parse_mode='HTML'
    )

    logger.info(f"Admin panel opened by user {user_id}")
