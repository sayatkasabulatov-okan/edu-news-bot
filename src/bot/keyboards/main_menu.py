"""Main menu keyboards for the bot"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu inline keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Статистика",
                callback_data="menu_stats"
            ),
            InlineKeyboardButton(
                "ℹ️ Справка",
                callback_data="menu_help"
            )
        ],
        [
            InlineKeyboardButton(
                "📰 Последняя статья",
                callback_data="menu_last_article"
            )
        ],
        [
            InlineKeyboardButton(
                "🔧 Админ-панель",
                callback_data="menu_admin"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Перейти в канал",
                url="https://t.me/eksperimentysayata"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_menu_reply_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu reply keyboard (persistent menu)"""
    keyboard = [
        [
            KeyboardButton("📊 Статистика"),
            KeyboardButton("ℹ️ Справка")
        ],
        [
            KeyboardButton("📰 Последняя статья")
        ],
        [
            KeyboardButton("🔧 Админ-панель"),
            KeyboardButton("🔄 Собрать новости")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
