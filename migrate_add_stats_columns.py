"""Add statistics columns to posts table"""
import asyncio
from sqlalchemy import text

from src.database.connection import engine


async def migrate():
    """Add statistics columns to posts table"""

    print("🔄 Добавление колонок статистики в таблицу posts\n")
    print("=" * 60)

    migrations = [
        """
        ALTER TABLE posts
        ADD COLUMN IF NOT EXISTS views_count INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE posts
        ADD COLUMN IF NOT EXISTS reactions_count INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE posts
        ADD COLUMN IF NOT EXISTS forwards_count INTEGER DEFAULT 0;
        """,
        """
        ALTER TABLE posts
        ADD COLUMN IF NOT EXISTS last_stats_update TIMESTAMP;
        """,
    ]

    async with engine.begin() as conn:
        for i, migration in enumerate(migrations, 1):
            print(f"\n{i}. Выполнение миграции...")
            try:
                await conn.execute(text(migration))
                print(f"   ✅ Готово")
            except Exception as e:
                print(f"   ⚠️  {e}")

    print("\n" + "=" * 60)
    print("✅ Миграция завершена!")
    print("\n📊 Добавлены колонки:")
    print("   • views_count (просмотры)")
    print("   • reactions_count (реакции)")
    print("   • forwards_count (пересылки)")
    print("   • last_stats_update (время обновления)")

    print("\n🎯 Теперь можно:")
    print("   1. Опубликовать пост: python publish_test_post.py")
    print("   2. Обновить статистику: python update_stats.py")
    print("   3. Посмотреть аналитику: /admin → 📊 Аналитика")


if __name__ == "__main__":
    asyncio.run(migrate())
