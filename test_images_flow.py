"""Test images flow - parsing articles with images and creating digest"""
import asyncio
import sys

sys.path.insert(0, '.')

from src.database.connection import get_session
from src.database.repositories.article_repo import ArticleRepository
from src.services.digest_service import DigestService
from sqlalchemy import update
from src.database.models import Article


async def reset_articles():
    """Reset is_processed flag for testing"""
    async with get_session() as session:
        # Reset all articles to unprocessed
        await session.execute(
            update(Article).values(is_processed=False)
        )
        await session.commit()
        print("✅ Сброшен флаг is_processed для всех статей")


async def collect_new_articles():
    """Collect new articles from parsers"""
    from src.scraper.scheduler import ScraperScheduler

    scheduler = ScraperScheduler()

    print("\n📥 Собираю новые статьи с изображениями...")
    # Run the daily scraping task
    await scheduler.run_daily_scraping()

    print(f"\n✅ Сбор статей завершен")
    return True


async def check_articles_with_images():
    """Check how many articles have images"""
    async with get_session() as session:
        repo = ArticleRepository(session)

        # Get unprocessed articles
        articles = await repo.get_unprocessed(limit=10)

        print(f"\n📊 Статистика по необработанным статьям:")
        print(f"   Всего необработанных: {len(articles)}")

        with_images = 0
        without_images = 0

        for article in articles:
            if article.image_url:
                with_images += 1
                print(f"\n   ✅ С изображением: {article.title[:60]}...")
                print(f"      Image: {article.image_url[:80]}...")
            else:
                without_images += 1

        print(f"\n   📸 С изображениями: {with_images}")
        print(f"   ❌ Без изображений: {without_images}")

        return len(articles), with_images


async def test_digest_creation():
    """Test digest creation with images"""
    async with get_session() as session:
        service = DigestService(session)

        print("\n\n🔄 Создаю дайджест...")

        try:
            digest_id = await service.create_digest_if_ready()

            if digest_id:
                # Get created digest
                digest = await service.get_digest(digest_id)

                print(f"\n✅ Дайджест #{digest_id} создан!")
                print(f"\n📝 Содержание (первые 200 символов):")
                print(f"   {digest.content[:200]}...")

                if digest.image_url:
                    print(f"\n📸 Изображение: ДА")
                    print(f"   URL: {digest.image_url}")
                else:
                    print(f"\n📸 Изображение: НЕТ (будет сгенерировано при необходимости)")

                return digest_id, digest.image_url
            else:
                print("\n⚠️ Недостаточно статей для создания дайджеста")
                print("   Нужно минимум 5 необработанных статей")
                return None, None

        except Exception as e:
            print(f"\n❌ Ошибка при создании дайджеста: {e}")
            import traceback
            traceback.print_exc()
            return None, None


async def main():
    print("🧪 Тестирование функционала изображений\n")
    print("="*60)

    # Step 1: Reset articles for testing
    print("\n1️⃣ Сброс флага обработки статей для тестирования...")
    await reset_articles()

    # Step 2: Collect new articles
    print("\n2️⃣ Сбор новых статей...")
    new_count = await collect_new_articles()

    # Step 3: Check articles
    print("\n3️⃣ Проверка статей...")
    total, with_images = await check_articles_with_images()

    # Step 4: Create digest
    if total >= 5:
        print("\n4️⃣ Создание дайджеста...")
        digest_id, image_url = await test_digest_creation()

        if digest_id:
            print("\n" + "="*60)
            print("✅ ТЕСТ ПРОЙДЕН!")
            print("="*60)
            print(f"\nДайджест #{digest_id} готов к публикации")
            if image_url:
                print(f"С изображением: {image_url}")
            else:
                print("Изображение будет сгенерировано через DALL-E при публикации")
    else:
        print(f"\n⚠️ Недостаточно статей: {total}/5")
        print("Запусти /collect через бота или подожди накопления статей")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
