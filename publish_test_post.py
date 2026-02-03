"""Publish a test post to the channel and track it in DB"""
import asyncio
from datetime import datetime
from telegram import Bot

from src.config import settings
from src.database.connection import get_session
from src.database.repositories.post_repo import PostRepository
from src.database.repositories.digest_repo import DigestRepository


async def publish_test_post():
    """Publish a real test post to the channel"""

    print("📤 Публикация тестового поста в канал\n")
    print("=" * 60)

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    # Create post content
    content = """🎓 <b>Стипендия для обучения в Германии</b>

💰 <b>Покрытие:</b> 100% стоимости обучения + проживание
📚 <b>Уровень:</b> Магистратура, PhD
🌍 <b>Направления:</b> Все специальности
📅 <b>Дедлайн:</b> 15.03.2026

<i>Это тестовый пост для проверки аналитики</i>

#образование #гранты #стипендии #германия"""

    try:
        # Send message to channel
        print(f"📡 Отправка поста в канал @eksperimentysayata...")

        message = await bot.send_message(
            chat_id=settings.CHANNEL_ID,
            text=content,
            parse_mode='HTML'
        )

        print(f"✅ Пост опубликован!")
        print(f"   Message ID: {message.message_id}")
        print(f"   Канал: {message.chat.title}")

        # Save to database
        async with get_session() as session:
            post_repo = PostRepository(session)
            digest_repo = DigestRepository(session)

            # Get or create a digest
            from sqlalchemy import text
            result = await session.execute(text("SELECT id FROM digests LIMIT 1"))
            digest_id = result.scalar()

            if not digest_id:
                print("\n⚠️  Создаю тестовый дайджест...")
                # Create a test digest
                from src.database.models import Digest
                digest = Digest(
                    content=content,
                    article_ids=[],
                    status='approved'
                )
                session.add(digest)
                await session.commit()
                await session.refresh(digest)
                digest_id = digest.id
                print(f"✅ Дайджест создан (ID: {digest_id})")

            # Create post record
            post = await post_repo.create_post(
                digest_id=digest_id,
                content=content,
                status='published'
            )

            # Update with channel info
            post.channel_id = settings.CHANNEL_ID
            post.message_id = message.message_id
            post.published_at = datetime.now()
            post.status = 'published'

            await session.commit()

            print(f"\n💾 Сохранено в БД:")
            print(f"   Post ID: {post.id}")
            print(f"   Channel ID: {post.channel_id}")
            print(f"   Message ID: {post.message_id}")

        print("\n" + "=" * 60)
        print("✅ ГОТОВО!")
        print("\n📊 Теперь можно:")
        print("   1. Подожди 1-2 минуты (чтобы набрались просмотры)")
        print("   2. Запусти: python update_stats.py --quick")
        print("   3. Проверь аналитику: /admin → 📊 Аналитика")

        print(f"\n💡 Или открой пост в Telegram:")
        print(f"   https://t.me/eksperimentysayata/{message.message_id}")

        return post.id

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(publish_test_post())
