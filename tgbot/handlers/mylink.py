import os
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.database import get_user_token

router = Router()

APP_URL = os.getenv("APP_URL", "https://example.com")


def get_open_keyboard():
    """Клавиатура для открытия доступа"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔓 Открыть все буквы — 1200 ₽", callback_data="open_payment")
    builder.adjust(1)
    return builder.as_markup()


@router.message(Command("mylink"))
async def cmd_mylink(message: Message):
    """Обработчик команды /mylink — показывает персональную ссылку"""
    token = await get_user_token(message.from_user.id)

    if token:
        await message.answer(
            f"🔗 Вот твоя ссылка на читалку:\n"
            f"{APP_URL}?token={token}\n\n"
            f"Сохрани в закладки, чтобы не потерять 🔑"
        )
    else:
        await message.answer(
            "У тебя пока нет доступа. Хочешь открыть все буквы? 🌟",
            reply_markup=get_open_keyboard(),
        )
