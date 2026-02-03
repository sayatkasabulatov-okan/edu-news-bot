"""Test bot permissions and channel access"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError

from src.config import settings


async def test_permissions():
    """Test if bot has proper permissions in the channel"""

    print("🔍 Проверка прав бота в канале\n")
    print("=" * 60)

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    # Test 1: Get bot info
    print("\n1️⃣ Информация о боте:")
    try:
        bot_info = await bot.get_me()
        print(f"   ✅ Бот: @{bot_info.username}")
        print(f"   Имя: {bot_info.first_name}")
        print(f"   ID: {bot_info.id}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return

    # Test 2: Get channel info
    print(f"\n2️⃣ Проверка доступа к каналу (ID: {settings.CHANNEL_ID}):")
    try:
        chat = await bot.get_chat(settings.CHANNEL_ID)
        print(f"   ✅ Название: {chat.title}")
        print(f"   Тип: {chat.type}")
        if chat.username:
            print(f"   Username: @{chat.username}")

        # Get member count
        try:
            member_count = await bot.get_chat_member_count(settings.CHANNEL_ID)
            print(f"   👥 Подписчиков: {member_count:,}")
        except:
            print(f"   ⚠️  Не удалось получить количество подписчиков")

    except TelegramError as e:
        print(f"   ❌ Ошибка доступа к каналу: {e}")
        print(f"\n   💡 Возможные причины:")
        print(f"      - Бот не добавлен в канал")
        print(f"      - Неверный CHANNEL_ID в .env")
        print(f"      - Бот не является администратором")
        return

    # Test 3: Check bot's admin status
    print(f"\n3️⃣ Проверка прав администратора:")
    try:
        bot_member = await bot.get_chat_member(settings.CHANNEL_ID, bot_info.id)
        print(f"   Статус: {bot_member.status}")

        if bot_member.status == "administrator":
            print(f"   ✅ Бот является администратором!")

            # Check specific permissions
            print(f"\n   📋 Права бота:")
            print(f"      • Публикация: {'✅' if bot_member.can_post_messages else '❌'}")
            print(f"      • Редактирование: {'✅' if bot_member.can_edit_messages else '❌'}")
            print(f"      • Удаление: {'✅' if bot_member.can_delete_messages else '❌'}")
            print(f"      • Управление чатом: {'✅' if bot_member.can_manage_chat else '❌'}")

            # Check if all required permissions are granted
            required_perms = [
                bot_member.can_post_messages,
                bot_member.can_edit_messages,
                bot_member.can_delete_messages,
            ]

            if all(required_perms):
                print(f"\n   🎉 ВСЕ необходимые права есть!")
            else:
                print(f"\n   ⚠️  Не хватает некоторых прав. Нужно добавить в настройках канала.")

        elif bot_member.status == "creator":
            print(f"   ✅ Бот является создателем канала!")
        else:
            print(f"   ❌ Бот НЕ администратор!")
            print(f"\n   📝 Что делать:")
            print(f"      1. Открой канал в Telegram")
            print(f"      2. Настройки → Администраторы")
            print(f"      3. Добавь бота @{bot_info.username}")
            print(f"      4. Выдай права: публикация, редактирование, удаление")
            return

    except TelegramError as e:
        print(f"   ❌ Ошибка: {e}")
        return

    # Test 4: Try to send a test message
    print(f"\n4️⃣ Проверка возможности публикации:")
    try:
        test_message = await bot.send_message(
            chat_id=settings.CHANNEL_ID,
            text="🤖 Тестовое сообщение для проверки прав бота\n\nЭто сообщение будет удалено через 2 секунды."
        )
        print(f"   ✅ Сообщение отправлено (ID: {test_message.message_id})")

        # Wait 2 seconds
        await asyncio.sleep(2)

        # Delete test message
        await bot.delete_message(
            chat_id=settings.CHANNEL_ID,
            message_id=test_message.message_id
        )
        print(f"   ✅ Сообщение удалено")

    except TelegramError as e:
        print(f"   ❌ Не удалось отправить сообщение: {e}")
        print(f"\n   💡 Проверь права бота на публикацию и удаление")
        return

    # Summary
    print("\n" + "=" * 60)
    print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("\n🎯 Бот готов к работе со статистикой!")
    print("\n📊 Следующие шаги:")
    print("   1. Опубликуй несколько постов через бота")
    print("   2. Запусти: python update_stats.py")
    print("   3. Проверь аналитику: /admin → 📊 Аналитика")


if __name__ == "__main__":
    asyncio.run(test_permissions())
