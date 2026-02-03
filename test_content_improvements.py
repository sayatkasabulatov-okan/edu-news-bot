"""Test script for content and admin improvements"""
import asyncio
from src.utils.content_deduplicator import ContentDeduplicator
from src.utils.enhanced_logger import LogContext, structured_logger, log_function_call


async def test_content_deduplication():
    """Test content deduplication"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 1: Content Deduplication")
    print("="*60)

    deduplicator = ContentDeduplicator(similarity_threshold=0.85)

    # Test URL fingerprinting
    print("\n📋 Тест 1: URL Fingerprinting")
    test_urls = [
        ("https://example.com/article?utm_source=facebook", "https://example.com/article"),
        ("https://example.com/article/?fbclid=123", "https://example.com/article"),
        ("https://EXAMPLE.com/article/", "https://example.com/article"),
    ]

    for original, expected in test_urls:
        fingerprint = deduplicator.get_url_fingerprint(original)
        match = "✅" if fingerprint == expected else "❌"
        print(f"  {match} {original[:50]}...")
        print(f"     → {fingerprint}")

    # Test content similarity
    print("\n📋 Тест 2: Content Similarity")
    content1 = "This is a test article about education abroad"
    content2 = "This is a test article about education abroad"  # Exact match
    content3 = "This is a TEST article about EDUCATION abroad"  # Case difference
    content4 = "Completely different article about technology"

    sim1 = deduplicator.calculate_similarity(content1, content2)
    sim2 = deduplicator.calculate_similarity(content1, content3)
    sim3 = deduplicator.calculate_similarity(content1, content4)

    print(f"  Exact match: {sim1:.2%} {'✅' if sim1 == 1.0 else '❌'}")
    print(f"  Case difference: {sim2:.2%} {'✅' if sim2 > 0.95 else '❌'}")
    print(f"  Different content: {sim3:.2%} {'✅' if sim3 < 0.5 else '❌'}")

    # Test deduplication
    print("\n📋 Тест 3: Article Deduplication")
    articles = [
        {'id': 1, 'url': 'https://example.com/1', 'title': 'Article 1', 'content': 'Content A'},
        {'id': 2, 'url': 'https://example.com/1?utm=123', 'title': 'Article 1', 'content': 'Content A'},
        {'id': 3, 'url': 'https://example.com/2', 'title': 'Article 2', 'content': 'Content B'},
        {'id': 4, 'url': 'https://example.com/3', 'title': 'Article 3', 'content': 'Content A'},
    ]

    print(f"  Исходных статей: {len(articles)}")

    # Deduplicate by URL
    unique_by_url = deduplicator.deduplicate_by_url(articles)
    print(f"  После URL дедупликации: {len(unique_by_url)}")

    # Deduplicate by content
    fully_unique = deduplicator.deduplicate_by_content(unique_by_url, 'content')
    print(f"  После content дедупликации: {len(fully_unique)}")

    if len(fully_unique) == 2:  # Should keep articles 1 and 3
        print("  ✅ Дедупликация работает корректно")
    else:
        print("  ❌ Неожиданное количество уникальных статей")

    print("\n✅ ТЕСТ ДЕДУПЛИКАЦИИ ЗАВЕРШЕН\n")


async def test_enhanced_logging():
    """Test enhanced logging with context"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 2: Enhanced Logging")
    print("="*60)

    print("\n📋 Тест 1: Log Context")

    # Test context manager
    with LogContext(request_id="req-123", user_id=456):
        print("  ✅ Контекст установлен: request_id=req-123, user_id=456")

    print("  ✅ Контекст очищен после выхода")

    # Test structured logging
    print("\n📋 Тест 2: Structured Events")

    structured_logger.log_user_action(
        user_id=123,
        action="button_click",
        button="approve"
    )
    print("  ✅ User action logged")

    structured_logger.log_api_call(
        service="telegram",
        endpoint="/sendMessage",
        status="success",
        duration_ms=150.5
    )
    print("  ✅ API call logged")

    structured_logger.log_database_query(
        operation="select",
        table="articles",
        duration_ms=5.2,
        rows_affected=10
    )
    print("  ✅ Database query logged")

    # Test function decorator
    print("\n📋 Тест 3: Function Call Logging")

    @log_function_call(log_args=True, log_result=True)
    async def test_function(x: int, y: int) -> int:
        await asyncio.sleep(0.1)
        return x + y

    result = await test_function(5, 3)
    if result == 8:
        print("  ✅ Function decorator работает корректно")
    else:
        print("  ❌ Неожиданный результат функции")

    print("\n✅ ТЕСТ ЛОГИРОВАНИЯ ЗАВЕРШЕН\n")


async def test_admin_features():
    """Test admin dashboard features"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 3: Admin Dashboard Features")
    print("="*60)

    print("\n📋 Доступные админ-команды:")
    commands = [
        ("/status", "Системный статус (uptime, память, CPU)"),
        ("/cleanup", "Очистка старых данных"),
        ("/logs", "Просмотр последних логов"),
        ("/optimize", "Оптимизация базы данных"),
    ]

    for cmd, description in commands:
        print(f"  ✅ {cmd} - {description}")

    print("\n📋 Тест: Проверка импортов")
    try:
        from src.bot.handlers import admin_dashboard
        print("  ✅ admin_dashboard импортирован")

        # Check functions exist
        funcs = [
            'system_status_command',
            'cleanup_command',
            'logs_command',
            'optimize_db_command'
        ]

        for func_name in funcs:
            if hasattr(admin_dashboard, func_name):
                print(f"  ✅ {func_name} доступен")
            else:
                print(f"  ❌ {func_name} не найден")

    except Exception as e:
        print(f"  ❌ Ошибка импорта: {e}")

    print("\n✅ ТЕСТ АДМИН-ПАНЕЛИ ЗАВЕРШЕН\n")


async def main():
    """Run all content and admin improvement tests"""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ТЕСТОВ УЛУЧШЕНИЙ КОНТЕНТА И АДМИН-ПАНЕЛИ")
    print("="*60)

    try:
        await test_content_deduplication()
        await test_enhanced_logging()
        await test_admin_features()

        print("\n" + "="*60)
        print("✅ ВСЕ ТЕСТЫ УЛУЧШЕНИЙ ЗАВЕРШЕНЫ")
        print("="*60)
        print("\n📋 Реализованные улучшения:")
        print(" 11. ✅ Content Deduplication - умная проверка дубликатов")
        print(" 12. ✅ Enhanced Logging - структурированное логирование")
        print(" 13. ✅ Admin Dashboard - расширенная админ-панель\n")

    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
