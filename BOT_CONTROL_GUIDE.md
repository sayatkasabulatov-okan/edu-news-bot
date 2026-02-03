# 🤖 Руководство по управлению ботом

## Проблема, которую решает bot_control.py

**Проблема:** Бот периодически переставал работать из-за запуска множества экземпляров одновременно. Telegram API не позволяет нескольким экземплярам бота работать одновременно (конфликт getUpdates).

**Решение:** Скрипт `bot_control.py` управляет жизненным циклом бота:
- ✅ Проверяет наличие запущенных процессов перед стартом
- ✅ Корректно останавливает все экземпляры
- ✅ Сохраняет PID в файл для отслеживания
- ✅ Логирует вывод бота в файлы
- ✅ Показывает статус и логи

---

## 📋 Доступные команды

### 1. Запустить бота
```bash
python3 bot_control.py start
```
**Что делает:**
- Проверяет, не запущен ли уже бот
- Запускает новый процесс
- Сохраняет PID в `bot.pid`
- Перенаправляет логи в файлы

**Вывод:**
```
🚀 Starting bot...
Waiting for bot to initialize...
✅ Bot started successfully (PID: 50377)
📝 PID saved to /Users/.../bot.pid
📋 Logs: /Users/.../logs/bot_stdout.log
📋 Errors: /Users/.../logs/bot_stderr.log
```

---

### 2. Остановить бота
```bash
python3 bot_control.py stop
```
**Что делает:**
- Находит все запущенные процессы бота
- Отправляет SIGTERM для корректной остановки
- Если процесс не останавливается за 5 секунд - принудительно убивает (SIGKILL)
- Удаляет PID файл

**Вывод:**
```
🛑 Stopping bot...
Found 1 running process(es): [50377]
  Sent SIGTERM to process 50377
  Process 50377 stopped gracefully
✅ All bot processes stopped
```

---

### 3. Перезапустить бота
```bash
python3 bot_control.py restart
```
**Что делает:**
- Останавливает все запущенные процессы (как `stop`)
- Ждёт 2 секунды
- Запускает бота заново (как `start`)

**Когда использовать:**
- После изменения кода
- После изменения `.env` файла
- Если бот "завис" или работает неправильно

---

### 4. Проверить статус
```bash
python3 bot_control.py status
```
**Что делает:**
- Показывает, запущен ли бот
- Показывает все активные процессы
- Проверяет валидность PID файла

**Вывод (бот работает):**
```
📊 Bot Status:
============================================================
Status: ✅ RUNNING
Active processes: 1
PIDs: [50377]

PID file: ✅ Valid
Saved PID: 50377
============================================================
```

**Вывод (бот не работает):**
```
📊 Bot Status:
============================================================
Status: ❌ NOT RUNNING

PID file: Not found
============================================================
```

---

### 5. Посмотреть логи (вывод)
```bash
python3 bot_control.py logs [количество строк]
```
**Примеры:**
```bash
# Последние 50 строк (по умолчанию)
python3 bot_control.py logs

# Последние 100 строк
python3 bot_control.py logs 100

# Последние 20 строк
python3 bot_control.py logs 20
```

**Что показывает:**
- Вывод бота (stdout)
- Информационные сообщения
- Статус запуска
- Работа schedulers

---

### 6. Посмотреть логи ошибок
```bash
python3 bot_control.py logs errors [количество строк]
```
**Примеры:**
```bash
# Последние 50 строк ошибок
python3 bot_control.py logs errors

# Последние 100 строк ошибок
python3 bot_control.py logs errors 100
```

**Что показывает:**
- Ошибки (stderr)
- Traceback
- Критические проблемы
- Причины падения бота

---

## 🔄 Типичные сценарии использования

### Сценарий 1: Первый запуск
```bash
# 1. Проверить, что ничего не запущено
python3 bot_control.py status

# 2. Запустить бота
python3 bot_control.py start

# 3. Проверить логи
python3 bot_control.py logs 30
```

---

### Сценарий 2: Бот перестал отвечать
```bash
# 1. Проверить статус
python3 bot_control.py status

# 2. Посмотреть ошибки
python3 bot_control.py logs errors

# 3. Перезапустить
python3 bot_control.py restart

# 4. Убедиться, что работает
python3 bot_control.py status
```

---

### Сценарий 3: Изменил код, нужно перезапустить
```bash
# Просто перезапусти
python3 bot_control.py restart
```

---

