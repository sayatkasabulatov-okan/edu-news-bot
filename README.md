# Telegram Education News Bot

Telegram бот для автоматического мониторинга и публикации новостей об образовании за рубежом для казахстанских студентов.

## 🚀 Возможности

### Основной функционал
- 📰 **Автоматический парсинг** 10+ образовательных порталов
- 🤖 **AI-обработка контента** с помощью GPT-4
- 🎨 **Генерация изображений** через DALL-E
- ✏️ **Редактирование** перед публикацией
- 📅 **Планирование публикаций** (preset времена + custom)
- 🚀 **Моментальная публикация** в Telegram канал
- 📊 **Статистика и аналитика**
- 💾 **PostgreSQL** для хранения истории
- ⚙️ **Админ-панель** для управления настройками

### Режимы работы

#### 🔵 Режим индивидуальных статей (по умолчанию)
- Парсинг каждые **4 часа**
- Каждая статья обрабатывается отдельно
- Краткая выжимка (максимум 5 предложений)
- Немедленная отправка модератору
- Используется для оперативной публикации новостей

#### 🟢 Режим дайджестов (опционально)
- Парсинг раз в день (по умолчанию в 9:00)
- Накопление 5-6 статей
- Создание единого дайджеста
- Отправка модератору для проверки

## 📋 Архитектура

```
src/
├── bot/                    # Telegram бот и обработчики
│   ├── handlers/          # Обработчики команд и callback'ов
│   ├── keyboards/         # Inline клавиатуры
│   └── messages/          # Шаблоны сообщений
├── scraper/               # Модуль парсинга сайтов
│   ├── parsers/          # Парсеры для конкретных сайтов
│   └── scheduler.py      # Планировщик задач
├── ai/                    # AI обработка и создание выжимок
│   ├── summarizer.py     # OpenAI GPT-4 для суммаризации
│   ├── prompts.py        # Промпты для AI
│   └── image_generator.py # DALL-E для генерации изображений
├── database/              # Модели БД и репозитории
│   ├── models.py         # SQLAlchemy модели
│   └── repositories/     # Data access layer
├── services/              # Бизнес-логика
│   ├── article_post_service.py  # Обработка индивидуальных статей
│   ├── digest_service.py        # Создание дайджестов
│   └── post_service.py          # Публикация постов
└── utils/                 # Утилиты (логирование, мониторинг)
```

## 🛠 Требования

- Python 3.10+
- PostgreSQL 16+
- Telegram Bot Token
- OpenAI API Key (GPT-4 + DALL-E доступ)

## 📦 Установка

### 1. Клонирование и установка зависимостей

```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка базы данных

Запустить PostgreSQL через Docker:

```bash
docker-compose up -d postgres
```

Или установить PostgreSQL локально и создать базу данных:

```bash
createdb edu_news_bot
```

### 3. Настройка переменных окружения

Скопировать `.env.example` в `.env`:

```bash
cp .env.example .env
```

Заполнить переменные в `.env`:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
MODERATOR_CHAT_ID=your_telegram_user_id
CHANNEL_ID=your_channel_id

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=edu_news_bot
DB_USER=postgres
DB_PASSWORD=your_password

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview

# Article Mode Configuration (default)
SCRAPING_INTERVAL_HOURS=4         # Парсинг каждые 4 часа
ENABLE_ARTICLE_MODE=true          # Режим индивидуальных статей
ENABLE_DIGEST_MODE=false          # Режим дайджестов
MAX_ARTICLE_SUMMARY_SENTENCES=5   # Максимум предложений в выжимке
SEND_ARTICLES_IMMEDIATELY=true    # Отправлять статьи сразу

# Digest Mode Configuration (optional)
SCRAPING_SCHEDULE_HOUR=9          # Час парсинга для дайджестов
MIN_ARTICLES_FOR_DIGEST=5         # Минимум статей для дайджеста
MAX_ARTICLES_FOR_DIGEST=6         # Максимум статей для дайджеста

# Logging
LOG_LEVEL=INFO
```

