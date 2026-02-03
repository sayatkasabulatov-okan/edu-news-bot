"""Business logic for processing individual articles into posts"""
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from telegram import Bot

from src.database.models import Article, Post, Source
from src.database.repositories.article_repo import ArticleRepository
from src.ai.summarizer import ContentSummarizer
from src.services.image_generation_service import ImageGenerationService
from src.bot.keyboards.post_actions import get_post_actions_keyboard
from src.config import settings


class ArticlePostService:
    """Service for creating posts from individual articles"""

    def __init__(self, session: AsyncSession, bot: Optional[Bot] = None):
        """
        Initialize ArticlePostService

        Args:
            session: Database session
            bot: Telegram bot instance (optional, needed for sending notifications)
        """
        self.session = session
        self.bot = bot
        self.article_repo = ArticleRepository(session)
        self.summarizer = ContentSummarizer()
        self.image_service = ImageGenerationService()

    async def process_article(self, article: Article) -> Optional[Post]:
        """
        Process a single article into a post

        Steps:
        1. Check if article was already processed
        2. Create brief summary (max 5 sentences)
        3. Generate image if needed
        4. Create Post with article_id
        5. Send to moderator

        Args:
            article: Article object to process

        Returns:
            Post object if successful, None otherwise
        """
        try:
            # Check if already processed
            if await self.has_article_been_processed(article.id):
                logger.debug(f"Article {article.id} already processed, skipping")
                return None

            # Create summary
            logger.info(f"Processing article: {article.title[:60]}...")
            summary = await self.create_summary_for_article(article)

            if not summary:
                logger.warning(f"Failed to create summary for article {article.id}")
                return None

            # Generate or get image
            image_url = await self._get_article_image(article)

            # Create post
            post = Post(
                article_id=article.id,
                content=summary,
                status='sent_to_moderator'
            )
            self.session.add(post)
            await self.session.flush()  # Get post ID

            # Send to moderator
            if self.bot:
                await self.notify_moderator_about_post(post, article)
            else:
                logger.warning("Bot instance not provided, cannot send to moderator")

            await self.session.commit()

            logger.info(f"✅ Article {article.id} processed successfully as post {post.id}")
            return post

        except Exception as e:
            logger.error(f"Error processing article {article.id}: {e}")
            await self.session.rollback()
            return None

    async def create_summary_for_article(self, article: Article) -> Optional[str]:
        """
        Create a brief summary (max 5 sentences) from article

        Args:
            article: Article object

        Returns:
            Summary text or None if failed
        """
        try:
            summary = await self.summarizer.summarize_single_article(
                article_title=article.title,
                article_content=article.content or '',
                article_url=article.url
            )

            return summary

        except Exception as e:
            logger.error(f"Error creating summary for article {article.id}: {e}")
            return None

    async def notify_moderator_about_post(self, post: Post, article: Article):
        """
        Send post to moderator with action buttons

        Args:
            post: Post object
            article: Article object
        """
        if not self.bot:
            logger.error("Bot instance not available for sending notification")
            return

        try:
            # Get source info
            result = await self.session.execute(
                select(Source).where(Source.id == article.source_id)
            )
            source = result.scalar_one_or_none()
            source_name = source.name if source else "Неизвестный источник"

            # Build header
            header = f"""📄 <b>Новая статья от {source_name}</b>
🕐 {article.published_at.strftime('%d.%m.%Y %H:%M') if article.published_at else 'Дата неизвестна'}
━━━━━━━━━━━━━━━━━━━━━━

"""

            # Build footer with article link
            footer = f"""

━━━━━━━━━━━━━━━━━━━━━━
<a href="{article.url}">🔗 Читать оригинал</a>

<i>💡 Используй кнопки ниже для управления публикацией</i>
"""

            full_message = header + post.content + footer

            # Get keyboard
            keyboard = get_post_actions_keyboard(post.id, has_digest=False)

            # Send message
            message = await self.bot.send_message(
                chat_id=settings.MODERATOR_CHAT_ID,
                text=full_message,
                reply_markup=keyboard,
                parse_mode='HTML',
                disable_web_page_preview=True
            )

            logger.info(f"Post {post.id} sent to moderator (message_id: {message.message_id})")

        except Exception as e:
            logger.error(f"Error sending post {post.id} to moderator: {e}")

    async def has_article_been_processed(self, article_id: int) -> bool:
        """
        Check if article was already processed into a post

        An article is considered processed if there's a Post with article_id
        in status: 'sent_to_moderator', 'approved', 'scheduled', or 'published'

        Args:
            article_id: Article ID to check

        Returns:
            True if article was processed, False otherwise
        """
        try:
            result = await self.session.execute(
                select(Post)
                .where(Post.article_id == article_id)
                .where(Post.status.in_([
                    'sent_to_moderator',
                    'approved',
                    'scheduled',
                    'published'
                ]))
            )
            post = result.scalar_one_or_none()
            return post is not None

        except Exception as e:
            logger.error(f"Error checking if article {article_id} was processed: {e}")
            return False

    async def _get_article_image(self, article: Article) -> Optional[str]:
        """
        Get image for article: either from article or generate new one

        Args:
            article: Article object

        Returns:
            Image URL or None
        """
        # Check settings
        from src.database.repositories.settings_repo import SettingsRepository
        settings_repo = SettingsRepository(self.session)
        settings_obj = await settings_repo.get_settings()

        if not settings_obj.images_enabled:
            logger.debug("Images disabled in settings")
            return None

        # Use existing image if available
        if article.image_url:
            logger.info(f"Using existing image from article")
            return article.image_url

        # Generate new image using DALL-E
        logger.info("No image in article, generating with DALL-E")
        try:
            image_url = await self.image_service.generate_image(
                article.title,
                article.content or ""
            )

            if image_url:
                logger.info(f"Generated image: {image_url}")
                return image_url
            else:
                logger.warning("Failed to generate image with DALL-E")
                return None

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