### Сценарий 4: Бот запустился, но сразу упал
```bash
# 1. Посмотреть ошибки
python3 bot_control.py logs errors 50

# 2. Исправить проблему в коде

# 3. Попробовать снова
python3 bot_control.py start
```

---

### Сценарий 5: Множественные экземпляры (конфликт)
```bash
# Скрипт автоматически найдёт и остановит все процессы
python3 bot_control.py stop

# Затем запусти заново
python3 bot_control.py start
```

---

## 📁 Файлы и их назначение

### `bot.pid`
- Сохраняет PID текущего запущенного процесса
- Автоматически создаётся при `start`
- Автоматически удаляется при `stop`

### `logs/bot_stdout.log`
- Стандартный вывод бота (stdout)
- Информационные сообщения
- Статус работы
- История запусков (с разделителем)

### `logs/bot_stderr.log`
- Ошибки (stderr)
- Traceback
- Предупреждения
- Критические проблемы

---

## ⚠️ Частые проблемы и решения

### Проблема 1: "Bot already running"
```
⚠️  Bot already running with PID(s): [50377]
Use 'restart' to restart or 'stop' to stop first
```
**Решение:**
```bash
python3 bot_control.py restart
```

---

### Проблема 2: "Conflict: terminated by other getUpdates request"
**Причина:** Где-то запущен другой экземпляр бота

**Решение:**
```bash
# Остановить все
python3 bot_control.py stop

# Убедиться, что остановлены
python3 bot_control.py status

# Запустить заново
python3 bot_control.py start
```

---

### Проблема 3: Bot started, но сразу Status: NOT RUNNING
**Причина:** Бот падает при запуске

**Решение:**
```bash
# Посмотреть ошибки
python3 bot_control.py logs errors 50

# Обычно проблемы:
# - Неверный токен в .env
# - База данных не запущена (docker-compose up -d postgres)
# - Отсутствуют зависимости (pip install -r requirements.txt)
# - Неправильный MODERATOR_CHAT_ID или CHANNEL_ID
```

---

### Проблема 4: PID file: Stale
**Причина:** PID файл существует, но процесс не запущен (бот упал)

**Решение:**
```bash
# Просто запустить заново (файл перезапишется)
python3 bot_control.py start
```

---

## 🎯 Почему это решает проблему множественных экземпляров

**До bot_control.py:**
- Запускали бота вручную: `python -m src.main &`
- Забывали остановить старый процесс
- Запускали новый → 2 экземпляра конфликтовали
- Telegram API возвращал ошибку Conflict
- Бот переставал работать

**С bot_control.py:**
1. При `start` - проверяется, нет ли уже запущенных процессов
2. Если есть - отказывается запускать (предлагает `restart`)
3. При `stop` - находит ВСЕ процессы и убивает их
4. При `restart` - гарантированно останавливает всё и запускает 1 новый процесс
5. PID файл хранит информацию о текущем процессе

**Результат:** Всегда работает максимум 1 экземпляр бота!

---

## 🚀 Быстрая шпаргалка

```bash
# Запустить
python3 bot_control.py start

# Остановить
python3 bot_control.py stop

# Перезапустить
python3 bot_control.py restart

# Статус
python3 bot_control.py status

# Логи (последние 50 строк)
python3 bot_control.py logs

# Ошибки (последние 50 строк)
python3 bot_control.py logs errors
```

---

## 💡 Рекомендации

1. **После изменения кода:** Всегда делай `restart`
2. **Перед выключением компьютера:** Делай `stop`
3. **Если бот не отвечает:** Сначала `status`, потом `logs errors`
4. **Проверка работы:** После каждого запуска делай `status` через 5 секунд
5. **Мониторинг:** Периодически смотри `logs` чтобы видеть, что бот работает

---

## ✅ Итог

`bot_control.py` - это твой единственный инструмент для управления ботом. Больше НЕ нужно:
- ❌ `python -m src.main &` - НЕ используй
- ❌ `ps aux | grep python` - НЕ нужно
- ❌ `kill -9 <PID>` - НЕ нужно
- ❌ Искать процессы вручную - НЕ нужно

**Используй только:**
- ✅ `python3 bot_control.py start`
- ✅ `python3 bot_control.py stop`
- ✅ `python3 bot_control.py restart`
- ✅ `python3 bot_control.py status`
- ✅ `python3 bot_control.py logs`

**Это гарантирует, что проблема множественных экземпляров больше не повторится!**
