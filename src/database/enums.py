"""Enumerations for database models"""
from enum import Enum


class DigestStatus(str, Enum):
    """Status of a digest"""
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"


class PostStatus(str, Enum):
    """Status of a post"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
