"""Test analytics feature directly"""
import asyncio
from telegram import Bot

from src.config import settings
from src.database.connection import get_session
from src.database.repositories.post_repo import PostRepository
from src.services.analytics_service import AnalyticsService


async def test_analytics():
    """Test analytics generation and sending"""
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    print("📊 Тестирую аналитику...\n")

    async with get_session() as session:
        post_repo = PostRepository(session)

        # Get last 5 published posts
        posts = await post_repo.get_published_posts(limit=5)

        if not posts:
            print("❌ Нет опубликованных постов для анализа.")
            return

        print(f"✅ Найдено {len(posts)} опубликованных постов\n")

        # Get analytics service
        analytics_service = AnalyticsService(bot)

        # Get mock statistics
        statistics = await analytics_service.get_mock_statistics(posts)

        print("📈 Статистика:")
        for stat in statistics:
            print(f"  Пост #{stat['post_id']}: {stat['views']} просмотров, "
                  f"{stat['reactions']} реакций, {stat['forwards']} пересылок")

        print("\n🎨 Генерирую диаграмму...")

        # Generate chart
        chart_image = analytics_service.generate_analytics_chart(statistics)

        # Generate text summary
        text_summary = analytics_service.generate_text_analytics(statistics)

        print("\n📤 Отправляю аналитику в Telegram...")

        # Send chart as photo
        await bot.send_photo(
            chat_id=settings.MODERATOR_CHAT_ID,
            photo=chart_image,
            caption=text_summary,
            parse_mode='Markdown'
        )

        print("\n✅ Аналитика отправлена!")
        print("\nПроверь Telegram - должна появиться красивая диаграмма с:")
        print("  📊 4 графика (просмотры, реакции, пересылки, таблица)")
        print("  📈 Текстовая сводка с общей статистикой")
        print("  🏆 Информация о лучшем посте")


if __name__ == "__main__":
    asyncio.run(test_analytics())
