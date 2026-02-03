# 📊 Интеграция источников из Excel в систему парсинга

## 📝 Описание

Добавлены все сайты из листа **"Сайты для поиска"** Excel-файла **"Контент план Grants 2023.xlsx"** в систему парсинга бота.

---

## ✅ Что было сделано

### 1. Создан универсальный парсер GenericParser

**Файл:** [src/scraper/parsers/generic_parser.py](src/scraper/parsers/generic_parser.py)

**Возможности:**
- ✅ Автоматическое определение структуры сайта
- ✅ Использование эвристик для поиска статей
- ✅ Поддержка различных HTML-структур
- ✅ Извлечение заголовков, контента и дат публикации
- ✅ Работа с относительными и абсолютными URL

**Как работает:**
```python
# Пытается найти статьи используя популярные селекторы:
- article, .post, .article, .news-item
- .entry, .blog-post, [class*="article"]

# Извлекает контент используя:
- h1, h2 для заголовков
- article, .content, .post-content для текста
- time, .date для дат публикации
```

### 2. Добавлен скрипт для массового добавления источников

**Файл:** [scripts/add_excel_sources.py](scripts/add_excel_sources.py)

**Функционал:**
- ✅ Читает список источников из кода
- ✅ Проверяет, не существует ли источник уже в БД
- ✅ Добавляет только новые источники
- ✅ Показывает статистику и полный список источников

---

## 📋 Добавленные источники

Из Excel файла было добавлено **11 новых источников**:

| № | Название | URL | Парсер |
|---|----------|-----|--------|
| 1 | ST-GR - Гранты и стипендии | https://st-gr.com/?cat=4 | GenericParser |
| 2 | SICA Grants - Social Innovation | https://socialinnovationca.org/ru/grants-ru/sica-grants/ | GenericParser |
| 3 | Grantist - База грантов | https://grantist.com/ | GenericParser |
| 4 | The Village KZ - Образование | https://www.the-village-kz.com/village/city/education | GenericParser |
| 5 | Scholars4Dev - Стипендии | https://www.scholars4dev.com/ | GenericParser |
| 6 | Opportunities For Youth | https://opportunitiesforyouth.org/ | GenericParser |
| 7 | Great YOP - Образовательные возможности | https://greatyop.com/fully-funded-scholarships-for-international-students/ | GenericParser |
| 8 | Inform.kz - Новости образования | https://www.inform.kz/ | GenericParser |
| 9 | МОН РК - Министерство образования | https://www.gov.kz/memleket/entities/sci?lang=ru | GenericParser |
| 10 | 24.kz - Новости Казахстана | https://24.kz/ru | GenericParser |
| 11 | Zakon.kz - Законодательство об образовании | https://www.zakon.kz/ | GenericParser |

