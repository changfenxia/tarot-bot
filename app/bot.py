import os
import logging
import asyncio
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from yandex_gpt import YandexGPTClient
import json
from pathlib import Path
import signal
import atexit
import fcntl
from constants import TAROT_CARDS
from database import Database
from messages import (
    WELCOME_MESSAGE, COOLDOWN_MESSAGE, READING_START,
    SECOND_CARD_INTRO, THIRD_CARD_INTRO,
    PAST_CARD, PRESENT_CARD, FUTURE_CARD,
    INTERPRETATION_START, CARDS_SILENT,
    MYSTICAL_POWERS_UNAVAILABLE, ORACLE_MEDITATION,
    CLOSING_MESSAGE, ERROR_MESSAGE
)

# Load environment variables
load_dotenv()

# Configure logging
log_file = Path(__file__).resolve().parent.parent / "bot.log"
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
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
        # Get the correct image filename from TAROT_CARDS dictionary
        if card_name not in TAROT_CARDS:
            logger.error(f"Card name not found in TAROT_CARDS: {card_name}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{position}\n(Invalid card name)"
            )
            return
            
        image_filename = TAROT_CARDS[card_name]
        
        # Try different possible paths
        possible_paths = [
            CARDS_DIR / image_filename,  # Absolute path
            Path(__file__).resolve().parent / "static" / "cards" / image_filename,  # Relative to bot.py
            Path("app/static/cards") / image_filename  # Project root relative
        ]
        
        image_path = None
        for path in possible_paths:
            if path.exists():
                image_path = path
                break
                
        if not image_path:
            logger.error(f"Card image file not found: {image_filename}. Tried paths: {possible_paths}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{position}\n(Image file not found)"
            )
            return

        logger.info(f"Sending card image from path: {image_path}")
        with open(image_path, 'rb') as image_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_file,
                caption=position
            )
    except Exception as e:
        logger.error(f"Error sending card image: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{position}\n(Error: {str(e)})"
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(WELCOME_MESSAGE)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and perform tarot reading."""
    user_id = update.effective_user.id
    question = update.message.text
    
    logger.info(f"Received message from user {user_id}: {question}")

    try:
        # Check cooldown
        logger.info(f"Checking cooldown for user {user_id}")
        if await db.is_on_cooldown(user_id, cooldown_seconds=60):
            logger.info(f"User {user_id} is on cooldown")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=COOLDOWN_MESSAGE
            )
            return

        # Update last request time
        logger.info(f"Updating last request time for user {user_id}")
        await db.update_last_request(user_id)

        # Generate three random cards
        cards = random.sample(list(TAROT_CARDS.keys()), 3)
        logger.info(f"Generated cards for user {user_id}: {cards}")

        # Initial message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=READING_START
        )

        # Send first card
        await send_card_image(update, context, cards[0], PAST_CARD.format(cards[0]))
        
        # Message before second card
        await asyncio.sleep(3)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=SECOND_CARD_INTRO
        )

        # Send second card
        await asyncio.sleep(3)
        await send_card_image(update, context, cards[1], PRESENT_CARD.format(cards[1]))

        # Message before third card
        await asyncio.sleep(3)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=THIRD_CARD_INTRO
        )

        # Send third card
        await asyncio.sleep(3)
        await send_card_image(update, context, cards[2], FUTURE_CARD.format(cards[2]))

        # Generate interpretation using YandexGPT
        if yandex_gpt:
            try:
                logger.info(f"Generating interpretation for user {user_id}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=INTERPRETATION_START
                )
                await asyncio.sleep(3)
                response = await yandex_gpt.generate_interpretation(cards, question)
                
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=response if response else CARDS_SILENT
                )
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=MYSTICAL_POWERS_UNAVAILABLE
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=ORACLE_MEDITATION
            )

        # Send closing message
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=CLOSING_MESSAGE
        )

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=ERROR_MESSAGE
        )

async def cleanup():
    """Cleanup resources before shutdown."""
    logger.info("Starting cleanup...")
    try:
        # Close database connection
        await db.close()
        logger.info("Database connection closed")
        
        # Release bot lock
        if bot_lock:
            bot_lock.release()
            logger.info("Bot lock released")
            
        # Additional cleanup tasks can be added here
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    finally:
        logger.info("Cleanup completed")

class TarotBot:
    def __init__(self):
        self.application = None
        self.running = False
        
    async def initialize(self):
        """Initialize bot components."""
        # Initialize database
        logger.info("Initializing database...")
        await db.init()
        logger.info("Database initialized successfully")

        # Create the Application
        logger.info("Creating Telegram application...")
        self.application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
    async def start(self):
        """Start the bot."""
        logger.info("Starting bot...")
        
        # Try to acquire lock
        global bot_lock
        bot_lock = BotLock(LOCK_FILE)
        if not bot_lock.acquire():
            logger.error("Another instance of the bot is already running")
            return

        try:
            await self.initialize()
            
            # Start the Bot
            logger.info("Starting bot polling...")
            self.running = True
            
            # Create a new event loop for the polling
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling()
                
                # Keep the bot running
                while self.running:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error during bot operation: {e}", exc_info=True)
                self.running = False
            finally:
                await self.application.updater.stop()
                await self.application.stop()
                loop.stop()
                loop.close()
                
        except Exception as e:
            logger.error(f"Critical error: {e}", exc_info=True)
        finally:
            await self.stop()
            
    async def stop(self):
        """Stop the bot and cleanup resources."""
        if self.running:
            logger.info("Stopping bot...")
            try:
                self.running = False
                if self.application:
                    if self.application.updater and self.application.updater.running:
                        await self.application.updater.stop()
                    await self.application.stop()
                await cleanup()
                logger.info("Bot stopped successfully")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            finally:
                if bot_lock:
                    bot_lock.release()

def run_bot():
    """Run the bot with proper asyncio handling."""
    bot = TarotBot()
    
    async def _run():
        try:
            await bot.start()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
        finally:
            await bot.stop()
    
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == '__main__':
    run_bot()
