"""Script to add new sources from Google Spreadsheet and TZ"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_session
from src.database.models import Source
from sqlalchemy import select


async def add_new_sources():
    """Add new education sources from TZ and Google Spreadsheet"""

    sources_data = [
        {
            'name': 'Bright Scholarship',
            'url': 'https://brightscholarship.com/',
            'parser_class': 'BrightScholarshipParser',
            'is_active': True
        },
        {
            'name': 'Global Scholarships (Kazakhstan)',
            'url': 'https://globalscholarships.com/scholarship-search/nationality-kazakhstan/',
            'parser_class': 'GlobalScholarshipsParser',
            'is_active': True
        },
        {
            'name': 'SPUBL.kz - Scientific Publications',
            'url': 'https://spubl.kz/ru/blog/',
            'parser_class': 'SpublParser',
            'is_active': True
        }
    ]

    async with get_session() as session:
        added_count = 0
        existing_count = 0

        print("📚 Добавление новых источников из Google Spreadsheet и ТЗ\n")
        print("=" * 60)

        for source_data in sources_data:
            # Check if source already exists
            result = await session.execute(
                select(Source).where(Source.url == source_data['url'])
            )
            existing_source = result.scalar_one_or_none()

            if existing_source:
                print(f"✓ Источник уже существует: {source_data['name']}")
                existing_count += 1
                continue

            # Add new source
            source = Source(**source_data)
            session.add(source)
            print(f"+ Добавлен источник: {source_data['name']}")
            print(f"  URL: {source_data['url']}")
            print(f"  Парсер: {source_data['parser_class']}")
            added_count += 1

        await session.commit()

        print(f"\n{'='*60}")
        print(f"Итого:")
        print(f"  ✅ Добавлено новых источников: {added_count}")
        print(f"  ℹ️  Уже существовало: {existing_count}")
        print(f"  📊 Всего обработано: {added_count + existing_count}")
        print(f"{'='*60}")

        # Show all sources
        print(f"\n📋 Все источники в базе данных:")
        print(f"{'='*60}\n")
        result = await session.execute(select(Source))
        all_sources = result.scalars().all()

        for i, source in enumerate(all_sources, 1):
            status = "✅ Активен" if source.is_active else "❌ Неактивен"
            print(f"{i}. {source.name}")
            print(f"   URL: {source.url}")
            print(f"   Парсер: {source.parser_class}")
            print(f"   Статус: {status}")
            print()

        print(f"{'='*60}")
        print(f"\n🎯 Следующие шаги:")
        print(f"   1. Запусти ресерч: /admin → 🔍 Запустить ресерч")
        print(f"   2. Или в коде: python src/scraper/run_scraper.py")
        print(f"   3. Проверь статьи: SELECT * FROM articles")


if __name__ == "__main__":
    asyncio.run(add_new_sources())
    print("\n✅ Готово!")
