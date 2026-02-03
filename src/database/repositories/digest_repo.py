"""Digest repository"""
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Digest
from src.database.repositories.base import BaseRepository


class DigestRepository(BaseRepository[Digest]):
    """Repository for Digest model"""

    def __init__(self, session: AsyncSession):
        super().__init__(Digest, session)

    async def create_digest(
        self, content: str, article_ids: List[int], image_url: Optional[str] = None
    ) -> Digest:
        """Create new digest"""
        return await self.create(
            content=content,
            article_ids=article_ids,
            image_url=image_url,
            status='draft'
        )

    async def update_content(self, digest_id: int, new_content: str) -> None:
        """Update digest content"""
        await self.session.execute(
            update(Digest)
            .where(Digest.id == digest_id)
            .values(content=new_content)
        )
        await self.session.flush()

    async def update_status(self, digest_id: int, status: str) -> None:
        """Update digest status"""
        await self.session.execute(
            update(Digest)
            .where(Digest.id == digest_id)
            .values(status=status)
        )
        await self.session.flush()

    async def set_moderator_message(
        self, digest_id: int, message_id: int
    ) -> None:
        """Set moderator message ID"""
        await self.session.execute(
            update(Digest)
            .where(Digest.id == digest_id)
            .values(moderator_message_id=message_id)
        )
        await self.session.flush()

    async def get_by_status(self, status: str, limit: int = 50) -> List[Digest]:
        """Get digests by status"""
        result = await self.session.execute(
            select(Digest)
            .where(Digest.status == status)
            .order_by(Digest.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
