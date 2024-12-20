import os
import logging
import random
import asyncio
import aiosqlite
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / 'bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables before importing constants
env_path = Path(__file__).parent.parent / '.env'
logger.info(f"Loading environment variables from: {env_path}")
load_dotenv(env_path)

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from yandex_gpt import YandexGPTClient
import json
import signal
import atexit
import fcntl
from constants import TAROT_CARDS, ADMIN_USER_IDS
from database import Database
from messages import (
    WELCOME_MESSAGE, READING_START,
    SECOND_CARD_INTRO, THIRD_CARD_INTRO,
    PAST_CARD, PRESENT_CARD, FUTURE_CARD,
    INTERPRETATION_START, CARDS_SILENT,
    MYSTICAL_POWERS_UNAVAILABLE, ORACLE_MEDITATION,
    CLOSING_MESSAGE, ERROR_MESSAGE, get_cooldown_message,
    escape_html
)

# Configure paths
BASE_DIR = Path(__file__).resolve().parent.parent
CARDS_DIR = (Path(__file__).resolve().parent / "static" / "cards").resolve()
logger.info(f"Initialized CARDS_DIR as: {CARDS_DIR}")
logger.info(f"CARDS_DIR exists: {CARDS_DIR.exists()}")
if CARDS_DIR.exists():
    logger.info(f"Found card images: {list(CARDS_DIR.glob('*.jpg'))}")
else:
    logger.error(f"CARDS_DIR does not exist: {CARDS_DIR}")
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
    """Send a card image followed by its description."""
    try:
        # Get the correct image filename from TAROT_CARDS dictionary
        if card_name not in TAROT_CARDS:
            logger.error(f"Card name not found in TAROT_CARDS: {card_name}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{position}\n(Invalid card name)",
                parse_mode=ParseMode.HTML
            )
            return
            
        image_filename = TAROT_CARDS[card_name]
        logger.info(f"Looking for image file: {image_filename}")
        
        image_path = CARDS_DIR / image_filename
        logger.info(f"Full image path: {image_path}")
        
        if not image_path.exists():
            logger.error(f"Card image file not found: {image_path}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"{position}\n(Image file not found)",
                parse_mode=ParseMode.HTML
            )
            return

        logger.info(f"Sending card image from path: {image_path}")
        # First send just the image
        with open(image_path, 'rb') as image_file:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_file
            )
        
        # Then send the description
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=position,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error sending card image: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{position}\n(Error: {str(e)})",
            parse_mode=ParseMode.HTML
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode=ParseMode.HTML
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - show bot statistics (admin only)"""
    user_id = update.effective_user.id
    logger.info(f"Stats command requested by user {user_id} (type: {type(user_id)})")
    logger.info(f"Current admin IDs: {ADMIN_USER_IDS} (types: {[type(aid) for aid in ADMIN_USER_IDS]})")
    
    try:
        if not ADMIN_USER_IDS:
            logger.warning("Admin IDs list is empty!")
            await update.message.reply_text(
                "Список администраторов пуст. Обратитесь к разработчику бота.",
                parse_mode=ParseMode.HTML
            )
            return
            
        if user_id not in ADMIN_USER_IDS:
            logger.warning(f"Access denied for user {user_id} - not in admin list {ADMIN_USER_IDS}")
            await update.message.reply_text(
                "Эта команда доступна только администраторам бота.",
                parse_mode=ParseMode.HTML
            )
            return
        
        logger.info(f"Access granted for admin {user_id}")
        # Get days parameter if provided
        try:
            days = int(context.args[0]) if context.args else 7
        except (ValueError, IndexError):
            days = 7
        
        stats = await db.get_user_stats(days)
        if not stats:
            await update.message.reply_text(
                "Не удалось получить статистику.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Format statistics message
        message = f"Статистика бота за {stats['period_days']} дней:\n\n"
        message += f"Всего запросов: {stats['total_requests']}\n"
        message += f"Уникальных пользователей: {stats['unique_users']}\n"
        message += f"Успешных запросов: {stats['successful_requests']}\n"
        message += f"Неудачных запросов: {stats['failed_requests']}\n\n"
        
        if stats['top_users']:
            message += "*Самые активные пользователи:*\n"
            for username, count in stats['top_users']:
                message += f"- {username}: {count} запросов\n"
            message += "\n"
        
        if stats['top_questions']:
            message += "*Популярные вопросы:*\n"
            for question, count in stats['top_questions']:
                # Truncate long questions
                short_q = question[:50] + "..." if len(question) > 50 else question
                message += f"- {short_q} ({count} раз)\n"
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        logger.error(f"Error during stats command: {e}")
        await update.message.reply_text(
            "Ошибка при получении статистики.",
            parse_mode=ParseMode.HTML
        )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user their Telegram ID"""
    user = update.effective_user
    message = f"Your Telegram info:\nID: {user.id}"
    if user.username:
        message += f"\nUsername: @{user.username}"
    if user.first_name:
        message += f"\nFirst Name: {user.first_name}"
    if user.last_name:
        message += f"\nLast Name: {user.last_name}"
    
    await update.message.reply_text(message)

