# Развертывание Tarot Bot

## Подготовка окружения

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/tarot-bot.git
cd tarot-bot
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл с переменными окружения:
```bash
cp .env.example .env
```

5. Отредактируйте `.env` файл, добавив необходимые токены:
```bash
# Telegram Bot Token
TELEGRAM_TOKEN=your_telegram_token

# YandexGPT Configuration
YANDEX_FOLDER_ID=your_folder_id
YANDEX_AUTH_TOKEN=your_auth_token

# Admin Configuration
ADMIN_USER_IDS=your_telegram_id
```

## Запуск бота через Screen

### Установка Screen

```bash
sudo apt-get update
sudo apt-get install screen
```

### Запуск бота

1. Создайте новую screen сессию:
```bash
screen -S tarot-bot
```

2. В открывшейся сессии запустите бота:
```bash
./run_bot.sh
```

3. Отключитесь от screen сессии (бот продолжит работать):
- Нажмите `Ctrl+A`, затем `D`

### Управление Screen сессией

```bash
# Посмотреть список сессий
screen -ls

# Подключиться к существующей сессии
screen -r tarot-bot

# Убить сессию (если нужно)
screen -X -S tarot-bot quit
```

### Автоматический перезапуск

Для автоматического перезапуска бота при перезагрузке сервера, добавьте в crontab:

```bash
crontab -e
```

Добавьте строку:
```
@reboot cd /path/to/tarot-bot && screen -dmS tarot-bot ./run_bot.sh
```

## Мониторинг

### Логи

Логи бота сохраняются в файлы:
- `bot.log` - основной лог бота
- `bot_manager.log` - лог процесса управления

### Проверка статуса

1. Подключитесь к screen сессии:
```bash
screen -r tarot-bot
```

2. Просмотр логов в реальном времени:
```bash
tail -f bot.log
```

## Обновление бота

1. Остановите бота:
```bash
screen -X -S tarot-bot quit
```

2. Обновите код:
```bash
git pull origin main
```

3. Обновите зависимости:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

4. Запустите бота снова:
```bash
screen -S tarot-bot ./run_bot.sh
```
