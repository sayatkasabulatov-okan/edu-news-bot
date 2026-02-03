"""Test hallucination checker"""
from src.services.hallucination_checker import HallucinationChecker


def test_hallucination_checker():
    """Test the hallucination checker with various scenarios"""

    checker = HallucinationChecker()

    print("🧪 Тест 1: Нормальный дайджест без галлюцинаций")
    print("=" * 60)

    digest = """
    🎓 Новая стипендия для студентов

    Университет открыл новую программу стипендий.
    Подробности на https://example.edu/scholarship

    Источник: https://example.edu/news
    """

    sources = [
        {
            'url': 'https://example.edu/news',
            'content': 'Университет объявил о новой программе. Подробности: https://example.edu/scholarship'
        }
    ]

    result = checker.check_digest(digest, sources)
    print(f"Has issues: {result['has_issues']}")
    print(f"Suspicious URLs: {result['suspicious_urls']}")
    print(f"Warnings: {result['warnings']}")
    print(f"Valid URLs: {result['valid_urls']}")
    print(f"\n{checker.format_warnings(result)}\n")

    print("\n🧪 Тест 2: Дайджест с галлюцинациями")
    print("=" * 60)

    digest_halluc = """
    🎓 Стипендия в Гарварде

    По данным исследования https://fake-site.com/study,
    Гарвард открыл новую программу.

    Источник: https://example.edu/news
    """

    result2 = checker.check_digest(digest_halluc, sources)
    print(f"Has issues: {result2['has_issues']}")
    print(f"Suspicious URLs: {result2['suspicious_urls']}")
    print(f"Warnings: {result2['warnings']}")
    print(f"\n{checker.format_warnings(result2)}\n")

    print("\n🧪 Тест 3: Утверждение без источника")
    print("=" * 60)

    digest_claim = """
    🎓 Новости образования

    Согласно исследованию, 95% студентов получают стипендии.

    Источник: https://example.edu/news
    """

    result3 = checker.check_digest(digest_claim, sources)
    print(f"Has issues: {result3['has_issues']}")
    print(f"Warnings: {result3['warnings']}")
    print(f"\n{checker.format_warnings(result3)}\n")

    print("\n✅ Тесты завершены!")


if __name__ == "__main__":
    test_hallucination_checker()
