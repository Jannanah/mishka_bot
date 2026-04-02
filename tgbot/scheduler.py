from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from tgbot.database import get_unpaid_users_for_reminder, set_reminder_sent


ADMIN_USERNAME = "Ksenia_qurancoach"


def get_reminder_keyboard():
    """Клавиатура для напоминания"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔒Открыть все буквы - 1200₽", callback_data="open_payment")
    builder.button(text="❓Задать вопрос", callback_data="ask_question")
    builder.adjust(1)
    return builder.as_markup()


async def send_reminders(bot: Bot):
    """Отправка напоминаний пользователям, не оплатившим через 24 часа"""
    users = await get_unpaid_users_for_reminder()
    for user in users:
        try:
            await bot.send_message(
                chat_id=user["user_id"],
                text=(
                    "Ты уже начал изучение букв 📚\n"
                    "Хочешь продолжить?\n"
                    "Остался один шаг"
                ),
                reply_markup=get_reminder_keyboard(),
            )
            await set_reminder_sent(user["user_id"])
        except Exception:
            # Если пользователь заблокировал бота — пропускаем
            await set_reminder_sent(user["user_id"])


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Настройка и запуск планировщика задач"""
    scheduler = AsyncIOScheduler()
    # Проверяем каждый час пользователей, которым нужно напоминание через 24 часа
    scheduler.add_job(send_reminders, "interval", hours=1, args=[bot])
    return scheduler
