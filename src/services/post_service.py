"""Business logic for post publishing"""
from datetime import datetime
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot

from src.database.repositories.post_repo import PostRepository
from src.database.repositories.digest_repo import DigestRepository
from src.config import settings
from src.utils.image_helpers import prepare_photo


class PostService:
    """Service for publishing and scheduling posts"""

    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.post_repo = PostRepository(session)
        self.digest_repo = DigestRepository(session)
        self.channel_id = settings.CHANNEL_ID

    async def publish_now(self, digest_id: int) -> bool:
        """
        Publish digest immediately to channel

        Args:
            digest_id: ID of the digest to publish

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Get digest
            digest = await self.digest_repo.get_by_id(digest_id)
            if not digest:
                logger.error(f"Digest {digest_id} not found")
                return False

            # Publish to channel
            logger.info(f"Publishing digest {digest_id} to channel {self.channel_id}")

            # Send with image if available
            if digest.image_url:
                logger.info(f"Sending digest with image: {digest.image_url}")

                # Check if caption is too long (Telegram limit is 1024 chars)
                if len(digest.content) > 1024:
                    # Send image and text separately
                    await self.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=prepare_photo(digest.image_url)
                    )
                    message = await self.bot.send_message(
                        chat_id=self.channel_id,
                        text=digest.content,
                        parse_mode='HTML'
                    )
                else:
                    # Send image with caption
                    message = await self.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=prepare_photo(digest.image_url),
                        caption=digest.content,
                        parse_mode='HTML'
                    )
            else:
                message = await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=digest.content,
                    parse_mode='HTML'
                )

            # Create or update post record
            existing_post = await self.post_repo.get_by_digest(digest_id)

            if existing_post:
                await self.post_repo.mark_published(
                    post_id=existing_post.id,
                    channel_id=self.channel_id,
                    message_id=message.message_id
                )
            else:
                await self.post_repo.create_post(
                    digest_id=digest_id,
                    content=digest.content,
                    status='published'
                )
                await self.post_repo.mark_published(
                    post_id=(await self.post_repo.get_by_digest(digest_id)).id,
                    channel_id=self.channel_id,
                    message_id=message.message_id
                )

            # Update digest status
            await self.digest_repo.update_status(digest_id, 'published')

            await self.session.commit()

            logger.info(f"Digest {digest_id} published successfully. Message ID: {message.message_id}")

            return True

        except Exception as e:
            logger.error(f"Error publishing digest {digest_id}: {e}")

            # Try to record error
            try:
                existing_post = await self.post_repo.get_by_digest(digest_id)
                if existing_post:
                    await self.post_repo.update_error(existing_post.id, str(e))
            except:
                pass

            await self.session.rollback()
            return False

    async def schedule_post(
        self, digest_id: int, scheduled_at: datetime
    ) -> bool:
        """
        Schedule post for future publishing

        Args:
            digest_id: ID of the digest to schedule
            scheduled_at: When to publish

        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            # Get digest
            digest = await self.digest_repo.get_by_id(digest_id)
            if not digest:
                logger.error(f"Digest {digest_id} not found")
                return False

            # Check if already has a post
            existing_post = await self.post_repo.get_by_digest(digest_id)

            if existing_post:
                # Update existing post
                await self.post_repo.update_status(existing_post.id, 'scheduled')
                from sqlalchemy import update
                from src.database.models import Post
                await self.session.execute(
                    update(Post)
                    .where(Post.id == existing_post.id)
                    .values(scheduled_at=scheduled_at)
                )
            else:
                # Create new post
                await self.post_repo.create_post(
                    digest_id=digest_id,
                    content=digest.content,
                    status='scheduled',
                    scheduled_at=scheduled_at
                )

            # Update digest status
            await self.digest_repo.update_status(digest_id, 'scheduled')

            await self.session.commit()

            logger.info(f"Digest {digest_id} scheduled for {scheduled_at}")

            return True

        except Exception as e:
            logger.error(f"Error scheduling digest {digest_id}: {e}")
            await self.session.rollback()
            return False

    async def publish_scheduled_posts(self) -> int:
        """
        Publish all posts that are scheduled for now or earlier
        Handles both digest posts and individual article posts

        Returns:
            Number of posts published
        """
        try:
            # Get scheduled posts
            scheduled_posts = await self.post_repo.get_scheduled_posts()

            if not scheduled_posts:
                return 0

            published_count = 0

            for post in scheduled_posts:
                try:
                    # Check if this is a digest post or individual article post
                    if post.digest_id:
                        # Handle digest post
                        digest = await self.digest_repo.get_by_id(post.digest_id)
                        if not digest:
                            continue

                        # Get image from digest
                        image_url = digest.image_url

                        # Publish to channel with digest image
                        if image_url:
                            if len(post.content) > 1024:
                                await self.bot.send_photo(
                                    chat_id=self.channel_id,
                                    photo=prepare_photo(image_url)
                                )
                                message = await self.bot.send_message(
                                    chat_id=self.channel_id,
                                    text=post.content,
                                    parse_mode='HTML'
                                )
                            else:
                                message = await self.bot.send_photo(
                                    chat_id=self.channel_id,
                                    photo=prepare_photo(image_url),
                                    caption=post.content,
                                    parse_mode='HTML'
                                )
                        else:
                            message = await self.bot.send_message(
                                chat_id=self.channel_id,
                                text=post.content,
                                parse_mode='HTML'
                            )

                        # Update digest status
                        await self.digest_repo.update_status(digest.id, 'published')

                    elif post.article_id:
                        # Handle individual article post
                        from sqlalchemy import select
                        from sqlalchemy.orm import joinedload
                        from src.database.models import Post, Article

                        result = await self.session.execute(
                            select(Post)
                            .options(joinedload(Post.article))
                            .where(Post.id == post.id)
                        )
                        post_with_article = result.scalar_one_or_none()

                        if not post_with_article or not post_with_article.article:
                            continue

                        # Get image from article
                        image_url = post_with_article.article.image_url if post_with_article.article else None

                        # Publish to channel with article image
                        if image_url:
                            if len(post.content) > 1024:
                                await self.bot.send_photo(
                                    chat_id=self.channel_id,
                                    photo=prepare_photo(image_url)
                                )
                                message = await self.bot.send_message(
                                    chat_id=self.channel_id,
                                    text=post.content,
                                    parse_mode='HTML',
                                    disable_web_page_preview=True
                                )
                            else:
                                message = await self.bot.send_photo(
                                    chat_id=self.channel_id,
                                    photo=prepare_photo(image_url),
                                    caption=post.content,
                                    parse_mode='HTML'
                                )
                        else:
                            message = await self.bot.send_message(
                                chat_id=self.channel_id,
                                text=post.content,
                                parse_mode='HTML',
                                disable_web_page_preview=True
                            )

                        # Mark article as processed
                        from sqlalchemy import update
                        await self.session.execute(
                            update(Article)
                            .where(Article.id == post.article_id)
                            .values(is_processed=True)
                        )

                    else:
                        # Post has neither digest_id nor article_id
                        logger.warning(f"Post {post.id} has no digest_id or article_id")
                        continue

                    # Update post
                    await self.post_repo.mark_published(
                        post_id=post.id,
                        channel_id=self.channel_id,
                        message_id=message.message_id
                    )

                    published_count += 1

                    logger.info(f"Scheduled post {post.id} published successfully")

                except Exception as e:
                    logger.error(f"Error publishing scheduled post {post.id}: {e}")
                    await self.post_repo.update_error(post.id, str(e))

            await self.session.commit()

            logger.info(f"Published {published_count} scheduled posts")

            return published_count

        except Exception as e:
            logger.error(f"Error publishing scheduled posts: {e}")
            await self.session.rollback()
            return 0

    async def schedule_individual_post(
        self, post_id: int, scheduled_at: datetime
    ) -> bool:
        """
        Schedule individual post for future publishing

        Args:
            post_id: ID of the post to schedule
            scheduled_at: When to publish

        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            # Get post
            from sqlalchemy import select
            from src.database.models import Post

            result = await self.session.execute(
                select(Post).where(Post.id == post_id)
            )
            post = result.scalar_one_or_none()

            if not post:
                logger.error(f"Post {post_id} not found")
                return False

            # Update post status and scheduled time
            from sqlalchemy import update
            await self.session.execute(
                update(Post)
                .where(Post.id == post_id)
                .values(
                    status='scheduled',
                    scheduled_at=scheduled_at
                )
            )

            await self.session.commit()

            logger.info(f"Post {post_id} scheduled for {scheduled_at}")

            return True

        except Exception as e:
            logger.error(f"Error scheduling post {post_id}: {e}")
            await self.session.rollback()
            return False

    async def publish_post(self, post_id: int) -> bool:
        """
        Publish individual post immediately to channel

        Args:
            post_id: ID of the post to publish

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Get post with relationships
            from sqlalchemy import select
            from sqlalchemy.orm import joinedload
            from src.database.models import Post, Article

            result = await self.session.execute(
                select(Post)
                .options(joinedload(Post.article))
                .where(Post.id == post_id)
            )
            post = result.scalar_one_or_none()

            if not post:
                logger.error(f"Post {post_id} not found")
                return False

            # Publish to channel
            logger.info(f"Publishing post {post_id} to channel {self.channel_id}")

            # Get image from article if available
            image_url = None
            if post.article_id and post.article and post.article.image_url:
                image_url = post.article.image_url
                logger.info(f"Using image from article: {image_url}")

            # Send with image if available
            if image_url:
                # Check if caption is too long (Telegram limit is 1024 chars)
                if len(post.content) > 1024:
                    # Send image and text separately
                    await self.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=prepare_photo(image_url)
                    )
                    message = await self.bot.send_message(
                        chat_id=self.channel_id,
                        text=post.content,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                else:
                    # Send image with caption
                    message = await self.bot.send_photo(
                        chat_id=self.channel_id,
                        photo=prepare_photo(image_url),
                        caption=post.content,
                        parse_mode='HTML'
                    )
            else:
                message = await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=post.content,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )

            # Mark post as published
            await self.post_repo.mark_published(
                post_id=post_id,
                channel_id=self.channel_id,
                message_id=message.message_id
            )

            # Mark article as processed if this is an article post
            if post.article_id:
                from sqlalchemy import update
                await self.session.execute(
                    update(Article)
                    .where(Article.id == post.article_id)
                    .values(is_processed=True)
                )

            await self.session.commit()

            logger.info(f"Post {post_id} published successfully. Message ID: {message.message_id}")

            return True

        except Exception as e:
            logger.error(f"Error publishing post {post_id}: {e}")

            # Try to record error
            try:
                await self.post_repo.update_error(post_id, str(e))
                await self.session.commit()
            except:
                pass

            await self.session.rollback()
            return False
