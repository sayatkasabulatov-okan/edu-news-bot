"""Post repository"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Post
from src.database.repositories.base import BaseRepository


class PostRepository(BaseRepository[Post]):
    """Repository for Post model"""

    def __init__(self, session: AsyncSession):
        super().__init__(Post, session)

    async def create_post(
        self,
        digest_id: int,
        content: str,
        status: str = 'draft',
        scheduled_at: Optional[datetime] = None
    ) -> Post:
        """Create new post"""
        return await self.create(
            digest_id=digest_id,
            content=content,
            status=status,
            scheduled_at=scheduled_at
        )

    async def update_status(self, post_id: int, status: str) -> None:
        """Update post status"""
        await self.session.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(status=status)
        )
        await self.session.flush()

    async def mark_published(
        self,
        post_id: int,
        channel_id: int,
        message_id: int
    ) -> None:
        """Mark post as published"""
        await self.session.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(
                status='published',
                published_at=datetime.now(),
                channel_id=channel_id,
                message_id=message_id
            )
        )
        await self.session.flush()

    async def update_error(self, post_id: int, error_message: str) -> None:
        """Update post with error message"""
        await self.session.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(
                status='failed',
                error_message=error_message
            )
        )
        await self.session.flush()

    async def get_scheduled_posts(self) -> List[Post]:
        """Get posts scheduled for publishing"""
        result = await self.session.execute(
            select(Post)
            .where(Post.status == 'scheduled')
            .where(Post.scheduled_at <= datetime.now())
            .order_by(Post.scheduled_at)
        )
        return list(result.scalars().all())

    async def get_by_digest(self, digest_id: int) -> Optional[Post]:
        """Get post by digest ID"""
        result = await self.session.execute(
            select(Post).where(Post.digest_id == digest_id)
        )
        return result.scalar_one_or_none()

    async def get_published_posts(self, limit: int = 10) -> List[Post]:
        """Get published posts ordered by publication date"""
        result = await self.session.execute(
            select(Post)
            .where(Post.status == 'published')
            .order_by(Post.published_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_content(self, post_id: int, content: str) -> None:
        """Update post content"""
        await self.session.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(content=content)
        )
        await self.session.flush()
