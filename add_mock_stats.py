"""Add mock statistics to test posts for demonstration"""
import asyncio
import random
from datetime import datetime
from sqlalchemy import text

from src.database.connection import get_session


async def add_mock_stats():
    """Add realistic mock statistics to all posts"""

    print("📊 Добавление mock-статистики для демонстрации\n")
    print("=" * 60)

    async with get_session() as session:
        # Get all published posts
        result = await session.execute(
            text("SELECT id FROM posts WHERE status='published' ORDER BY id")
        )
        post_ids = [row[0] for row in result.fetchall()]

        if not post_ids:
            print("❌ Нет опубликованных постов")
            return

        print(f"📝 Найдено {len(post_ids)} постов\n")

        for i, post_id in enumerate(post_ids):
            # Generate realistic mock data
            # Newer posts have more views
            base_views = 1200 - (i * 150)
            views = max(100, base_views + random.randint(-200, 200))
            reactions = max(10, (views // 50) + random.randint(-10, 20))
            forwards = max(5, (views // 100) + random.randint(-3, 10))

            await session.execute(
                text(f"""
                UPDATE posts
                SET views_count = {views},
                    reactions_count = {reactions},
                    forwards_count = {forwards},
                    last_stats_update = NOW()
                WHERE id = {post_id}
                """)
            )

            print(f"Post #{post_id}:")
            print(f"  👁️  Просмотры: {views:,}")
            print(f"  ❤️  Реакции: {reactions:,}")
            print(f"  🔄 Пересылки: {forwards:,}\n")

        await session.commit()

        print("=" * 60)
        print("✅ Mock-статистика добавлена!")
        print("\n🎯 Теперь:")
        print("   1. Открой Telegram: /admin")
        print("   2. Нажми: 📊 Аналитика")
        print("   3. Получи красивую диаграмму!")


if __name__ == "__main__":
    asyncio.run(add_mock_stats())
