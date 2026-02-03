"""Test parser to see what's happening"""
import asyncio
import sys

sys.path.insert(0, '.')

from src.scraper.parsers.bolashak_parser import BolashakParser


async def test_parser():
    print("Тестирую парсер Bolashak...")
    parser = BolashakParser()

    print(f"URL: {parser.source_url}")
    print("\nПытаюсь получить список статей...")

    try:
        articles = await parser.fetch_articles()
        print(f"\n✓ Найдено статей: {len(articles)}")

        if articles:
            print("\nПервые 3 статьи:")
            for i, article in enumerate(articles[:3], 1):
                print(f"\n{i}. {article['title']}")
                print(f"   URL: {article['url']}")
                print(f"   Дата: {article.get('published_at', 'Не указана')}")
        else:
            print("\n⚠️ Статьи не найдены. Возможные причины:")
            print("1. CSS-селекторы не соответствуют структуре сайта")
            print("2. Сайт блокирует запросы")
            print("3. Структура сайта изменилась")

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_parser())
