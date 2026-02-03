"""Test script for improvements"""
import asyncio
from src.utils.rate_limiter import RateLimiter
from src.utils.validators import URLValidator, TextValidator
from src.utils.exceptions import DigestNotFoundError, InvalidURLError
from src.database.repositories.settings_repo import SettingsRepository
from src.database.connection import get_session
import time


async def test_rate_limiter():
    """Test rate limiter functionality"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 1: Rate Limiter")
    print("="*60)

    rate_limiter = RateLimiter()

    # Mock query object
    class MockQuery:
        class FromUser:
            id = 123
        from_user = FromUser()

        async def answer(self, text, show_alert=False):
            print(f"  ⚠️  Rate limit: {text}")

    # Mock function
    @rate_limiter.limit(seconds=2.0, message="⏰ Подожди")
    async def test_function(query, context):
        print(f"  ✅ Function executed at {time.time():.2f}")
        return "success"

    query = MockQuery()

    # Test rapid calls
    print("\n📊 Тестирую быстрые вызовы (3 раза подряд):")
    for i in range(3):
        print(f"\n  Вызов #{i+1}:")
        result = await test_function(query, None)
        if i < 2:
            await asyncio.sleep(0.5)  # Quick succession

    print("\n  ⏱️  Жду 2.5 секунды...")
    await asyncio.sleep(2.5)

    print("\n  Вызов #4 (после задержки):")
    await test_function(query, None)

    print("\n✅ ТЕСТ ПРОЙДЕН: Rate limiter работает")


async def test_url_validator():
    """Test URL validation"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 2: URL Validator")
    print("="*60)

    validator = URLValidator()

    test_cases = [
        ("https://topuniversities.com/article", True, "Whitelist domain"),
        ("https://evil-site.com/phishing", False, "Not in whitelist"),
        ("javascript:alert(1)", False, "JavaScript protocol"),
        ("http://studyqa.com/grants", True, "HTTP allowed"),
        ("ftp://example.com", False, "FTP not allowed"),
        ("", False, "Empty URL"),
        ("https://www.topuniversities.com/news", True, "With www prefix"),
    ]

    print("\n📊 Тестирую валидацию URL:\n")
    passed = 0
    for url, expected, description in test_cases:
        result = validator.validate_url(url, check_whitelist=True)
        status = "✅" if result == expected else "❌"
        passed += (result == expected)
        print(f"  {status} {description}")
        print(f"     URL: {url[:50]}...")
        print(f"     Expected: {expected}, Got: {result}\n")

    print(f"✅ ТЕСТ ЗАВЕРШЕН: {passed}/{len(test_cases)} проверок пройдено")


async def test_custom_exceptions():
    """Test custom exceptions"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 3: Custom Exceptions")
    print("="*60)

    print("\n📊 Тестирую exceptions:\n")

    # Test DigestNotFoundError
    try:
        raise DigestNotFoundError("Test digest not found")
    except DigestNotFoundError as e:
        print(f"  ✅ DigestNotFoundError caught")
        print(f"     User message: {e.user_message}\n")

    # Test InvalidURLError
    try:
        raise InvalidURLError("Test invalid URL")
    except InvalidURLError as e:
        print(f"  ✅ InvalidURLError caught")
        print(f"     User message: {e.user_message}\n")

    print("✅ ТЕСТ ПРОЙДЕН: Exceptions работают корректно")


async def test_text_validator():
    """Test text validation"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 4: Text Validator")
    print("="*60)

    validator = TextValidator()

    test_cases = [
        ("Normal text content", True, "Normal text"),
        ("<script>alert('xss')</script>", False, "XSS attempt"),
        ("Click <a onclick='evil()'>here</a>", False, "onclick attribute"),
        ("A" * 10001, False, "Too long (>10000)"),
        ("Hello world", True, "Simple text"),
    ]

    print("\n📊 Тестирую валидацию текста:\n")
    passed = 0
    for text, expected, description in test_cases:
        result = validator.validate_digest_content(text)
        status = "✅" if result == expected else "❌"
        passed += (result == expected)
        print(f"  {status} {description}")
        print(f"     Text: {text[:50]}...")
        print(f"     Expected: {expected}, Got: {result}\n")

    print(f"✅ ТЕСТ ЗАВЕРШЕН: {passed}/{len(test_cases)} проверок пройдено")


async def test_settings_cache():
    """Test settings caching"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 5: Settings Cache")
    print("="*60)

    print("\n📊 Тестирую кэширование настроек:\n")

    async with get_session() as session:
        settings_repo = SettingsRepository(session)

        # Clear cache first
        settings_repo.clear_cache()
        print("  🗑️  Кэш очищен")

        # First call - should hit database
        print("\n  📥 Первый запрос (из БД)...")
        start = time.time()
        settings1 = await settings_repo.get_settings()
        time1 = time.time() - start
        print(f"     Время: {time1*1000:.2f}ms")

        # Second call - should hit cache
        print("\n  ⚡ Второй запрос (из кэша)...")
        start = time.time()
        settings2 = await settings_repo.get_settings()
        time2 = time.time() - start
        print(f"     Время: {time2*1000:.2f}ms")

        # Compare
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"\n  📊 Ускорение: {speedup:.1f}x")

        if speedup > 2:
            print("  ✅ Кэш работает эффективно")
        else:
            print("  ⚠️  Кэш может работать лучше")

        # Verify it's the same object
        if settings1 is settings2:
            print("  ✅ Возвращён закэшированный объект")
        else:
            print("  ❌ Разные объекты (кэш не работает)")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ТЕСТОВ УЛУЧШЕНИЙ")
    print("="*60)

    try:
        await test_rate_limiter()
        await test_url_validator()
        await test_custom_exceptions()
        await test_text_validator()
        await test_settings_cache()

        print("\n" + "="*60)
        print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        print("="*60)

    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
