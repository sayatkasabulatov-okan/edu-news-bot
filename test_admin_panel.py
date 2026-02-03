"""Test admin panel command"""
import asyncio
from telegram import Bot
from src.config import settings


async def test_admin_command():
    """Send /admin command to test admin panel"""
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    # Send /admin command
    message = await bot.send_message(
        chat_id=settings.MODERATOR_CHAT_ID,
        text="/admin"
    )

    print(f"✅ Отправлена команда /admin")
    print(f"   Message ID: {message.message_id}")
    print(f"\nПроверь Telegram - должна появиться админ-панель с кнопками:")
    print("   📚 Разделы образования")
    print("   🌐 Источники")
    print("   ⏰ Время публикаций")
    print("   🌍 Язык контента")
    print("   📏 Длина постов")
    print("   🔍 Запустить ресерч")
    print("   📜 История постов")


if __name__ == "__main__":
    asyncio.run(test_admin_command())
