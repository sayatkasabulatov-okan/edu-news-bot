"""SQLAlchemy database models"""
from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, ARRAY, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Source(Base):
    """News source model"""
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    parser_class = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Article(Base):
    """Article model"""
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'))
    title = Column(Text, nullable=False)
    url = Column(Text, unique=True, nullable=False)
    content = Column(Text)
    image_url = Column(Text)
    published_at = Column(TIMESTAMP)
    scraped_at = Column(TIMESTAMP, server_default=func.now())
    is_processed = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    source = relationship("Source", foreign_keys=[source_id])
    posts = relationship("Post", back_populates="article")


class Digest(Base):
    """Digest model - AI-generated summary of multiple articles"""
    __tablename__ = 'digests'

    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    article_ids = Column(ARRAY(Integer), nullable=False)
    image_url = Column(Text)
    status = Column(String(50), default='draft')
    moderator_message_id = Column(BigInteger)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    posts = relationship("Post", back_populates="digest")


class Post(Base):
    """Post model - published or scheduled posts

    Can be linked to either:
    - digest_id: Post from a digest (multiple articles)
    - article_id: Post from a single article
    """
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    # Digest reference (for posts from digests) - now nullable
    digest_id = Column(Integer, ForeignKey('digests.id'), nullable=True)
    # Article reference (for individual article posts) - new field
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=True, index=True)
    content = Column(Text, nullable=False)
    status = Column(String(50), default='draft')
    scheduled_at = Column(TIMESTAMP)
    published_at = Column(TIMESTAMP)
    channel_id = Column(BigInteger)
    message_id = Column(BigInteger)
    error_message = Column(Text)
    # Statistics fields
    views_count = Column(Integer, default=0)
    reactions_count = Column(Integer, default=0)
    forwards_count = Column(Integer, default=0)
    last_stats_update = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    digest = relationship("Digest", back_populates="posts")
    article = relationship("Article", back_populates="posts")


class PostRevision(Base):
    """Post revision model - history of edits"""
    __tablename__ = 'post_revisions'

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'))
    content = Column(Text, nullable=False)
    edited_by = Column(BigInteger)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Settings(Base):
    """Bot settings model"""
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    # Education sections (enabled sections list)
    education_sections = Column(ARRAY(String), default=[
        'higher_education',      # Высшее образование
        'secondary_education',   # Среднее образование
        'private_schools',       # Частные школы
        'online_education',      # Онлайн-образование
        'courses_edtech',        # Курсы и EdTech
        'grants_scholarships',   # Гранты, стипендии
        'reforms',               # Образовательные реформы
        'legislation',           # Новости и изменения законодательства
        'international'          # Международные программы
    ])
    # Content language
    language = Column(String(10), default='ru')  # 'ru', 'kz', 'en'
    # Post length setting
    post_length = Column(String(20), default='short')  # 'short', 'medium', 'long'
    # Publication schedule
    publication_hour = Column(Integer, default=9)  # Hour of the day (0-23)
    publication_frequency = Column(Integer, default=1)  # Posts per day
    # Images settings
    images_enabled = Column(Boolean, default=True)  # Enable/disable image generation
    # Timestamps
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
