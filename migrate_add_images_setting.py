"""Add images_enabled column to settings table"""
import asyncio
from sqlalchemy import text

from src.database.connection import engine


async def migrate():
    """Add images_enabled setting"""

    print("🔄 Добавление настройки изображений в таблицу settings\n")
    print("=" * 60)

    migration = """
    ALTER TABLE settings
    ADD COLUMN IF NOT EXISTS images_enabled BOOLEAN DEFAULT TRUE;
    """

    async with engine.begin() as conn:
        print("\nВыполнение миграции...")
        try:
            await conn.execute(text(migration))
            print("   ✅ Готово")
        except Exception as e:
            print(f"   ⚠️  {e}")

    print("\n" + "=" * 60)
    print("✅ Миграция завершена!")
    print("\n📊 Добавлено поле:")
    print("   • images_enabled (включение/выключение изображений)")

    print("\n🎯 Теперь можно:")
    print("   1. Зайти в /admin → 🖼️ Изображения")
    print("   2. Включить или выключить генерацию изображений")


if __name__ == "__main__":
    asyncio.run(migrate())
