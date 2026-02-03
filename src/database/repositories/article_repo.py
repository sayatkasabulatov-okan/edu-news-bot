"""Article repository"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Article
from src.database.repositories.base import BaseRepository


class ArticleRepository(BaseRepository[Article]):
    """Repository for Article model"""

    def __init__(self, session: AsyncSession):
        super().__init__(Article, session)

    async def get_unprocessed(self, limit: int = 6) -> List[Article]:
        """Get unprocessed articles"""
        result = await self.session.execute(
            select(Article)
            .where(Article.is_processed == False)
            .order_by(Article.scraped_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_as_processed(self, article_ids: List[int]) -> None:
        """Mark articles as processed"""
        await self.session.execute(
            update(Article)
            .where(Article.id.in_(article_ids))
            .values(is_processed=True)
        )
        await self.session.flush()

    async def get_by_url(self, url: str) -> Optional[Article]:
        """Get article by URL"""
        result = await self.session.execute(
            select(Article).where(Article.url == url)
        )
        return result.scalar_one_or_none()

    async def get_by_source(self, source_id: int, limit: int = 50) -> List[Article]:
        """Get articles by source ID"""
        result = await self.session.execute(
            select(Article)
            .where(Article.source_id == source_id)
            .order_by(Article.scraped_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Article:
        """Create new article, handling timezone-aware datetimes"""
        # Convert timezone-aware datetime to naive datetime
        if 'published_at' in kwargs and kwargs['published_at'] is not None:
            published_at = kwargs['published_at']
            if isinstance(published_at, datetime) and published_at.tzinfo is not None:
                # Remove timezone info (convert to naive datetime)
                kwargs['published_at'] = published_at.replace(tzinfo=None)

        # Call parent create method
        return await super().create(**kwargs)
