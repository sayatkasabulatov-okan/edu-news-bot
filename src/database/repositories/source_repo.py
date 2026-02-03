"""Source repository"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import Source
from src.database.repositories.base import BaseRepository


class SourceRepository(BaseRepository[Source]):
    """Repository for news sources"""

    def __init__(self, session: AsyncSession):
        super().__init__(Source, session)

    async def get_all(self) -> List[Source]:
        """Get all sources"""
        result = await self.session.execute(
            select(Source).order_by(Source.name)
        )
        return list(result.scalars().all())

    async def get_active_sources(self) -> List[Source]:
        """Get all active sources"""
        result = await self.session.execute(
            select(Source).where(Source.is_active == True).order_by(Source.name)
        )
        return list(result.scalars().all())

    async def toggle_active(self, source_id: int) -> Source:
        """Toggle source active status"""
        source = await self.get_by_id(source_id)
        if source:
            source.is_active = not source.is_active
            await self.session.commit()
            await self.session.refresh(source)
        return source

    async def set_active(self, source_id: int, is_active: bool) -> Source:
        """Set source active status"""
        source = await self.get_by_id(source_id)
        if source:
            source.is_active = is_active
            await self.session.commit()
            await self.session.refresh(source)
        return source
