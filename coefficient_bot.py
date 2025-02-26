import os
import re
import logging
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Telethon-клиента
client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Храним последние 100 сообщений
chat_messages = []

async def fetch_old_messages():
    """Загружает последние 100 сообщений из чата."""
    async for message in client.iter_messages(CHAT_ID, limit=100):
        if message.text:
            process_message(message.text, message.date.strftime("%d.%m.%Y"))

def process_message(message_text, message_date):
    """Обрабатывает сообщение и отправляет результат в чат."""
    pattern = r"(Дух|Олимп|Техно):?\s*(\d+\.\d+)"
    matches = re.findall(pattern, message_text)

    if matches:
        for match in matches:
            place, coefficient = match
            result = f"{message_date} {place} {coefficient}"
            client.loop.create_task(client.send_message(CHAT_ID, result))
            logger.info(f"Sent message: {result}")

    chat_messages.append((message_date, message_text))
    if len(chat_messages) > 100:
        chat_messages.pop(0)

# Обработчик новых сообщений
@client.on(events.NewMessage(chats=CHAT_ID))
async def handler(event):
    message_text = event.message.text
    message_date = event.message.date.strftime("%d.%m.%Y")
    process_message(message_text, message_date)

async def main():
    """Основная функция запуска бота."""
    logger.info("Fetching old messages...")
    await fetch_old_messages()
    logger.info("Bot started. Listening for new messages...")
    await client.run_until_disconnected()

# Запуск бота
if __name__ == "__main__":
    client.loop.run_until_complete(main())