**Примечание:** Источник **Bright Scholarship** (https://brightscholarship.com/) уже был в базе данных с собственным парсером.

---

## 📊 Итоговая статистика

### До интеграции:
- 📚 Источников в базе: **10**
- 🔧 Специализированных парсеров: **9**

### После интеграции:
- 📚 Источников в базе: **21** (+11)
- 🔧 Специализированных парсеров: **9**
- 🌐 Универсальных парсеров: **11** (GenericParser)

---

## 🚀 Как использовать

### Автоматический сбор новостей

Бот автоматически собирает новости со всех источников по расписанию (каждый день в 9:00).

### Ручной запуск сбора

```bash
# В Telegram боте
/collect

# Или через кнопку
🔄 Собрать новости
```

### Проверка источников в базе данных

```bash
source venv/bin/activate
python3 << EOF
import asyncio
from src.database.connection import get_session
from src.database.models import Source
from sqlalchemy import select

async def show_sources():
    async with get_session() as session:
        result = await session.execute(select(Source))
        sources = result.scalars().all()
        for i, s in enumerate(sources, 1):
            print(f"{i}. {s.name} - {s.parser_class}")

asyncio.run(show_sources())
EOF
```

---

## 🎯 Преимущества GenericParser

### ✅ Плюсы:
1. **Быстрое добавление** - не нужно писать парсер для каждого сайта
2. **Универсальность** - работает с большинством новостных сайтов
3. **Гибкость** - использует множество селекторов и эвристик
4. **Надежность** - обрабатывает ошибки и продолжает работу

### ⚠️ Ограничения:
1. **Точность** - может извлекать лишний контент или пропускать важный
2. **Специфичность** - не учитывает особенности конкретных сайтов
3. **Качество** - может быть хуже чем у специализированных парсеров

---

## 🔧 Улучшения в будущем

Для повышения качества парсинга рекомендуется:

### 1. Создать специализированные парсеры

Для наиболее важных источников создать отдельные парсеры:

```bash
# Пример: создать парсер для ST-GR
cp src/scraper/parsers/example_parser.py src/scraper/parsers/stgr_parser.py
# Отредактировать селекторы под структуру сайта ST-GR
```

### 2. Мониторить качество парсинга

Периодически проверять, насколько хорошо GenericParser извлекает контент:

```bash
# Запустить тестовый сбор
/collect

# Проверить логи
python3 bot_control.py logs 50 | grep -i "error\|warning"
```

### 3. Настроить приоритеты источников

В админ-панели можно управлять источниками:

```
🔧 Админ-панель → ⚙️ Источники новостей
```

Можно:
- ✅ Включить/выключить источник
- 📝 Изменить URL
- 🔄 Сменить парсер

---

## 📚 Список всех источников в системе

### Специализированные парсеры:
1. StudyQA Education Blog - StudyQAParser
2. EducationAbroad.kz - EducationAbroadParser
3. Top Universities - TopUniversitiesParser
4. Bolashak (2 источника) - BolashakParser
5. Opportunities Circle - OpportunitiesCircleParser
6. Opportunities Corners - OpportunitiesCornersParser
7. Bright Scholarship - BrightScholarshipParser
8. Global Scholarships - GlobalScholarshipsParser
9. SPUBL.kz - SpublParser

### Универсальный парсер (GenericParser):
10. ST-GR - Гранты и стипендии
11. SICA Grants
12. Grantist
13. The Village KZ
14. Scholars4Dev
15. Opportunities For Youth
16. Great YOP
17. Inform.kz
18. МОН РК
19. 24.kz
20. Zakon.kz

---

## 🧪 Тестирование

### Проверить работу парсера:

```bash
source venv/bin/activate
python3 << 'EOF'
import asyncio
from src.scraper.parsers.generic_parser import GenericParser

async def test():
    parser = GenericParser(
        source_url="https://st-gr.com/?cat=4",
        source_name="ST-GR Test"
    )
    articles = await parser.fetch_articles()
    print(f"Найдено статей: {len(articles)}")
    for i, article in enumerate(articles[:3], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   URL: {article['url']}")

asyncio.run(test())
EOF
```

---

## 📞 Поддержка

При возникновении проблем с парсингом:

1. **Проверить логи:**
   ```bash
   python3 bot_control.py logs 100 | grep -i "parser\|scraper"
   ```

2. **Проверить статус источников:**
   ```bash
   python3 << 'EOF'
   import asyncio
   from src.database.connection import get_session
   from src.database.models import Source
   from sqlalchemy import select

   async def check():
       async with get_session() as session:
           result = await session.execute(
               select(Source).where(Source.is_active == True)
           )
           sources = result.scalars().all()
           print(f"Активных источников: {len(sources)}")

   asyncio.run(check())
   EOF
   ```

3. **Отключить проблемный источник:**
   Через админ-панель бота: `🔧 Админ-панель → ⚙️ Источники новостей`

---

## 🎉 Итог

✅ **Успешно интегрированы все источники из Excel файла!**

Теперь бот будет собирать новости с **21 источника** вместо 10, охватывая:
- 🎓 Гранты и стипендии
- 🌍 Стажировки и программы обмена
- 📰 Новости образования Казахстана
- 🏛️ Официальные источники (МОН РК)
- 📚 Международные образовательные платформы

**Больше источников = больше контента для дайджестов = больше пользы для аудитории!** 🚀

---

**Дата интеграции:** 2026-02-03
**Автор:** Claude Sonnet 4.5 + Sayat
**Статус:** ✅ Реализовано и протестировано
