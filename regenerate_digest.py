"""Regenerate digest with updated prompts"""
import asyncio
import sys

sys.path.insert(0, '.')

from src.database.connection import get_session
from src.database.repositories.digest_repo import DigestRepository
from src.database.repositories.article_repo import ArticleRepository
from src.ai.summarizer import ContentSummarizer


async def regenerate_digest(digest_id: int):
    """Regenerate digest content with new prompts"""

    async with get_session() as session:
        digest_repo = DigestRepository(session)
        article_repo = ArticleRepository(session)
        summarizer = ContentSummarizer()

        # Get existing digest
        digest = await digest_repo.get_by_id(digest_id)
        if not digest:
            print(f"❌ Дайджест #{digest_id} не найден")
            return

        print(f"📝 Дайджест #{digest_id} найден")
        print(f"   Статус: {digest.status}")
        print(f"   Статей использовано: {len(digest.article_ids)}")

        # Get articles
        articles = []
        for article_id in digest.article_ids:
            article = await article_repo.get_by_id(article_id)
            if article:
                articles.append(article)

        print(f"\n📥 Получено {len(articles)} статей")

        # Prepare articles data
        articles_data = [
            {
                'title': article.title,
                'content': article.content or '',
            }
            for article in articles
        ]

        # Generate new content
        print(f"\n🤖 Генерирую новый контент с обновленным промптом...")
        new_content = await summarizer.create_digest(articles_data)

        print(f"\n✅ Новый контент создан!")
        print(f"   Длина: {len(new_content)} символов")
        print(f"\n📄 Содержание:")
        print("="*60)
        print(new_content)
        print("="*60)

        # Update digest
        await digest_repo.update_content(digest_id, new_content)
        await session.commit()

        print(f"\n✅ Дайджест #{digest_id} успешно обновлен!")


if __name__ == "__main__":
    digest_id = 2  # Regenerate digest #2
    print(f"🔄 Регенерация дайджеста #{digest_id}\n")
    asyncio.run(regenerate_digest(digest_id))
