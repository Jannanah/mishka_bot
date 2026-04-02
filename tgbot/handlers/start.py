from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.database import upsert_user

router = Router()


def get_start_keyboard():
    """Клавиатура для стартового сообщения"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👉 Начать", callback_data="start_begin")
    builder.button(text="👉 Написать оператору", url="https://t.me/Ksenia_qurancoach")
    builder.adjust(1)
    return builder.as_markup()


def get_features_keyboard():
    """Клавиатура для экрана с описанием возможностей"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔒Открыть все буквы - 1200₽", callback_data="open_payment")
    builder.button(text="❓Задать вопрос", callback_data="ask_question")
    builder.adjust(1)
    return builder.as_markup()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    await upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )
    await message.answer(
        "✨ Добро пожаловать в звучащую читалку!\n\n"
        "Ты уже начал изучать буквы в приложении 📚\n"
        "Сейчас откроем тебе полный доступ — без замков ✨",
        reply_markup=get_start_keyboard(),
    )


@router.callback_query(F.data == "start_begin")
async def cb_start_begin(callback: CallbackQuery):
    """Обработчик нажатия 'Начать'"""
    await callback.answer()
    await callback.message.answer(
        "✨ В полной версии тебя ждёт:\n\n"
        "📚 все буквы и стишки\n"
        "📖 все книги\n"
        "⭐️ задания и награды\n"
        "🧠 методичка для мамы\n\n"
        "💡 Это не PDF — это живая читалка, где ребёнок участвует сам\n\n"
        "Готовы открыть все буквы?",
        reply_markup=get_features_keyboard(),
    )
