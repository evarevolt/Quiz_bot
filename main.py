
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from db_connection import create_table
from handlers import router

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Замените "YOUR_BOT_TOKEN" на токен, который вы получили от BotFather
API_TOKEN = '7140254626:AAFiDCB5cuYpT4Tc-8QPPY2Tze_SR1Tz_lU'

# Запуск процесса поллинга новых апдейтов
async def main():
    # Объект бота
    bot = Bot(token=API_TOKEN)
    # Диспетчер
    dp = Dispatcher()
    dp.include_router(router)
    await create_table()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())