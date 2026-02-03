"""Script to add news sources to the database"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_session
from src.database.models import Source
from sqlalchemy import select


async def add_sources():
    """Add all education news sources to the database"""

    sources_data = [
        {
            'name': 'Bolashak International Scholarship',
            'url': 'https://bolashak.gov.kz/ru/news/',
            'parser_class': 'BolashakParser',
            'is_active': True
        },
        {
            'name': 'Opportunities Circle',
            'url': 'https://www.opportunitiescircle.com/scholarships/',
            'parser_class': 'OpportunitiesCircleParser',
            'is_active': True
        },
        {
            'name': 'Opportunities Corners',
            'url': 'https://opportunitiescorners.com/category/internships/',
            'parser_class': 'OpportunitiesCornersParser',
            'is_active': True
        }
    ]

    async with get_session() as session:
        added_count = 0
        existing_count = 0

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
            added_count += 1

        await session.commit()

        print(f"\n{'='*60}")
        print(f"Итого:")
        print(f"  Добавлено новых источников: {added_count}")
        print(f"  Уже существовало: {existing_count}")
        print(f"  Всего источников: {added_count + existing_count}")
        print(f"{'='*60}")

        # Show all sources
        print(f"\nВсе источники в базе данных:")
        result = await session.execute(select(Source))
        all_sources = result.scalars().all()

        for i, source in enumerate(all_sources, 1):
            status = "✓ Активен" if source.is_active else "✗ Неактивен"
            print(f"{i}. {source.name}")
            print(f"   URL: {source.url}")
            print(f"   Парсер: {source.parser_class}")
            print(f"   Статус: {status}")
            print()


if __name__ == "__main__":
    print("Добавление источников новостей в базу данных...\n")
    asyncio.run(add_sources())
    print("Готово!")
