"""Script to add news sources to the database"""
import asyncio
import sys
sys.path.insert(0, '.')

from src.database.connection import get_session
from src.database.models import Source
from loguru import logger


async def add_example_sources():
    """Add example news sources to database"""

    sources_to_add = [
        {
            'name': 'Example Education Portal',
            'url': 'https://example.com/news',
            'parser_class': 'ExampleParser',
            'is_active': False  # Set to False until you implement the parser
        },
        # Add more sources here
        # {
        #     'name': 'Bolashak Foundation',
        #     'url': 'https://bolashak.gov.kz/news',
        #     'parser_class': 'BolashakParser',
        #     'is_active': True
        # },
    ]

    try:
        async with get_session() as session:
            for source_data in sources_to_add:
                # Check if source already exists
                from sqlalchemy import select
                result = await session.execute(
                    select(Source).where(Source.url == source_data['url'])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    logger.info(f"Source {source_data['name']} already exists")
                    continue

                # Create new source
                source = Source(**source_data)
                session.add(source)
                logger.info(f"Added source: {source_data['name']}")

            await session.commit()
            logger.info("All sources added successfully")

    except Exception as e:
        logger.error(f"Error adding sources: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(add_example_sources())
