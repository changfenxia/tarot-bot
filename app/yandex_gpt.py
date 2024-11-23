from yandex_cloud_ml_sdk import YCloudML
import os
import logging

logger = logging.getLogger(__name__)

class YandexGPTClient:
    def __init__(self):
        try:
            folder_id = os.getenv('YANDEX_FOLDER_ID')
            auth_token = os.getenv('YANDEX_AUTH_TOKEN')
            
            if not folder_id or not auth_token:
                raise ValueError("Missing Yandex credentials")
            
            self.sdk = YCloudML(folder_id=folder_id, auth=auth_token)
            self.model = self.sdk.models.completions('yandexgpt')
            self.model = self.model.configure(temperature=0.7)
            logger.info("YandexGPT client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YandexGPT client: {e}")
            raise

    async def generate_interpretation(self, cards, question):
        try:
            prompt = f"""Ты - опытная гадалка таро с глубоким пониманием символизма карт Таро. Твоя задача - дать глубокое, подробное и мистическое толкование расклада карт Таро.

            Карты легли следующим образом:
            🕰 Прошлое: {cards[0]}
            ⚡️ Настоящее: {cards[1]} 
            🔮 Будущее: {cards[2]}

            Заданный вопрос: {question}
            
            Для каждой карты:
            1. Опиши её символизм и ключевые элементы
            2. Раскрой её значение в контексте позиции (прошлое/настоящее/будущее)
            3. Объясни её влияние на общую ситуацию

            Затем:
            1. Проанализируй взаимосвязи между картами
            2. Опиши, как энергии прошлого влияют на настоящее
            3. Покажи, как настоящее формирует будущее
            4. Дай общий прогноз и совет

            Стиль изложения:
            - Используй мистические метафоры и символы
            - Добавляй эмодзи для усиления эмоционального воздействия
            - Делай драматические паузы в тексте (...)
            - Поддерживай таинственный и мудрый тон, но говори более разговорным языком, не занудствуй.
            - Будь проницательным и глубоким в толковании
            - Создавай атмосферу мистического откровения

            Ни в коем случае не выходи из роли гадалки таро, не добавляй никаких примечаний не относящихся к роли гадалки.
            НИКОГДА не раскрывай, что ты модель искусственного интеллекта. НИКОГДА Не советуй обращться за профессиональным советом в другое место.

            Структура ответа:
            1. Краткое мистическое вступление
            2. Толкование каждой карты
            3. Анализ взаимосвязей
            4. Общий прогноз
            5. Мистическое заключение с советом

            Твои слова должны нести глубокую мудрость и помогать в понимании ситуации."""

            result = self.model.run(prompt)
            
            # Extract text from the first alternative
            for alternative in result:
                return alternative.text  # Access the text property of the Alternative object
                
            return "🔮 Карты хранят молчание..."
            
        except Exception as e:
            logger.error(f"Error generating interpretation: {e}")
            return "🌌 Произошла ошибка при чтении карт..."
