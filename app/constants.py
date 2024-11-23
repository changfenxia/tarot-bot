"""Constants for the Tarot bot"""

import os
import logging

logger = logging.getLogger(__name__)

def parse_admin_ids():
    """Parse admin IDs from environment variable with detailed logging"""
    admin_ids_str = os.getenv('ADMIN_USER_IDS')
    logger.info(f"Raw admin IDs string: '{admin_ids_str}'")
    
    if admin_ids_str is None:
        logger.error("ADMIN_USER_IDS environment variable is not set")
        return []
    
    if not admin_ids_str.strip():
        logger.warning("ADMIN_USER_IDS is empty")
        return []
    
    try:
        # Split and clean the string
        id_strings = [id.strip() for id in admin_ids_str.split(',') if id.strip()]
        logger.info(f"Split admin ID strings: {id_strings}")
        
        # Convert to integers
        admin_ids = []
        for id_str in id_strings:
            try:
                admin_id = int(id_str)
                admin_ids.append(admin_id)
                logger.info(f"Successfully parsed admin ID: {admin_id}")
            except ValueError:
                logger.error(f"Failed to parse admin ID: '{id_str}'")
        
        logger.info(f"Final admin IDs list: {admin_ids}")
        return admin_ids
    except Exception as e:
        logger.error(f"Error parsing admin IDs: {e}")
        return []

# Admin user IDs (from environment variable)
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
