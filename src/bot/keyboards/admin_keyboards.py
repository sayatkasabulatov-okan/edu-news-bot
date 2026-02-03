"""Admin panel keyboards"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Get main admin menu keyboard"""
    keyboard = [
        # Content settings row 1
        [
            InlineKeyboardButton(
                "📚 Разделы",
                callback_data="admin_sections"
            ),
            InlineKeyboardButton(
                "🌐 Источники",
                callback_data="admin_sources"
            )
        ],
        # Content settings row 2
        [
            InlineKeyboardButton(
                "🌍 Язык",
                callback_data="admin_language"
            ),
            InlineKeyboardButton(
                "📏 Длина",
                callback_data="admin_length"
            ),
            InlineKeyboardButton(
                "🖼️ Изображения",
                callback_data="admin_images"
            )
        ],
        # Automation row
        [
            InlineKeyboardButton(
                "⏰ Расписание",
                callback_data="admin_schedule"
            ),
            InlineKeyboardButton(
                "🔍 Собрать новости",
                callback_data="admin_run_research"
            )
        ],
        # Monitoring row
        [
            InlineKeyboardButton(
                "📜 История",
                callback_data="admin_history"
            )
            # InlineKeyboardButton(
            #     "📊 Аналитика",
            #     callback_data="admin_analytics"
            # )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_admin_menu() -> InlineKeyboardMarkup:
    """Get back button to admin menu"""
    keyboard = [
        [
            InlineKeyboardButton(
                "◀️ Назад",
                callback_data="admin_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# Education section labels in Russian
SECTION_LABELS = {
    'higher_education': 'Высшее образование',
    'secondary_education': 'Среднее образование',
    'private_schools': 'Частные школы',
    'online_education': 'Онлайн-образование',
    'courses_edtech': 'Курсы и EdTech',
    'grants_scholarships': 'Гранты, стипендии',
    'reforms': 'Образовательные реформы',
    'legislation': 'Законодательство',
    'international': 'Международные программы'
}


def get_education_sections_keyboard(enabled_sections: list) -> InlineKeyboardMarkup:
    """Get keyboard for education sections selection"""
    keyboard = []

    for section_id, label in SECTION_LABELS.items():
        is_enabled = section_id in enabled_sections
        checkbox = "✅" if is_enabled else "⬜️"

        keyboard.append([
            InlineKeyboardButton(
                f"{checkbox} {label}",
                callback_data=f"section_toggle_{section_id}"
            )
        ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            "◀️ Назад",
            callback_data="admin_back"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


def get_sources_keyboard(sources: list) -> InlineKeyboardMarkup:
    """Get keyboard for sources management"""
    keyboard = []

    for source in sources:
        checkbox = "✅" if source.is_active else "⬜️"

        keyboard.append([
            InlineKeyboardButton(
                f"{checkbox} {source.name}",
                callback_data=f"source_toggle_{source.id}"
            )
        ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            "◀️ Назад",
            callback_data="admin_back"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


def get_schedule_settings_keyboard(current_hour: int) -> InlineKeyboardMarkup:
    """Get keyboard for publication schedule settings"""
    keyboard = []

    # Hours selection (6-21)
    hours = [6, 9, 12, 15, 18, 21]
    row = []
    for hour in hours:
        label = f"{'✅' if hour == current_hour else ''} {hour:02d}:00"
        row.append(InlineKeyboardButton(
            label,
            callback_data=f"schedule_hour_{hour}"
        ))
        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            "◀️ Назад",
            callback_data="admin_back"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


def get_language_keyboard(current_language: str) -> InlineKeyboardMarkup:
    """Get keyboard for language selection"""
    languages = {
        'ru': 'Русский 🇷🇺',
        'kz': 'Казахский 🇰🇿',
        'en': 'English 🇬🇧'
    }

    keyboard = []
    for lang_code, lang_name in languages.items():
        checkbox = "✅" if lang_code == current_language else "⬜️"
        keyboard.append([
            InlineKeyboardButton(
                f"{checkbox} {lang_name}",
                callback_data=f"language_set_{lang_code}"
            )
        ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            "◀️ Назад",
            callback_data="admin_back"
        )
    ])

    return InlineKeyboardMarkup(keyboard)


def get_post_length_keyboard(current_length: str) -> InlineKeyboardMarkup:
    """Get keyboard for post length selection"""
    lengths = {
        'short': 'Короткий (1 предложение)',
        'medium': 'Средний (2-3 предложения)',
        'long': 'Длинный (подробно)'
    }

    keyboard = []
    for length_code, length_name in lengths.items():
        checkbox = "✅" if length_code == current_length else "⬜️"
        keyboard.append([
            InlineKeyboardButton(
                f"{checkbox} {length_name}",
                callback_data=f"length_set_{length_code}"
            )
        ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            "◀️ Назад",
            callback_data="admin_back"
        )
    ])

    return InlineKeyboardMarkup(keyboard)
