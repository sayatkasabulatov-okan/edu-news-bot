"""Update statistics for published posts from Telegram"""
import asyncio
from telegram import Bot

from src.config import settings
from src.database.connection import get_session
from src.database.repositories.post_repo import PostRepository
from src.services.telegram_stats_service import TelegramStatsService


async def update_all_stats():
    """Update statistics for all published posts"""

    print("📊 Обновление статистики постов из Telegram\n")
    print("=" * 60)

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    stats_service = TelegramStatsService(bot)

    async with get_session() as session:
        post_repo = PostRepository(session)

        # Get all published posts
        posts = await post_repo.get_published_posts(limit=50)

        if not posts:
            print("❌ Нет опубликованных постов для обновления")
            return

        print(f"📝 Найдено {len(posts)} опубликованных постов\n")

        # Filter posts that have channel/message info
        posts_with_info = [
            p for p in posts
            if p.channel_id and p.message_id
        ]

        if not posts_with_info:
            print("⚠️  Ни у одного поста нет информации о канале/сообщении")
            print("   Посты должны быть опубликованы через бота для получения статистики")
            return

        print(f"🔄 Обновляю статистику для {len(posts_with_info)} постов...\n")

        # Update stats
        results = await stats_service.bulk_update_statistics(posts_with_info)

        # Save to database
        await session.commit()

        print("\n" + "=" * 60)
        print("📈 РЕЗУЛЬТАТЫ:")
        print(f"   Всего постов: {results['total']}")
        print(f"   ✅ Обновлено: {results['updated']}")
        print(f"   ❌ Ошибок: {results['failed']}")

        if results['updated'] > 0:
            print("\n📊 Обновленная статистика:")
            print("-" * 60)

            for post in posts_with_info[:10]:  # Show first 10
                if post.last_stats_update:
                    print(f"\nПост #{post.id}:")
                    print(f"  👁️  Просмотры: {post.views_count:,}")
                    print(f"  ❤️  Реакции: {post.reactions_count:,}")
                    print(f"  🔄 Пересылки: {post.forwards_count:,}")
                    print(f"  📅 Обновлено: {post.last_stats_update.strftime('%d.%m.%Y %H:%M')}")

        print("\n" + "=" * 60)
        print("✅ Готово!")

        # Get channel info
        if settings.CHANNEL_ID:
            print("\n📢 Информация о канале:")
            channel_info = await stats_service.get_channel_info(settings.CHANNEL_ID)

            if channel_info:
                print(f"   Название: {channel_info.get('title', 'N/A')}")
                print(f"   Username: @{channel_info.get('username', 'N/A')}")
                print(f"   Подписчиков: {channel_info.get('member_count', 'N/A'):,}")
                print(f"   Тип: {channel_info.get('type', 'N/A')}")


async def update_recent_stats():
    """Update statistics for last 5 posts only"""

    print("📊 Быстрое обновление (последние 5 постов)\n")

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    stats_service = TelegramStatsService(bot)

    async with get_session() as session:
        post_repo = PostRepository(session)

        # Get last 5 published posts
        posts = await post_repo.get_published_posts(limit=5)

        if not posts:
            print("❌ Нет опубликованных постов")
            return

        posts_with_info = [p for p in posts if p.channel_id and p.message_id]

        if not posts_with_info:
            print("⚠️  У постов нет информации о канале")
            return

        print(f"🔄 Обновляю {len(posts_with_info)} постов...\n")

        results = await stats_service.bulk_update_statistics(posts_with_info)
        await session.commit()

        print(f"✅ Обновлено: {results['updated']}")
        print(f"❌ Ошибок: {results['failed']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(update_recent_stats())
    else:
        asyncio.run(update_all_stats())
