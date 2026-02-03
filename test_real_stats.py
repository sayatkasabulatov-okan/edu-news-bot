"""Test what real statistics we can get from Telegram"""
import asyncio
from telegram import Bot

from src.config import settings


async def test_real_telegram_stats():
    """Test what statistics Telegram Bot API actually provides"""

    print("🔍 Проверка доступной статистики из Telegram API\n")
    print("=" * 60)

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    # Get the test post we published
    channel_id = settings.CHANNEL_ID
    message_id = 7  # The post we just published

    print(f"📊 Проверка поста в канале:")
    print(f"   Channel ID: {channel_id}")
    print(f"   Message ID: {message_id}\n")

    try:
        # Method 1: Copy message (gets basic info)
        print("1️⃣ Метод: Copy Message")
        copied = await bot.copy_message(
            chat_id=settings.MODERATOR_CHAT_ID,
            from_chat_id=channel_id,
            message_id=message_id
        )
        await bot.delete_message(
            chat_id=settings.MODERATOR_CHAT_ID,
            message_id=copied.message_id
        )
        print(f"   ✅ Копирование работает")

        # Method 2: Forward and check
        print("\n2️⃣ Метод: Forward Message")
        forwarded = await bot.forward_message(
            chat_id=settings.MODERATOR_CHAT_ID,
            from_chat_id=channel_id,
            message_id=message_id
        )

        print(f"   Информация о сообщении:")
        print(f"   - Text: {forwarded.text[:50] if forwarded.text else 'N/A'}...")
        print(f"   - Date: {forwarded.date}")
        print(f"   - Chat: {forwarded.chat.title}")

        # Check what statistics are available
        print(f"\n   📊 Доступная статистика:")

        if hasattr(forwarded, 'views'):
            print(f"   - Views: {forwarded.views} ✅")
        else:
            print(f"   - Views: ❌ Не доступно через Bot API")

        if hasattr(forwarded, 'forwards'):
            print(f"   - Forwards: {forwarded.forwards} ✅")
        else:
            print(f"   - Forwards: ❌ Не доступно")

        if hasattr(forwarded, 'reactions') and forwarded.reactions:
            total_reactions = sum(r.total_count for r in forwarded.reactions.reactions)
            print(f"   - Reactions: {total_reactions} ✅")
        else:
            print(f"   - Reactions: ❌ Пока нет реакций")

        # Clean up
        await bot.delete_message(
            chat_id=settings.MODERATOR_CHAT_ID,
            message_id=forwarded.message_id
        )

        # Method 3: Get chat administrators (check bot's rights)
        print("\n3️⃣ Права бота в канале:")
        admins = await bot.get_chat_administrators(channel_id)
        bot_admin = next((a for a in admins if a.user.id == bot.id), None)

        if bot_admin:
            print(f"   ✅ Бот - администратор")
            print(f"   - Может получать статистику администратора")
            print(f"   - НО Bot API все равно не дает просмотры!")
        else:
            print(f"   ❌ Бот не администратор")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("📝 ВЫВОД:")
    print("\n✅ ЧТО МОЖНО получить через Bot API:")
    print("   - Количество реакций (если есть)")
    print("   - Базовую информацию о сообщении")
    print("   - Количество подписчиков канала")

    print("\n❌ ЧТО НЕЛЬЗЯ получить через Bot API:")
    print("   - Точное количество просмотров")
    print("   - Количество пересылок")
    print("   - Детальную аналитику")

    print("\n💡 РЕШЕНИЯ:")
    print("   1. Использовать Telegram Analytics (веб-версия)")
    print("   2. Telegram Analytics API (требует MTProto)")
    print("   3. Собирать реакции + приблизительно считать просмотры")
    print("   4. Ручной ввод данных из официальной статистики")


if __name__ == "__main__":
    asyncio.run(test_real_telegram_stats())
