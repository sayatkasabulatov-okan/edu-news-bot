"""Test script for relevance filtering"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.relevance_checker import relevance_checker


def test_relevance_checker():
    """Test relevance checker with various examples"""

    test_cases = [
        # Релевантные статьи (должны пройти)
        {
            'title': 'Стипендии для студентов в 2024 году',
            'content': 'Министерство образования объявило новые гранты для студентов...',
            'expected': True
        },
        {
            'title': 'Scholarship for International Students at Oxford University',
            'content': 'Oxford University announces fully funded scholarships for graduate students...',
            'expected': True
        },
        {
            'title': 'Как поступить в зарубежный университет',
            'content': 'Полное руководство по поступлению в университеты за рубежом для казахстанских студентов...',
            'expected': True
        },
        {
            'title': 'Стажировка в ООН для молодых специалистов',
            'content': 'Организация Объединённых Наций открыла набор на оплачиваемую стажировку...',
            'expected': True
        },
        {
            'title': 'Бесплатные онлайн-курсы от ведущих университетов',
            'content': 'Coursera и EdX предлагают бесплатные курсы с сертификатами...',
            'expected': True
        },

        # Нерелевантные статьи (не должны пройти)
        {
            'title': 'Новый фильм вышел в прокат',
            'content': 'В кинотеатрах началась премьера нового блокбастера...',
            'expected': False
        },
        {
            'title': 'Футбольный матч закончился со счетом 3:1',
            'content': 'Вчера прошел матч между командами А и Б...',
            'expected': False
        },
        {
            'title': 'Акции компании выросли на 10%',
            'content': 'Биржевые торги показали рост акций технологических компаний...',
            'expected': False
        },
        {
            'title': 'Погода на выходные',
            'content': 'Прогноз погоды на ближайшие дни обещает солнечную погоду...',
            'expected': False
        },

        # Граничные случаи
        {
            'title': 'Новости образования: министр встретился с депутатами',
            'content': 'Министр образования обсудил с депутатами вопросы финансирования школ и университетов...',
            'expected': True  # Есть слова "образование", "университет"
        },
        {
            'title': 'Студенческий спортивный клуб провел чемпионат',
            'content': 'Студенты университета организовали футбольный турнир...',
            'expected': True  # Есть слово "студент", "университет"
        }
    ]

    print("="*80)
    print("🧪 ТЕСТИРОВАНИЕ ФИЛЬТРА РЕЛЕВАНТНОСТИ")
    print("="*80 + "\n")

    passed = 0
    failed = 0

    for i, test_case in enumerate(test_cases, 1):
        title = test_case['title']
        content = test_case['content']
        expected = test_case['expected']

        result = relevance_checker.check_relevance(title, content)
        actual = result['is_relevant']

        status = "✅ PASS" if actual == expected else "❌ FAIL"
        if actual == expected:
            passed += 1
        else:
            failed += 1

        print(f"\nТест {i}: {status}")
        print(f"Заголовок: {title}")
        print(f"Ожидалось: {'Релевантно' if expected else 'Нерелевантно'}")
        print(f"Результат: {'Релевантно' if actual else 'Нерелевантно'}")
        print(f"Оценка: {result['score']}")
        print(f"Причина: {result['reason']}")
        if result['relevant_matches']:
            print(f"Найденные ключевые слова: {', '.join(result['relevant_matches'][:5])}")
        if result['irrelevant_matches']:
            print(f"Нерелевантные слова: {', '.join(result['irrelevant_matches'][:3])}")
        print("-"*80)

    print(f"\n{'='*80}")
    print(f"📊 ИТОГИ:")
    print(f"   ✅ Пройдено: {passed}/{len(test_cases)}")
    print(f"   ❌ Провалено: {failed}/{len(test_cases)}")
    print(f"   📈 Успех: {passed/len(test_cases)*100:.1f}%")
    print(f"{'='*80}\n")

    return passed == len(test_cases)


def test_keywords_coverage():
    """Show all keywords used for filtering"""
    print("\n" + "="*80)
    print("📋 КЛЮЧЕВЫЕ СЛОВА ДЛЯ ФИЛЬТРАЦИИ")
    print("="*80 + "\n")

    print("✅ РЕЛЕВАНТНЫЕ СЛОВА (русский):")
    print("-"*80)
    for i, keyword in enumerate(relevance_checker.RELEVANT_KEYWORDS['ru'][:30], 1):
        print(f"{i:2d}. {keyword}")
    print(f"\n   ... всего {len(relevance_checker.RELEVANT_KEYWORDS['ru'])} слов\n")

    print("✅ РЕЛЕВАНТНЫЕ СЛОВА (английский):")
    print("-"*80)
    for i, keyword in enumerate(relevance_checker.RELEVANT_KEYWORDS['en'][:30], 1):
        print(f"{i:2d}. {keyword}")
    print(f"\n   ... всего {len(relevance_checker.RELEVANT_KEYWORDS['en'])} слов\n")

    print("❌ ИСКЛЮЧЕНИЯ (русский):")
    print("-"*80)
    for i, keyword in enumerate(relevance_checker.IRRELEVANT_KEYWORDS['ru'], 1):
        print(f"{i:2d}. {keyword}")
    print()

    print("❌ ИСКЛЮЧЕНИЯ (английский):")
    print("-"*80)
    for i, keyword in enumerate(relevance_checker.IRRELEVANT_KEYWORDS['en'], 1):
        print(f"{i:2d}. {keyword}")
    print()


if __name__ == "__main__":
    print("\n")

    # Test relevance checker
    success = test_relevance_checker()

    # Show keywords
    test_keywords_coverage()

    print("="*80)
    if success:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
    print("="*80 + "\n")
