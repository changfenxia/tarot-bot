import os
import re

def get_card_name(filename):
    # Extract the card name from DALL-E filename
    match = re.search(r"'([^']+)'", filename)
    if match:
        card_name = match.group(1)
        
        # Major Arcana
        major_arcana = {
            "The Fool": "fool",
            "The Magician": "magician",
            "The High Priestess": "high_priestess",
            "The Empress": "empress",
            "The Emperor": "emperor",
            "The Hierophant": "hierophant",
            "The Lovers": "lovers",
            "The Chariot": "chariot",
            "Strength": "strength",
            "The Hermit": "hermit",
            "The Wheel of Fortune": "wheel_of_fortune",
            "Justice": "justice",
            "The Hanged Man": "hanged_man",
            "Death": "death",
            "Temperance": "temperance",
            "The Devil": "devil",
            "The Tower": "tower",
            "The Star": "star",
            "The Moon": "moon",
            "The Sun": "sun",
            "Judgement": "judgement",
            "The World": "world"
        }
        
        # Check Major Arcana first
        for old_name, new_name in major_arcana.items():
            if card_name.startswith(old_name):
                return f"{new_name}.jpg"
        
        # Minor Arcana
        match = re.match(r"(\w+) of (\w+)", card_name)
        if match:
            number, suit = match.groups()
            number = number.lower()
            suit = suit.lower()
            
            # Convert number words to digits or court card names
            number_map = {
                "ace": "ace",
                "two": "two",
                "three": "three",
                "four": "four",
                "five": "five",
                "six": "six",
                "seven": "seven",
                "eight": "eight",
                "nine": "nine",
                "ten": "ten",
                "page": "page",
                "knight": "knight",
                "queen": "queen",
                "king": "king"
            }
            
            if number.lower() in number_map:
                return f"{suit}_{number_map[number.lower()]}.jpg"
    
    return None

def rename_cards():
    cards_dir = "/Users/artlvr/Documents/Apps/windsurf/tarot-bot/app/static/cards"
    
    for filename in os.listdir(cards_dir):
        if filename.startswith("DALL·E"):
            old_path = os.path.join(cards_dir, filename)
            new_name = get_card_name(filename)
            
            if new_name:
                new_path = os.path.join(cards_dir, new_name)
                print(f"Renaming: {filename} -> {new_name}")
                os.rename(old_path, new_path)
            else:
                print(f"Could not determine new name for: {filename}")

if __name__ == "__main__":
    rename_cards()
