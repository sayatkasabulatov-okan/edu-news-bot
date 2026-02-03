"""Business logic for digest management"""
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repositories.article_repo import ArticleRepository
from src.database.repositories.digest_repo import DigestRepository
from src.ai.summarizer import ContentSummarizer
from src.services.image_generation_service import ImageGenerationService
from src.config import settings


class DigestService:
    """Service for managing digests"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.article_repo = ArticleRepository(session)
        self.digest_repo = DigestRepository(session)
        self.summarizer = ContentSummarizer()
        self.image_service = ImageGenerationService()

    async def create_digest_if_ready(self) -> Optional[int]:
        """
        Create digest from unprocessed articles if enough are available

        Returns:
            Digest ID if created, None otherwise
        """
        # Get unprocessed articles
        articles = await self.article_repo.get_unprocessed(
            limit=settings.MAX_ARTICLES_FOR_DIGEST
        )

        if len(articles) < settings.MIN_ARTICLES_FOR_DIGEST:
            logger.info(
                f"Not enough articles for digest. "
                f"Found {len(articles)}, need {settings.MIN_ARTICLES_FOR_DIGEST}"
            )
            return None

        try:
            # Prepare articles for AI
            articles_data = [
                {
                    'title': article.title,
                    'content': article.content or '',
                }
                for article in articles
            ]

            # Create digest using AI
            logger.info(f"Creating digest from {len(articles)} articles")
            digest_content = await self.summarizer.create_digest(articles_data)

            # Select or generate image for digest (if enabled in settings)
            image_url = None
            from src.database.repositories.settings_repo import SettingsRepository
            settings_repo = SettingsRepository(self.session)
            settings = await settings_repo.get_settings()

            if settings.images_enabled:
                image_url = await self._get_digest_image(articles)
            else:
                logger.info("Images disabled in settings, skipping image generation")

            # Save digest to database
            article_ids = [article.id for article in articles]
            digest = await self.digest_repo.create_digest(
                content=digest_content,
                article_ids=article_ids,
                image_url=image_url
            )

            # Mark articles as processed
            await self.article_repo.mark_as_processed(article_ids)

            await self.session.commit()

            logger.info(f"Digest {digest.id} created successfully")

            return digest.id

        except Exception as e:
            logger.error(f"Error creating digest: {e}")
            await self.session.rollback()
            raise

    async def update_digest_content(
        self, digest_id: int, new_content: str
    ) -> None:
        """
        Update digest content after manual editing

        Args:
            digest_id: ID of the digest
            new_content: New content text
        """
        try:
            await self.digest_repo.update_content(digest_id, new_content)
            await self.session.commit()

            logger.info(f"Digest {digest_id} content updated")

        except Exception as e:
            logger.error(f"Error updating digest {digest_id}: {e}")
            await self.session.rollback()
            raise

    async def get_digest(self, digest_id: int):
        """Get digest by ID"""
        return await self.digest_repo.get_by_id(digest_id)

    async def _get_digest_image(self, articles) -> Optional[str]:
        """
        Get image for digest: either from articles or generate new one

        Args:
            articles: List of Article objects

        Returns:
            Image URL or None
        """
        # Try to find image from articles
        for article in articles:
            if hasattr(article, 'image_url') and article.image_url:
                logger.info(f"Using image from article: {article.title[:50]}...")
                return article.image_url

        # No images in articles - generate one using DALL-E
        logger.info("No images in articles, generating with DALL-E")

        # Use first article for prompt
        if articles and len(articles) > 0:
            first_article = articles[0]
            title = first_article.title
            content = first_article.content or ""

            # Generate image
            image_url = await self.image_service.generate_image(title, content)

            if image_url:
                logger.info(f"Generated image: {image_url}")
                return image_url
            else:
                logger.warning("Failed to generate image with DALL-E")
                return None

        return None
