import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from tgbot.database import init_db
from tgbot.handlers import start, payment, mylink
from tgbot.scheduler import setup_scheduler

# Загружаем переменные окружения из .env (если файл есть)
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в переменных окружения")


async def main():
    """Основная функция запуска бота"""
    # Инициализируем базу данных
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутеры обработчиков
    # Порядок важен: payment должен быть до start,
    # чтобы фото/документы обрабатывались в любом состоянии
    dp.include_router(payment.router)
    dp.include_router(start.router)
    dp.include_router(mylink.router)

    # Настраиваем и запускаем планировщик напоминаний
    scheduler = setup_scheduler(bot)
    scheduler.start()

    try:
        # Запускаем polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
