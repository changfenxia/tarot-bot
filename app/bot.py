import os
import logging
import asyncio
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from jinja2 import Environment, FileSystemLoader
from yandex_gpt import YandexGPTClient
import json
from pathlib import Path
import signal
import atexit
import fcntl
from constants import TAROT_CARDS
from database import Database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configure paths
BASE_DIR = Path(__file__).resolve().parent.parent
CARDS_DIR = Path(__file__).resolve().parent / "static" / "cards"
LOCK_FILE = BASE_DIR / "bot.lock"
DB_PATH = BASE_DIR / "data" / "tarot.db"

# Initialize Database
db = Database(str(DB_PATH))

# Initialize YandexGPT client
try:
    yandex_gpt = YandexGPTClient()
except Exception as e:
    logger.error(f"Failed to initialize YandexGPT: {e}")
    yandex_gpt = None

# Initialize Jinja2
env = Environment(loader=FileSystemLoader('app/templates'))

class BotLock:
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.lock_fd = None

    def acquire(self):
        try:
            # Open or create lock file
            self.lock_fd = open(self.lock_file, 'w')
            # Try to acquire exclusive lock
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            return True
        except (IOError, OSError):
            if self.lock_fd:
                self.lock_fd.close()
            return False

    def release(self):
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                if os.path.exists(self.lock_file):
                    os.unlink(self.lock_file)
            except (IOError, OSError) as e:
                logging.error(f"Error releasing lock: {e}")

async def send_card_image(update: Update, context: ContextTypes.DEFAULT_TYPE, card_name: str, position: str):
    """Send a card image with its position."""
    try:
        image_path = CARDS_DIR / TAROT_CARDS.get(card_name, '')
        if not image_path.exists():
            logger.warning(f"Image not found for card: {card_name}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f" {position}: {card_name} "
            )
        else:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_path.open('rb'),
                caption=f" {position}: {card_name} "
            )
    except Exception as e:
        logger.error(f"Error sending card image: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f" {position}: {card_name} "
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    welcome_message = (
        " Приветствую тебя в мире Таро! \n\n"
        "Я - мистический проводник в мир карт Таро. "
        "Просто напиши свой вопрос, и я проведу для тебя расклад.\n\n"
        " : карты Таро говорят с нами через символы и знаки. "
        "Будь открыт к их посланиям..."
    )
    
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and perform tarot reading."""
    user_id = update.effective_user.id
    question = update.message.text

    try:
        # Check cooldown
        if await db.is_on_cooldown(user_id):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=" Для следующего предсказания пока недостаточно магической энергии... Вернись позже "
            )
            return

        # Update last request time
        await db.update_last_request(user_id)

        # Generate three random cards
        cards = random.sample(list(TAROT_CARDS.keys()), 3)
        logger = logging.getLogger(__name__)
        logger.info(f"Generated cards for user {user_id}: {cards}")

        # Initial message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=" Я начинаю раскладывать карты... Древняя магия Таро откроет нам свои тайны..."
        )

        # Send first card
        await send_card_image(update, context, cards[0], "Прошлое ")
        
        # Message before second card
        await asyncio.sleep(3)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=" Туман времени рассеивается... Я вижу следующую карту..."
        )

        # Send second card
        await asyncio.sleep(3)
        await send_card_image(update, context, cards[1], "Настоящее ")

        # Message before third card
        await asyncio.sleep(3)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=" Последняя карта готова раскрыть свой секрет..."
        )

        # Send third card
        await asyncio.sleep(3)
        await send_card_image(update, context, cards[2], "Будущее ")

        # Generate interpretation using YandexGPT
        if yandex_gpt:
            try:
                logger.info(f"Generating interpretation for user {user_id}")
                # Добавляем мистическое сообщение перед толкованием
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=" Сейчас я погружаюсь в мистический транс... Карты шепчут свои тайны, и я готовлю для вас глубокое толкование... "
                )
                await asyncio.sleep(3)
                response = await yandex_gpt.generate_interpretation(cards, question)
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=response if response else " Карты хранят молчание..."
                )
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=" Мистические силы временно недоступны... "
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=" Оракул погрузился в глубокую медитацию... "
            )

        # Send closing message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=" Теперь картам нужен отдых... Ты можешь вернуться завтра за новым предсказанием "
        )

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error handling message: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=" Силы Таро временно недоступны... Попробуйте немного позже "
        )

async def cleanup():
    """Cleanup function to be called before shutdown"""
    logger = logging.getLogger(__name__)
    logger.info("Cleaning up before shutdown...")
    try:
        # Close Database connection
        db.close()
        # Release lock
        bot_lock.release()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def main():
    """Start the bot."""
    # Try to acquire lock
    global bot_lock
    bot_lock = BotLock(LOCK_FILE)
    if not bot_lock.acquire():
        logger.error("Another instance of the bot is already running")
        return

    # Register cleanup on normal exit
    atexit.register(lambda: asyncio.run(cleanup()))

    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(cleanup()))

    try:
        # Start the Bot
        application.run_polling(stop_signals=(signal.SIGINT, signal.SIGTERM))
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        asyncio.run(cleanup())
    finally:
        loop.close()

if __name__ == '__main__':
    main()
