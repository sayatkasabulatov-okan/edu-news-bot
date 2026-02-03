"""Custom exceptions for the bot"""


class BotException(Exception):
    """Base exception for all bot errors"""
    user_message = "Произошла ошибка. Попробуй позже."


# Digest exceptions
class DigestException(BotException):
    """Base exception for digest-related errors"""
    pass


class DigestNotFoundError(DigestException):
    """Digest not found in database"""
    user_message = "Дайджест не найден"


class DigestAlreadyPublishedError(DigestException):
    """Attempting to modify already published digest"""
    user_message = "Дайджест уже опубликован и не может быть изменен"


class DigestCreationError(DigestException):
    """Error creating digest"""
    user_message = "Не удалось создать дайджест"


class InsufficientArticlesError(DigestException):
    """Not enough articles to create digest"""
    user_message = "Недостаточно статей для создания дайджеста"


# Article exceptions
class ArticleException(BotException):
    """Base exception for article-related errors"""
    pass


class ArticleNotFoundError(ArticleException):
    """Article not found"""
    user_message = "Статья не найдена"


class ArticleParsingError(ArticleException):
    """Error parsing article"""
    user_message = "Ошибка при парсинге статьи"


# Image exceptions
class ImageException(BotException):
    """Base exception for image-related errors"""
    pass


class ImageGenerationError(ImageException):
    """Error generating image"""
    user_message = "Не удалось сгенерировать изображение"


class ImageDownloadError(ImageException):
    """Error downloading image"""
    user_message = "Не удалось скачать изображение"


# Publication exceptions
class PublicationException(BotException):
    """Base exception for publication errors"""
    pass


class ChannelAccessError(PublicationException):
    """Cannot access channel"""
    user_message = "Нет доступа к каналу"


class PublicationFailedError(PublicationException):
    """Failed to publish to channel"""
    user_message = "Не удалось опубликовать в канал"


# Permission exceptions
class PermissionException(BotException):
    """Base exception for permission errors"""
    pass


class UnauthorizedError(PermissionException):
    """User not authorized"""
    user_message = "У тебя нет прав для этого действия"


# Validation exceptions
class ValidationException(BotException):
    """Base exception for validation errors"""
    pass


class InvalidURLError(ValidationException):
    """Invalid URL provided"""
    user_message = "Неверный формат URL"


class InvalidContentError(ValidationException):
    """Invalid content"""
    user_message = "Неверный формат контента"


# AI exceptions
class AIException(BotException):
    """Base exception for AI-related errors"""
    pass


class AIGenerationError(AIException):
    """Error during AI content generation"""
    user_message = "Ошибка при генерации контента AI"


class AIHallucinationDetectedError(AIException):
    """AI hallucination detected"""
    user_message = "Обнаружены потенциальные галлюцинации в тексте"


# Database exceptions
class DatabaseException(BotException):
    """Base exception for database errors"""
    pass


class DatabaseConnectionError(DatabaseException):
    """Cannot connect to database"""
    user_message = "Ошибка подключения к базе данных"


class DatabaseTransactionError(DatabaseException):
    """Error in database transaction"""
    user_message = "Ошибка транзакции базы данных"
