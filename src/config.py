"""Application configuration using Pydantic Settings"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = Field(..., env='TELEGRAM_BOT_TOKEN')
    MODERATOR_CHAT_IDS: str = Field(..., env='MODERATOR_CHAT_IDS')
    CHANNEL_ID: int = Field(..., env='CHANNEL_ID')

    @property
    def moderator_ids(self) -> List[int]:
        """Parse comma-separated moderator IDs into a list"""
        return [int(x.strip()) for x in self.MODERATOR_CHAT_IDS.split(',') if x.strip()]

    def is_moderator(self, user_id: int) -> bool:
        """Check if user is a moderator"""
        return user_id in self.moderator_ids

    @property
    def MODERATOR_CHAT_ID(self) -> int:
        """Backward compatibility: return first moderator ID"""
        return self.moderator_ids[0]

    # Database Configuration
    DATABASE_URL: Optional[str] = Field(default=None, env='DATABASE_URL')
    DB_HOST: str = Field(default='localhost', env='DB_HOST')
    DB_PORT: int = Field(default=5432, env='DB_PORT')
    DB_NAME: str = Field(default='edu_news_bot', env='DB_NAME')
    DB_USER: str = Field(default='postgres', env='DB_USER')
    DB_PASSWORD: str = Field(default='postgres', env='DB_PASSWORD')

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL. Supports Railway's DATABASE_URL."""
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            # Railway gives postgresql:// but asyncpg needs postgresql+asyncpg://
            if url.startswith('postgresql://'):
                url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
            elif url.startswith('postgres://'):
                url = url.replace('postgres://', 'postgresql+asyncpg://', 1)
            return url
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(..., env='OPENAI_API_KEY')
    OPENAI_MODEL: str = Field(default='gpt-4-turbo-preview', env='OPENAI_MODEL')

    # Scraping Configuration
    SCRAPING_SCHEDULE_HOUR: int = Field(default=9, env='SCRAPING_SCHEDULE_HOUR')
    MIN_ARTICLES_FOR_DIGEST: int = Field(default=5, env='MIN_ARTICLES_FOR_DIGEST')
    MAX_ARTICLES_FOR_DIGEST: int = Field(default=6, env='MAX_ARTICLES_FOR_DIGEST')

    # Article Mode Configuration (NEW)
    SCRAPING_INTERVAL_HOURS: int = Field(default=4, env='SCRAPING_INTERVAL_HOURS')
    SCRAPING_HOURS: str = Field(default='9,14,18', env='SCRAPING_HOURS')
    TIMEZONE: str = Field(default='Asia/Almaty', env='TIMEZONE')

    @property
    def scraping_hours_list(self) -> List[int]:
        """Parse comma-separated scraping hours"""
        return [int(x.strip()) for x in self.SCRAPING_HOURS.split(',') if x.strip()]
    ENABLE_DIGEST_MODE: bool = Field(default=False, env='ENABLE_DIGEST_MODE')
    ENABLE_ARTICLE_MODE: bool = Field(default=True, env='ENABLE_ARTICLE_MODE')
    MAX_ARTICLE_SUMMARY_SENTENCES: int = Field(default=5, env='MAX_ARTICLE_SUMMARY_SENTENCES')
    SEND_ARTICLES_IMMEDIATELY: bool = Field(default=True, env='SEND_ARTICLES_IMMEDIATELY')

    # Logging Configuration
    LOG_LEVEL: str = Field(default='INFO', env='LOG_LEVEL')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


# Global settings instance
settings = Settings()
