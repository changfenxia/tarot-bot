"""Constants for the Tarot bot"""

import os
import logging

logger = logging.getLogger(__name__)

def parse_admin_ids():
    """Parse admin user IDs from environment variable"""
    try:
        admin_ids_str = os.getenv('ADMIN_USER_IDS', '')
        if not admin_ids_str:
            logger.warning("ADMIN_USER_IDS environment variable is empty")
            return []

        # Split by comma and convert to integers
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(',') if id_str.strip()]
        logger.info(f"Parsed admin IDs: {admin_ids}")
        return admin_ids
    except Exception as e:
        logger.error(f"Error parsing admin IDs: {e}")
        return []

# Bot configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_USER_IDS = parse_admin_ids()
logger.info(f"Initialized ADMIN_USER_IDS: {ADMIN_USER_IDS}")

# Mapping of card names to their image files
TAROT_CARDS = {
    # Старшие арканы (22)
    "Шут": "fool.jpg",
    "Маг": "magician.jpg",
    "Верховная Жрица": "high_priestess.jpg",
    "Императрица": "empress.jpg",
    "Император": "emperor.jpg",
    "Иерофант": "hierophant.jpg",
    "Влюбленные": "lovers.jpg",
    "Колесница": "chariot.jpg",
    "Сила": "strength.jpg",
    "Отшельник": "hermit.jpg",
    "Колесо Фортуны": "wheel_of_fortune.jpg",
    "Справедливость": "justice.jpg",
    "Повешенный": "hanged_man.jpg",
    "Смерть": "death.jpg",
    "Умеренность": "temperance.jpg",
    "Дьявол": "devil.jpg",
    "Башня": "tower.jpg",
    "Звезда": "star.jpg",
    "Луна": "moon.jpg",
    "Солнце": "sun.jpg",
    "Суд": "judgement.jpg",
    "Мир": "world.jpg",

    # Младшие арканы (14)
    "Туз Кубков": "cups_ace.jpg",
    "Двойка Жезлов": "wands_two.jpg",
    "Тройка Мечей": "swords_three.jpg",
    "Четверка Пентаклей": "pentacles_four.jpg",
    "Пятерка Жезлов": "wands_five.jpg",
    "Шестерка Кубков": "cups_six.jpg",
    "Семерка Мечей": "swords_seven.jpg",
    "Восьмерка Пентаклей": "pentacles_eight.jpg",
    "Девятка Кубков": "cups_nine.jpg",
    "Десятка Жезлов": "wands_ten.jpg",
    "Паж Кубков": "cups_page.jpg",
    "Рыцарь Мечей": "swords_knight.jpg",
    "Королева Пентаклей": "pentacles_queen.jpg",
    "Король Жезлов": "wands_king.jpg"
}
