"""Telegram bot application initialization"""
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from loguru import logger

from src.config import settings
from src.bot.handlers import commands, callbacks, admin_commands, menu_handlers, admin_dashboard, admin_callbacks


def create_bot_application() -> Application:
    """
    Create and configure Telegram bot application

    Returns:
        Configured Application instance
    """
    # Create application
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", commands.start_command))
    app.add_handler(CommandHandler("help", commands.help_command))
    app.add_handler(CommandHandler("stats", commands.stats_command))
    app.add_handler(CommandHandler("collect", commands.collect_command))
    app.add_handler(CommandHandler("health", commands.health_command))
    app.add_handler(CommandHandler("init_sources", commands.init_sources_command))
    app.add_handler(CommandHandler("admin", admin_commands.admin_command))

    # Extended admin commands
    app.add_handler(CommandHandler("status", admin_dashboard.system_status_command))
    app.add_handler(CommandHandler("cleanup", admin_dashboard.cleanup_command))
    app.add_handler(CommandHandler("logs", admin_dashboard.logs_command))
    app.add_handler(CommandHandler("optimize", admin_dashboard.optimize_db_command))

    # Add callback query handlers for inline buttons
    # Menu callbacks (checked first)
    app.add_handler(CallbackQueryHandler(
        menu_handlers.handle_menu_callback,
        pattern="^menu_"
    ))
    # Admin panel callbacks
    app.add_handler(CallbackQueryHandler(
        admin_callbacks.handle_admin_callbacks,
        pattern="^admin_|^section_|^source_|^schedule_hour_|^language_|^length_"
    ))
    # Post action callbacks
    app.add_handler(CallbackQueryHandler(callbacks.handle_post_actions))

    # Add message handlers for text input
    # Menu button presses (specific filters to avoid conflicts)
    menu_button_filter = filters.Regex("^(📊 Статистика|ℹ️ Справка|🔧 Админ-панель|🔄 Собрать новости|📰 Последний дайджест)$")
    app.add_handler(MessageHandler(
        menu_button_filter,
        menu_handlers.handle_menu_text
    ))
    # Generic text input (editing, scheduling) - for other text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~menu_button_filter,
            callbacks.handle_text_input
        )
    )

    logger.info("Telegram bot application configured")

    return app
