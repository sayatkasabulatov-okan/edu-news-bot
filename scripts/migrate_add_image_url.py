"""Migration: Add image_url column to articles table"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_session
from sqlalchemy import text


async def migrate():
    """Add image_url column to articles table"""

    async with get_session() as session:
        try:
            # Check if column already exists
            check_query = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='articles' AND column_name='image_url';
            """)
            result = await session.execute(check_query)
            exists = result.fetchone()

            if exists:
                print("✓ Колонка image_url уже существует в таблице articles")
                return

            # Add image_url column
            add_column_query = text("""
                ALTER TABLE articles
                ADD COLUMN image_url TEXT;
            """)

            await session.execute(add_column_query)
            await session.commit()

            print("✅ Колонка image_url успешно добавлена в таблицу articles")

        except Exception as e:
            print(f"❌ Ошибка при добавлении колонки: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    print("Миграция: Добавление колонки image_url в таблицу articles...\n")
    asyncio.run(migrate())
    print("\nГотово!")
