"""Settings repository"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import Settings
from src.database.repositories.base import BaseRepository


class SettingsRepository(BaseRepository[Settings]):
    """Repository for bot settings with caching"""

    # Class-level cache
    _cache: Optional[Settings] = None
    _cache_time: Optional[datetime] = None
    _cache_ttl = timedelta(minutes=5)

    def __init__(self, session: AsyncSession):
        super().__init__(Settings, session)

    @classmethod
    def clear_cache(cls):
        """Clear settings cache"""
        cls._cache = None
        cls._cache_time = None

    async def get_settings(self, use_cache: bool = True) -> Settings:
        """
        Get bot settings (creates default if not exists)

        Args:
            use_cache: If True, use cached settings if available
        """
        # Check cache
        now = datetime.now()
        if use_cache and self._cache and self._cache_time:
            if (now - self._cache_time) < self._cache_ttl:
                return self._cache

        # Fetch from database
        result = await self.session.execute(
            select(Settings).limit(1)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            # Create default settings
            settings = Settings(
                education_sections=[
                    'higher_education',
                    'secondary_education',
                    'private_schools',
                    'online_education',
                    'courses_edtech',
                    'grants_scholarships',
                    'reforms',
                    'legislation',
                    'international'
                ],
                language='ru',
                post_length='short',
                publication_hour=9,
                publication_frequency=1
            )
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)

        # Update cache
        self.__class__._cache = settings
        self.__class__._cache_time = now

        return settings

    async def update_education_sections(self, sections: List[str]) -> Settings:
        """Update enabled education sections"""
        settings = await self.get_settings(use_cache=False)
        settings.education_sections = sections
        await self.session.commit()
        await self.session.refresh(settings)
        self.clear_cache()  # Clear cache after update
        return settings

    async def update_language(self, language: str) -> Settings:
        """Update content language"""
        settings = await self.get_settings(use_cache=False)
        settings.language = language
        await self.session.commit()
        await self.session.refresh(settings)
        self.clear_cache()  # Clear cache after update
        return settings

    async def update_post_length(self, length: str) -> Settings:
        """Update post length setting"""
        settings = await self.get_settings(use_cache=False)
        settings.post_length = length
        await self.session.commit()
        await self.session.refresh(settings)
        self.clear_cache()  # Clear cache after update
        return settings

    async def update_publication_schedule(self, hour: int, frequency: int) -> Settings:
        """Update publication schedule"""
        settings = await self.get_settings(use_cache=False)
        settings.publication_hour = hour
        settings.publication_frequency = frequency
        await self.session.commit()
        await self.session.refresh(settings)
        self.clear_cache()  # Clear cache after update
        return settings

    async def is_section_enabled(self, section: str) -> bool:
        """Check if education section is enabled"""
        settings = await self.get_settings()
        return section in (settings.education_sections or [])
