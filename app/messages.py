# Bot messages

# Start command message
# Start command message
WELCOME_MESSAGE = (
    "🔮 Приветствую тебя в мире Таро! 🌟\n\n"
    "Я - мистический проводник в мир карт Таро. "
    "Просто напиши свой вопрос, и я проведу для тебя расклад.\n\n"
    "✨ Помни: карты Таро говорят с нами через символы и знаки. Будь открыт к их посланиям..."
)

# Reading process messages
READING_START = "🔮 Я начинаю раскладывать карты…. Древняя магия Таро откроет нам свои тайны…. "
SECOND_CARD_INTRO = "✨ Туман времени рассеивается…. Я вижу следующую карту…. "
THIRD_CARD_INTRO = "🌟 Последняя карта готова раскрыть свой секрет…. "

# Card position formats
PAST_CARD = "🕰 <b>Прошлое:</b> {}"
PRESENT_CARD = "⚡️ <b>Настоящее:</b> {}"
FUTURE_CARD = "🔮 <b>Будущее:</b> {}"

# YandexGPT related messages
INTERPRETATION_START = "🌟 Сейчас я погружаюсь в мистический транс... Карты шепчут свои тайны, и я готовлю для вас глубокое толкование... ✨"
CARDS_SILENT = "🔮 Карты хранят молчание..."
MYSTICAL_POWERS_UNAVAILABLE = "🌌 Мистические силы временно недоступны…. 🌌"
ORACLE_MEDITATION = "🌌 Оракул погрузился в глубокую медитацию…. 🌌"

# Admin help message
ADMIN_HELP_MESSAGE = """🛠 <b>Команды администратора:</b>

/stats - Показать статистику бота
/mode [test/prod] - Изменить режим работы
/cooldown [minutes] - Установить время ожидания

<b>Режимы работы:</b>
• test - Без ожидания между запросами
• prod - Стандартный режим с ожиданием"""

# Closing messages
CLOSING_MESSAGE = "🌙 Теперь картам нужен отдых…. ✨ Ты можешь вернуться позже за новым предсказанием 🔮"
ERROR_MESSAGE = "🌑 Силы Таро временно недоступны…. Попробуйте немного позже 🌑"

# Position messages
POSITION_MESSAGES = {
    0: "🎴 <b>Первая карта</b> - описывает текущую ситуацию",
    1: "🎴 <b>Вторая карта</b> - показывает препятствия или возможности",
    2: "🎴 <b>Третья карта</b> - предлагает решение или итог"
}

def escape_html(text: str) -> str:
    """Escape special characters for HTML."""
    special_chars = ['&', '<', '>', '"', "'"]
    for char in special_chars:
        text = text.replace(char, f'&{char};')
    return text

def get_cooldown_message(minutes: int) -> str:
    """Get cooldown message with remaining time"""
    if minutes >= 120:  # 2 hours or more
        hours = minutes // 60
        return f"🕐 Для следующего предсказания пока недостаточно магической энергии... Вернись через {hours} часа ✨"
    elif minutes >= 60:  # 1-2 hours
        return "🕐 Для следующего предсказания пока недостаточно магической энергии... Вернись через час ✨"
    else:  # Less than an hour
        return f"🕐 Для следующего предсказания пока недостаточно магической энергии... Вернись через {minutes} минут ✨"
