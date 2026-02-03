"""Script to add sources from Excel file to the database"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_session
from src.database.models import Source
from sqlalchemy import select


async def add_excel_sources():
    """Add all sources from Excel 'Контент план Grants 2023.xlsx' to the database"""

    # Sources from "Сайты для поиска" sheet
    sources_data = [
        {
            'name': 'ST-GR - Гранты и стипендии',
            'url': 'https://st-gr.com/?cat=4',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': 'SICA Grants - Social Innovation',
            'url': 'https://socialinnovationca.org/ru/grants-ru/sica-grants/',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': 'Grantist - База грантов',
            'url': 'https://grantist.com/',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': 'The Village KZ - Образование',
            'url': 'https://www.the-village-kz.com/village/city/education',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': 'Scholars4Dev - Стипендии',
            'url': 'https://www.scholars4dev.com/',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': 'Opportunities For Youth',
            'url': 'https://opportunitiesforyouth.org/',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': 'Great YOP - Образовательные возможности',
            'url': 'https://greatyop.com/fully-funded-scholarships-for-international-students/',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': 'Inform.kz - Новости образования',
            'url': 'https://www.inform.kz/',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': 'МОН РК - Министерство образования',
            'url': 'https://www.gov.kz/memleket/entities/sci?lang=ru',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': '24.kz - Новости Казахстана',
            'url': 'https://24.kz/ru',
            'parser_class': 'GenericParser',
            'is_active': True
        },
        {
            'name': 'Zakon.kz - Законодательство об образовании',
            'url': 'https://www.zakon.kz/',
            'parser_class': 'GenericParser',
            'is_active': True
        }
    ]

    async with get_session() as session:
        added_count = 0
        existing_count = 0
        skipped_count = 0

        print("📝 Добавление источников из Excel файла...\n")
        print("="*80)

        for source_data in sources_data:
            # Check if source already exists (by URL)
            result = await session.execute(
                select(Source).where(Source.url == source_data['url'])
            )
            existing_source = result.scalar_one_or_none()

            if existing_source:
                print(f"✓ Источник уже существует: {source_data['name']}")
                print(f"   {source_data['url']}")
                existing_count += 1
                continue

            # Check if similar source exists (by domain)
            try:
                from urllib.parse import urlparse
                domain = urlparse(source_data['url']).netloc

                result = await session.execute(select(Source))
                all_sources = result.scalars().all()

                similar = False
                for s in all_sources:
                    s_domain = urlparse(s.url).netloc
                    if domain in s_domain or s_domain in domain:
                        print(f"⚠️  Похожий источник уже есть: {s.name}")
                        print(f"   Существующий: {s.url}")
                        print(f"   Новый: {source_data['url']}")
                        skipped_count += 1
                        similar = True
                        break

                if similar:
                    continue

            except Exception as e:
                pass

            # Add new source
            source = Source(**source_data)
            session.add(source)
            print(f"+ Добавлен источник: {source_data['name']}")
            print(f"   {source_data['url']}")
            added_count += 1

        await session.commit()

        print(f"\n{'='*80}")
        print(f"📊 Итоги:")
        print(f"   ✅ Добавлено новых источников: {added_count}")
        print(f"   ✓  Уже существовало: {existing_count}")
        print(f"   ⚠️  Пропущено (похожие): {skipped_count}")
        print(f"   📚 Обработано всего: {added_count + existing_count + skipped_count}")
        print(f"{'='*80}\n")

        # Show all sources
        print(f"📋 Все источники в базе данных:")
        print("="*80)
        result = await session.execute(select(Source))
        all_sources = result.scalars().all()

        for i, source in enumerate(all_sources, 1):
            status = "✅" if source.is_active else "❌"
            print(f"{i:2d}. {status} {source.name}")
            print(f"     URL: {source.url}")
            print(f"     Парсер: {source.parser_class}")
            print()

        print(f"{'='*80}")
        print(f"📊 Всего источников в базе: {len(all_sources)}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("📝 Добавление источников из Excel 'Контент план Grants 2023.xlsx'")
    print("="*80 + "\n")

    asyncio.run(add_excel_sources())

    print("\n" + "="*80)
    print("✅ Готово!")
    print("="*80 + "\n")