### 4. Получение необходимых ID

#### Telegram Bot Token:
1. Открыть [@BotFather](https://t.me/botfather) в Telegram
2. Отправить `/newbot`
3. Следовать инструкциям
4. Скопировать токен

#### Moderator Chat ID (ваш ID):
1. Открыть [@userinfobot](https://t.me/userinfobot)
2. Скопировать ваш ID

#### Channel ID:
1. Создать канал в Telegram
2. Добавить бота как администратора канала
3. Отправить сообщение в канал
4. Открыть `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
5. Найти `chat` → `id` (будет отрицательное число)

### 5. Инициализация базы данных

```bash
python -m src.main
```

При первом запуске автоматически создадутся все таблицы.

## 🌐 Активные парсеры

Бот автоматически собирает новости из следующих источников:

- **Bolashak Foundation** - стипендии и гранты от Болашак
- **StudyQA** - образовательные возможности
- **EducationAbroad.kz** - обучение за рубежом
- **TopUniversities** - рейтинги и новости вузов
- **Opportunities Circle** - международные стипендии
- **Opportunities Corners** - образовательные программы
- **Bright Scholarship** - гранты на обучение
- **Global Scholarships** - мировые стипендии
- **Spubl** - образовательный контент
- **Generic Parser** - универсальный парсер для новых сайтов

Всего: **10+ активных парсеров**

## 🎮 Использование

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать работу с ботом (главное меню) |
| `/help` | Подробная справка по всем функциям |
| `/stats` | Статистика по дайджестам и публикациям |
| `/admin` | Админ-панель для настройки бота |
| `/collect` | Запустить парсинг вручную |
| `/health` | Проверить статус фоновых задач |

### Workflow (режим индивидуальных статей)

1. **Автоматический сбор**
   - Бот парсит источники каждые 4 часа
   - Проверяет релевантность статей с помощью AI
   - Сохраняет в базу данных

2. **Обработка статьи**
   - AI создает краткую выжимку (максимум 5 предложений)
   - Генерируется изображение через DALL-E (если нужно)
   - Создается пост с article_id

3. **Модерация**
   - Статья отправляется модератору с кнопками:
     - **✏️ Редактировать** - изменить текст
     - **🖼 Изображение** - сгенерировать новое
     - **📅 Запланировать** - выбрать время публикации
       - Завтра 10:00
       - Завтра 18:00
       - Послезавтра 10:00
       - Послезавтра 18:00
       - 📝 Ввести дату вручную
     - **✅ Опубликовать** - опубликовать сразу
     - **🔗 Оригинал статьи** - посмотреть источник
     - **❌ Отклонить** - отклонить статью

4. **Публикация**
   - Моментальная или по расписанию
   - Автоматически публикуется в канал
   - Поддержка изображений
   - Защита от дубликатов

### Workflow (режим дайджестов)

1. **Автоматический сбор**
   - Бот парсит источники раз в день (по умолчанию в 9:00)
   - Накапливает 5-6 релевантных статей

2. **Создание дайджеста**
   - AI создает единую выжимку из нескольких статей
   - Генерируется изображение для дайджеста

3. **Модерация**
   - Дайджест отправляется модератору с кнопками:
     - **✅ Утвердить** - одобрить дайджест
     - **❌ Отклонить** - отклонить дайджест
     - **✏️ Редактировать** - изменить текст
     - **🔄 Пересоздать** - создать заново
     - **🖼️ Новое фото** - сгенерировать другое изображение
     - **📅 Запланировать** - выбрать время
     - **🚀 Опубликовать** - опубликовать сразу

4. **Публикация**
   - После одобрения публикуется в канал

## 🗄 Структура базы данных

- **sources** - источники новостей (парсеры)
- **articles** - статьи с сайтов
- **digests** - AI-дайджесты из нескольких статей
- **posts** - опубликованные/запланированные посты
  - `digest_id` (nullable) - ссылка на дайджест
  - `article_id` (nullable) - ссылка на индивидуальную статью
- **post_revisions** - история редактирований
- **settings** - настройки бота

### Dual-mode архитектура

Пост может быть связан либо с `digest_id`, либо с `article_id`:
- **Digest post**: `post.digest_id != NULL`, `post.article_id == NULL`
- **Article post**: `post.digest_id == NULL`, `post.article_id != NULL`

## ⚙️ Админ-панель

Доступна по команде `/admin`. Позволяет настроить:

- **📚 Разделы образования** - выбрать категории контента
- **🌐 Источники** - включить/отключить парсеры
- **⏰ Время публикаций** - настроить расписание
- **🌍 Язык контента** - русский/казахский/английский
- **📏 Длина постов** - короткие/средние/длинные
- **🖼️ Изображения** - включить/отключить генерацию
- **🔍 Запустить ресерч** - ручной поиск статей
- **📜 История постов** - просмотр опубликованных
- **📊 Аналитика** - детальная статистика

## 📊 Логирование

Логи сохраняются в директории `logs/`:
- `bot_YYYY-MM-DD.log` - все логи
- `errors_YYYY-MM-DD.log` - только ошибки

Логи ротируются каждый день и хранятся 30 дней.

## 🔧 Добавление новых парсеров

### 1. Создать парсер

Скопировать `src/scraper/parsers/example_parser.py` и адаптировать:

```python
# src/scraper/parsers/my_parser.py
from src.scraper.base import BaseScraper

class MyParser(BaseScraper):
    def __init__(self):
        super().__init__(
            source_url="https://example.com/news",
            source_name="My Source"
        )

    async def fetch_articles(self):
        """Получить список статей"""
        # Реализовать парсинг списка
        pass

    async def parse_article(self, url):
        """Получить полный текст статьи"""
        # Реализовать парсинг статьи
        pass
```

### 2. Добавить источник в базу данных

```python
# scripts/add_source.py
import asyncio
from src.database.connection import get_session
from src.database.models import Source

async def add_my_source():
    async with get_session() as session:
        source = Source(
            name="My Source",
            url="https://example.com/news",
            parser_class="MyParser",
            is_active=True
        )
        session.add(source)
        await session.commit()

asyncio.run(add_my_source())
```

## 🚀 Запуск

```bash
python -m src.main
```

Или с помощью скрипта:

```bash
python src/main.py
```

## 🧪 Отладка и тестирование

### Тестирование парсера

```python
import asyncio
from src.scraper.parsers.bolashak_parser import BolashakParser

async def test():
    parser = BolashakParser()
    articles = await parser.fetch_articles()
    print(f"Found {len(articles)} articles")

    if articles:
        full_article = await parser.parse_article(articles[0]['url'])
        print(full_article)

asyncio.run(test())
```

### Тестирование AI (дайджест)

```python
import asyncio
from src.ai.summarizer import ContentSummarizer

async def test():
    summarizer = ContentSummarizer()
    articles = [
        {'title': 'Test 1', 'content': 'Content 1...'},
        {'title': 'Test 2', 'content': 'Content 2...'},
    ]
    digest = await summarizer.create_digest(articles)
    print(digest)

asyncio.run(test())
```

### Тестирование AI (индивидуальная статья)

```python
import asyncio
from src.ai.summarizer import ContentSummarizer

async def test():
    summarizer = ContentSummarizer()
    summary = await summarizer.summarize_single_article(
        article_title="Test Article",
        article_content="Full content here...",
        article_url="https://example.com/article"
    )
    print(summary)

asyncio.run(test())
```

### Проверка подключения к БД

```python
import asyncio
from src.database.connection import get_session
from src.database.models import Source
from sqlalchemy import select

async def test():
    async with get_session() as session:
        result = await session.execute(select(Source))
        sources = result.scalars().all()
        print(f"Found {len(sources)} sources")

asyncio.run(test())
```

### Проверка статуса фоновых задач

```bash
# В Telegram боте
/health
```

Покажет статус всех фоновых задач:
- Последний запуск
- Статус (успешно/ошибка)
- Количество обработанных статей

## ❗ Устранение проблем

### Бот не получает обновления
- Проверить токен бота
- Убедиться, что бот не запущен в другом месте
- Проверить, что бот добавлен в канал как администратор

### Ошибка подключения к БД
- Проверить, что PostgreSQL запущен (`docker ps` или `systemctl status postgresql`)
- Проверить параметры подключения в `.env`
- Проверить права доступа пользователя БД

### AI не создает выжимки
- Проверить OpenAI API ключ
- Проверить баланс на аккаунте OpenAI
- Убедиться, что модель доступна (`gpt-4-turbo-preview`)

### DALL-E не генерирует изображения
- Проверить, что у API ключа есть доступ к DALL-E
- Проверить настройки в админ-панели (`/admin` → Images)

### Бот не отправляет сообщения
- Убедиться, что `MODERATOR_CHAT_ID` правильный
- Начать диалог с ботом (`/start`)
- Проверить, что бот не заблокирован

### Парсеры не находят статьи
- Проверить, что CSS-селекторы актуальны
- Сайты могли изменить структуру
- Использовать `/collect` для тестирования

### Бот работает только когда компьютер включен
- Это нормально для локального запуска
- Для 24/7 работы нужен VPS или облачный хостинг:
  - **VPS** (DigitalOcean, Vultr, Hetzner)
  - **Railway.app** (простой деплой)
  - **Render.com** (бесплатный tier)

## 🔄 Расширение функционала

### Добавление новых команд

Добавить обработчик в `src/bot/handlers/commands.py`:

```python
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("My response")
```

Зарегистрировать в `src/bot/app.py`:

```python
app.add_handler(CommandHandler("mycommand", commands.my_command))
```

### Добавление webhook (для продакшена)

Изменить `src/main.py`:

```python
# Вместо run_polling()
await bot_app.run_webhook(
    listen="0.0.0.0",
    port=8443,
    url_path=settings.TELEGRAM_BOT_TOKEN,
    webhook_url=f"https://yourdomain.com/{settings.TELEGRAM_BOT_TOKEN}"
)
```

### Переключение между режимами

В `.env` изменить:

```env
# Для режима индивидуальных статей
ENABLE_ARTICLE_MODE=true
ENABLE_DIGEST_MODE=false
SCRAPING_INTERVAL_HOURS=4

# Для режима дайджестов
ENABLE_ARTICLE_MODE=false
ENABLE_DIGEST_MODE=true
SCRAPING_SCHEDULE_HOUR=9

# Для обоих режимов одновременно
ENABLE_ARTICLE_MODE=true
ENABLE_DIGEST_MODE=true
```

## 🎯 Ключевые особенности

### Защита от дубликатов
- Проверка URL при парсинге
- Предотвращение повторной публикации
- Информативное сообщение со ссылкой на оригинал

### AI Quality Control
- Проверка релевантности статей перед сохранением
- Краткие и информативные выжимки (без мотивационных фраз)
- Контроль качества контента

### Retry механизмы
- Автоматические повторные попытки при ошибках парсинга
- Graceful fallback при недоступности сервисов
- Подробное логирование для отладки

### Мониторинг
- Task monitor для отслеживания фоновых задач
- Health check endpoint (`/health`)
- Детальные логи всех операций

## 📝 Лицензия

MIT

## 💬 Поддержка

По вопросам обращаться к разработчику проекта.

---

**Версия**: 2.0
**Последнее обновление**: 2026-02-03
**Режим по умолчанию**: Индивидуальные статьи (каждые 4 часа)
