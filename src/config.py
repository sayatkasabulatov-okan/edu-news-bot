"""Application configuration using Pydantic Settings"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = Field(..., env='TELEGRAM_BOT_TOKEN')
    MODERATOR_CHAT_ID: int = Field(..., env='MODERATOR_CHAT_ID')
    CHANNEL_ID: int = Field(..., env='CHANNEL_ID')

    # Database Configuration
    DB_HOST: str = Field(default='localhost', env='DB_HOST')
    DB_PORT: int = Field(default=5432, env='DB_PORT')
    DB_NAME: str = Field(..., env='DB_NAME')
    DB_USER: str = Field(..., env='DB_USER')
    DB_PASSWORD: str = Field(..., env='DB_PASSWORD')

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL"""
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
