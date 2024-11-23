# Tarot Bot 🔮

Telegram бот для гадания на картах Таро с использованием YandexGPT для мистической интерпретации расклада.

## ✨ Функциональность

- Случайный выбор 3 карт Таро для расклада "Прошлое-Настоящее-Будущее"
- Глубокая интерпретация расклада с помощью YandexGPT
- Отправка красивых изображений карт
- Ограничение на использование (1 минута между запросами)
- Сохранение истории запросов в SQLite

## 📥 Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/tarot-bot.git
   cd tarot-bot
   ```

2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python -m venv venv
   source venv/bin/activate  # для Linux/macOS
   # или
   .\venv\Scripts\activate  # для Windows
   pip install -r requirements.txt
   ```

3. Скопируйте `.env.example` в `.env` и заполните необходимые значения:
   ```
   TELEGRAM_TOKEN=your_telegram_bot_token
   YANDEX_FOLDER_ID=your_yandex_folder_id
   YANDEX_AUTH_TOKEN=your_yandex_auth_token
   ```

## 🚀 Запуск

Используйте скрипт управления для запуска/остановки бота:

```bash
# Запуск бота
python manage.py start

# Остановка бота
python manage.py stop

# Перезапуск бота
python manage.py restart

# Проверка статуса
python manage.py status
```

## 📁 Структура проекта

```
tarot-bot/
├── app/
│   ├── bot.py         # Основной файл бота
│   ├── yandex_gpt.py  # Интеграция с YandexGPT
│   ├── database.py    # Работа с SQLite
│   ├── messages.py    # Текстовые сообщения
│   ├── constants.py   # Константы и конфигурация
│   └── static/
│       └── cards/     # Изображения карт
├── data/
│   └── tarot.db      # База данных SQLite
├── manage.py         # Скрипт управления ботом
├── requirements.txt  # Зависимости проекта
└── .env             # Конфигурация
```

## 🎯 Использование

1. Начните чат с ботом командой `/start`
2. Отправьте боту свой вопрос
3. Получите расклад из трех карт с мистической интерпретацией
4. Соблюдайте минутную паузу между запросами

## ⚙️ Технические требования

- Python 3.8+
- Доступ к API YandexGPT
- Telegram Bot Token

## 📝 Примечание

Бот использует:
- `python-telegram-bot` для взаимодействия с Telegram API
- YandexGPT для генерации мистических интерпретаций
- SQLite для хранения данных
- Асинхронное программирование для эффективной обработки запросов

## 🔒 Безопасность

- Все чувствительные данные хранятся в файле `.env`
- База данных SQLite используется для защиты от спама
- Реализована система блокировки для предотвращения параллельных запусков бота
