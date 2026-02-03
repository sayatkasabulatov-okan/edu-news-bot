"""Send test digest to moderator"""
import asyncio
import sys

sys.path.insert(0, '.')

from telegram import Bot
from src.config import settings
from src.database.connection import get_session
from src.database.repositories.digest_repo import DigestRepository
from src.bot.keyboards.post_actions import get_digest_keyboard


async def send_digest():
    """Send digest #2 to moderator"""

    # Initialize bot
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    # Get digest from database
    async with get_session() as session:
        repo = DigestRepository(session)
        digest = await repo.get_by_id(2)

        if not digest:
            print("❌ Дайджест #2 не найден")
            return

        print("📤 Отправляю дайджест модератору...")
        print(f"📸 Изображение: {digest.image_url[:100]}...")

        try:
            # Send image first if available
            if digest.image_url:
                await bot.send_photo(
                    chat_id=settings.MODERATOR_CHAT_ID,
                    photo=digest.image_url,
                    caption=f"📝 Дайджест #{digest.id}"
                )
                print("   ✓ Изображение отправлено")

            # Then send text with buttons
            message = await bot.send_message(
                chat_id=settings.MODERATOR_CHAT_ID,
                text=f"{digest.content}\n\n_Что хочешь сделать с этим дайджестом?_",
                reply_markup=get_digest_keyboard(digest.id, digest.status),
                parse_mode='Markdown'
            )
            print("   ✓ Текст с кнопками отправлен")

            # Save moderator message ID
            await repo.set_moderator_message(digest.id, message.message_id)
            await session.commit()

            print(f"✅ Дайджест отправлен!")
            print(f"   Message ID: {message.message_id}")
            print(f"   Модератор: {settings.MODERATOR_CHAT_ID}")

        except Exception as e:
            print(f"❌ Ошибка при отправке: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Отправка тестового дайджеста\n")
    asyncio.run(send_digest())