async def set_cooldown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set cooldown duration in minutes (admin only)"""
    user_id = update.effective_user.id
    logger.info(f"Set cooldown command from user {user_id}")

    if user_id not in ADMIN_USER_IDS:
        logger.warning(f"Unauthorized access attempt to set_cooldown by user {user_id}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="У вас нет прав для использования этой команды.",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        # Check if minutes parameter is provided
        if not context.args or not context.args[0].isdigit():
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Пожалуйста, укажите время ожидания в минутах.\n"
                     "Пример: /set_cooldown 1440",
                parse_mode=ParseMode.HTML
            )
            return

        minutes = int(context.args[0])
        if minutes < 1:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Время ожидания должно быть не менее 1 минуты.",
                parse_mode=ParseMode.HTML
            )
            return

        # Update cooldown in database
        if await db.set_cooldown_minutes(minutes, user_id):
            human_readable = (
                f"{minutes} минут" if minutes >= 5 
                else f"{minutes} минуты" if 2 <= minutes <= 4 
                else "минуту"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Время ожидания между предсказаниями установлено: {human_readable}.",
                parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Не удалось обновить время ожидания. Попробуйте позже.",
                parse_mode=ParseMode.HTML
            )

    except Exception as e:
        logger.error(f"Error in set_cooldown command: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при обновлении времени ожидания.",
            parse_mode=ParseMode.HTML
        )

async def switch_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle between test and normal mode."""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_USER_IDS:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=MYSTICAL_POWERS_UNAVAILABLE,
            parse_mode=ParseMode.HTML
        )
        return

    mode = await db.is_test_mode()
    new_mode = not mode
    
    await db.set_test_mode(new_mode, user_id)
    
    mode_str = "тестовый" if new_mode else "нормальный"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Режим работы изменен на: {mode_str}",
        parse_mode=ParseMode.HTML
    )
    logger.info(f"Bot mode changed to: {mode_str} by admin {user_id}")

def convert_markdown_to_html(text):
    """Convert markdown bold syntax to HTML bold tags."""
    import re
    # Replace markdown bold (**text**) with HTML bold (<b>text</b>)
    return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages and perform tarot reading."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "No username"
    question = update.message.text
    
    logger.info(f"Received message from user {user_id} (@{username}): {question}")

    try:
        # Check cooldown
        logger.info(f"Checking cooldown for user {user_id} (@{username})")
        is_cooldown, remaining_minutes = await db.is_on_cooldown(user_id)
        if is_cooldown:
            logger.info(f"User {user_id} (@{username}) is on cooldown, {remaining_minutes} minutes remaining")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=get_cooldown_message(remaining_minutes),
                parse_mode=ParseMode.HTML
            )
            return

        # Update last request time
        logger.info(f"Updating last request time for user {user_id} (@{username})")
        await db.update_last_request(user_id)

        # Draw cards
        try:
            logger.info(f"Drawing cards from TAROT_CARDS for user {user_id} (@{username})")
            cards = random.sample(list(TAROT_CARDS.keys()), 3)
            logger.info(f"Successfully drew cards for user {user_id} (@{username}): {cards}")
        except Exception as e:
            logger.error(f"Error drawing cards for user {user_id} (@{username}): {e}")
            raise
        
        try:
            # Send initial message
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=READING_START,
                parse_mode=ParseMode.HTML
            )
            await asyncio.sleep(2)
            
            # Send first card
            first_card_text = PAST_CARD.format(escape_html(cards[0]))
            await send_card_image(update, context, cards[0], first_card_text)
            await asyncio.sleep(2)
            
            # Send second card
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=SECOND_CARD_INTRO,
                parse_mode=ParseMode.HTML
            )
            await asyncio.sleep(1)
            second_card_text = PRESENT_CARD.format(escape_html(cards[1]))
            await send_card_image(update, context, cards[1], second_card_text)
            await asyncio.sleep(2)
            
            # Send third card
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=THIRD_CARD_INTRO,
                parse_mode=ParseMode.HTML
            )
            await asyncio.sleep(1)
            third_card_text = FUTURE_CARD.format(escape_html(cards[2]))
            await send_card_image(update, context, cards[2], third_card_text)
            await asyncio.sleep(2)
            
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=INTERPRETATION_START,
                    parse_mode=ParseMode.HTML
                )
                await asyncio.sleep(3)
                
                # Check test mode only for admin users
                is_test = await db.is_test_mode() and user_id in ADMIN_USER_IDS
                
                if is_test:
                    logger.info(f"Test mode active for admin {user_id} (@{username}), skipping YandexGPT request")
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Тестовый режим активен. Интерпретация карт отключена.",
                        parse_mode=ParseMode.HTML
                    )
                else:
                    response = await yandex_gpt.generate_interpretation(cards, question)
                    # Log successful request
                    await db.log_request(
                        user_id=user_id,
                        username=username,
                        question=question,
                        cards=cards,
                        success=True
                    )
                    logger.info(f"Successful request from user {user_id} (@{username}) with question: {question}")
                    # Escape special characters in the response
                    interpretation = convert_markdown_to_html(escape_html(response if response else CARDS_SILENT))
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=interpretation,
                        parse_mode=ParseMode.HTML
                    )
            except Exception as e:
                logger.error(f"Error handling message for user {user_id} (@{username}): {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=MYSTICAL_POWERS_UNAVAILABLE,
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            logger.error(f"Error handling message for user {user_id} (@{username}): {e}")
            # Log failed request
            await db.log_request(
                user_id=user_id,
                username=username,
                question=question,
                cards=[],
                success=False
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=ERROR_MESSAGE,
                parse_mode=ParseMode.HTML
            )

    except Exception as e:
        logger.error(f"Error handling message for user {user_id} (@{username}): {e}")
        # Log failed request
        await db.log_request(
            user_id=user_id,
            username=username,
            question=question,
            cards=[],
            success=False
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=ERROR_MESSAGE,
            parse_mode=ParseMode.HTML
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
        if self.application:
            return

        self.application = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
        
        # Initialize handlers
        self.application.add_handler(CommandHandler("start", start))
        self.application.add_handler(CommandHandler("stats", stats_command))
        self.application.add_handler(CommandHandler("id", id_command))
        self.application.add_handler(CommandHandler("set_cooldown", set_cooldown_command))
        self.application.add_handler(CommandHandler("switch_mode", switch_mode_command))
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
