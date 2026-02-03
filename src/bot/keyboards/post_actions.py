"""Inline keyboards for post actions"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_digest_keyboard(digest_id: int, status: str = 'draft') -> InlineKeyboardMarkup:
    """
    Create keyboard for digest management

    Args:
        digest_id: ID of the digest
        status: Current status of digest (draft, approved, rejected, published)

    Returns:
        InlineKeyboardMarkup with action buttons
    """
    keyboard = []

    # For draft or rejected digests - show approve/reject/regenerate
    if status in ['draft', 'rejected']:
        # Main actions row
        keyboard.append([
            InlineKeyboardButton(
                "✅ Утвердить",
                callback_data=f"approve_{digest_id}"
            ),
            InlineKeyboardButton(
                "❌ Отклонить",
                callback_data=f"reject_{digest_id}"
            )
        ])
        # Edit actions row
        keyboard.append([
            InlineKeyboardButton(
                "✏️ Редактировать",
                callback_data=f"edit_{digest_id}"
            ),
            InlineKeyboardButton(
                "🔄 Пересоздать",
                callback_data=f"regenerate_{digest_id}"
            )
        ])
        # Media and scheduling row
        keyboard.append([
            InlineKeyboardButton(
                "🖼️ Новое фото",
                callback_data=f"regenerate_image_{digest_id}"
            ),
            InlineKeyboardButton(
                "📅 Запланировать",
                callback_data=f"schedule_{digest_id}"
            )
        ])

    # For approved digests - show publish/schedule/edit
    elif status == 'approved':
        # Publish actions row
        keyboard.append([
            InlineKeyboardButton(
                "🚀 Опубликовать сейчас",
                callback_data=f"publish_{digest_id}"
            )
        ])
        keyboard.append([
            InlineKeyboardButton(
                "📅 Запланировать",
                callback_data=f"schedule_{digest_id}"
            )
        ])
        # Edit row
        keyboard.append([
            InlineKeyboardButton(
                "✏️ Редактировать",
                callback_data=f"edit_{digest_id}"
            ),
            InlineKeyboardButton(
                "🖼️ Новое фото",
                callback_data=f"regenerate_image_{digest_id}"
            )
        ])
        # Reject row
        keyboard.append([
            InlineKeyboardButton(
                "❌ Отклонить",
                callback_data=f"reject_{digest_id}"
            )
        ])

    return InlineKeyboardMarkup(keyboard)


def get_schedule_keyboard(digest_id: int) -> InlineKeyboardMarkup:
    """
    Create keyboard for scheduling options

    Args:
        digest_id: ID of the digest

    Returns:
        InlineKeyboardMarkup with scheduling options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "Завтра 10:00",
                callback_data=f"schedule_time_{digest_id}_tomorrow_10"
            ),
            InlineKeyboardButton(
                "Завтра 18:00",
                callback_data=f"schedule_time_{digest_id}_tomorrow_18"
            )
        ],
        [
            InlineKeyboardButton(
                "Послезавтра 10:00",
                callback_data=f"schedule_time_{digest_id}_day_after_10"
            ),
            InlineKeyboardButton(
                "Послезавтра 18:00",
                callback_data=f"schedule_time_{digest_id}_day_after_18"
            )
        ],
        [
            InlineKeyboardButton(
                "📝 Ввести дату вручную",
                callback_data=f"custom_schedule_{digest_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=f"back_to_digest_{digest_id}"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_post_schedule_keyboard(post_id: int) -> InlineKeyboardMarkup:
    """
    Create keyboard for scheduling options for individual posts

    Args:
        post_id: ID of the post

    Returns:
        InlineKeyboardMarkup with scheduling options
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "Завтра 10:00",
                callback_data=f"post_schedule_time_{post_id}_tomorrow_10"
            ),
            InlineKeyboardButton(
                "Завтра 18:00",
                callback_data=f"post_schedule_time_{post_id}_tomorrow_18"
            )
        ],
        [
            InlineKeyboardButton(
                "Послезавтра 10:00",
                callback_data=f"post_schedule_time_{post_id}_day_after_10"
            ),
            InlineKeyboardButton(
                "Послезавтра 18:00",
                callback_data=f"post_schedule_time_{post_id}_day_after_18"
            )
        ],
        [
            InlineKeyboardButton(
                "📝 Ввести дату вручную",
                callback_data=f"post_custom_schedule_{post_id}"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard(digest_id: int, action: str) -> InlineKeyboardMarkup:
    """
    Create confirmation keyboard

    Args:
        digest_id: ID of the digest
        action: Action to confirm (e.g., 'publish', 'delete')

    Returns:
        InlineKeyboardMarkup with confirmation buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Да, подтверждаю",
                callback_data=f"confirm_{action}_{digest_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data=f"back_to_digest_{digest_id}"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


def get_post_actions_keyboard(post_id: int, has_digest: bool = False) -> InlineKeyboardMarkup:
    """
    Create keyboard for post actions (works for both digest posts and individual article posts)

    Args:
        post_id: ID of the post
        has_digest: True if post is from a digest, False if it's an individual article

    Returns:
        InlineKeyboardMarkup with action buttons
    """
    buttons = [
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"post_edit_{post_id}"),
            InlineKeyboardButton("🖼 Изображение", callback_data=f"post_image_{post_id}")
        ],
        [
            InlineKeyboardButton("📅 Запланировать", callback_data=f"post_schedule_{post_id}"),
            InlineKeyboardButton("✅ Опубликовать", callback_data=f"post_publish_{post_id}")
        ]
    ]

    # For posts from digest - show link to full digest
    if has_digest:
        buttons.append([
            InlineKeyboardButton("📰 Весь дайджест", callback_data=f"show_digest_from_post_{post_id}")
        ])
    # For individual article posts - show link to original article
    else:
        buttons.append([
            InlineKeyboardButton("🔗 Оригинал статьи", callback_data=f"post_original_{post_id}")
        ])

    buttons.append([
        InlineKeyboardButton("❌ Отклонить", callback_data=f"post_reject_{post_id}")
    ])

    return InlineKeyboardMarkup(buttons)
