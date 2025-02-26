import os
import re
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler
from dotenv import load_dotenv
import asyncio
import nest_asyncio

# Разрешаем повторное использование event loop (фикс для Windows)
nest_asyncio.apply()

# Загружаем переменные окружения
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Клавиатура с кнопкой
KEYBOARD = ReplyKeyboardMarkup([["/request_coefficients"]], resize_keyboard=True)

# Храним последние 100 сообщений с датами
chat_messages = []

# Функция обработки команды /start
async def start(update: Update, context: CallbackContext) -> None:
    logger.info(f"Received /start from {update.message.chat_id}")
    await update.message.reply_text("Привет! Нажми '/request_coefficients', чтобы получить последние данные.", reply_markup=KEYBOARD)

# Функция обработки текстовых сообщений с коэффициентами
async def process_chat_message(update: Update, context: CallbackContext) -> None:
    try:
        message_text = update.message.text
        message_date = update.message.date.strftime("%d.%m.%Y")
        logger.info(f"Received message: {message_text} on {message_date}")

        # Ищем коэффициенты в сообщении
        pattern = r"(Дух|Олимп|Техно):?\s*(\d+\.\d+)"
        matches = re.findall(pattern, message_text)

        # Если нашли коэффициенты, отправляем их в другой чат
        if matches:
            for match in matches:
                place, coefficient = match
                result = f"{message_date} {place} {coefficient}"
                await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=result)
                logger.info(f"Sent message: {result}")

        # Сохраняем сообщение и дату в истории (не больше 100 сообщений)
        chat_messages.append((message_date, message_text))
        if len(chat_messages) > 100:
            chat_messages.pop(0)

    except Exception as e:
        logger.error(f"Error processing message: {e}")

# Функция обработки команды /request_coefficients
async def request_coefficients(update: Update, context: CallbackContext) -> None:
    logger.info(f"User {update.message.from_user.id} requested coefficients.")
    
    try:
        if not chat_messages:
            await update.message.reply_text("Нет сохраненных сообщений.")
            return

        found_results = []
        for message_date, message_text in chat_messages:
            matches = re.findall(r"(Дух|Олимп|Техно):?\s*(\d+\.\d+)", message_text)
            if matches:
                for place, coefficient in matches:
                    found_results.append(f"{message_date} {place} {coefficient}")

        if found_results:
            logger.info(f"Found coefficients: {found_results}")
            await update.message.reply_text("\n".join(found_results))
        else:
            await update.message.reply_text("Коэффициенты не найдены в последних 100 сообщениях.")

    except Exception as e:
        logger.error(f"Error fetching stored messages: {e}")
        await update.message.reply_text("Ошибка при обработке запроса!")

# Основная функция
async def main():
    if not TOKEN or not YOUR_CHAT_ID:
        logger.error("TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не заданы!")
        return
    
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))  # обработчик /start
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_chat_message))  # обработчик всех сообщений
    application.add_handler(CommandHandler("request_coefficients", request_coefficients))  # обработчик /request_coefficients

    logger.info("Bot started")
    await application.run_polling()

# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())  # Запуск бота