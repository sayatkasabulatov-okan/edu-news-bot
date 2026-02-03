"""Test new parsers"""
import asyncio
import sys

sys.path.insert(0, '.')

from src.scraper.parsers.opportunities_circle_parser import OpportunitiesCircleParser
from src.scraper.parsers.opportunities_corners_parser import OpportunitiesCornersParser


async def test_opportunities_circle():
    print("\n" + "="*60)
    print("Testing Opportunities Circle Parser")
    print("="*60)

    parser = OpportunitiesCircleParser()
    print(f"URL: {parser.source_url}\n")

    print("Fetching articles...")
    articles = await parser.fetch_articles()
    print(f"✓ Found {len(articles)} articles\n")

    if articles:
        print("First 3 articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   URL: {article['url']}")

        # Test parsing first article
        print(f"\n\nTesting full article parsing...")
        first_article = await parser.parse_article(articles[0]['url'])
        if first_article:
            print(f"✓ Successfully parsed article")
            print(f"  Title: {first_article['title'][:60]}...")
            print(f"  Content length: {len(first_article['content'])} chars")
        else:
            print("✗ Failed to parse article")
    else:
        print("⚠️ No articles found")


async def test_opportunities_corners():
    print("\n" + "="*60)
    print("Testing Opportunities Corners Parser")
    print("="*60)

    parser = OpportunitiesCornersParser()
    print(f"URL: {parser.source_url}\n")

    print("Fetching articles...")
    articles = await parser.fetch_articles()
    print(f"✓ Found {len(articles)} articles\n")

    if articles:
        print("First 3 articles:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   URL: {article['url']}")
            if article.get('published_at'):
                print(f"   Date: {article['published_at']}")

        # Test parsing first article
        print(f"\n\nTesting full article parsing...")
        first_article = await parser.parse_article(articles[0]['url'])
        if first_article:
            print(f"✓ Successfully parsed article")
            print(f"  Title: {first_article['title'][:60]}...")
            print(f"  Content length: {len(first_article['content'])} chars")
        else:
            print("✗ Failed to parse article")
    else:
        print("⚠️ No articles found")


async def main():
    print("\n🧪 Testing New Parsers\n")

    try:
        await test_opportunities_circle()
        await test_opportunities_corners()

        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
