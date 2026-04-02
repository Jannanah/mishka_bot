import os
import secrets
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from tgbot.database import (
    upsert_user,
    save_token,
    set_payment_requested,
    get_user,
)

router = Router()

APP_URL = os.getenv("APP_URL", "https://example.com")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# Путь к QR-коду Сбербанка
QR_PATH = os.path.join(os.path.dirname(__file__), "..", "qr_sberbank.png")
ADMIN_USERNAME = "Ksenia_qurancoach"


class PaymentState(StatesGroup):
    # Состояние ожидания чека от пользователя
    waiting_for_receipt = State()
    # Состояние ожидания вопроса от пользователя
    waiting_for_question = State()


def get_operator_keyboard():
    """Клавиатура с кнопкой написать оператору"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👉 Написать оператору", url=f"https://t.me/{ADMIN_USERNAME}")
    builder.adjust(1)
    return builder.as_markup()


def get_send_receipt_keyboard():
    """Клавиатура для напоминания о чеке"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👉 Отправить чек", callback_data="open_payment")
    builder.button(text="👉 Написать оператору", url=f"https://t.me/{ADMIN_USERNAME}")
    builder.adjust(1)
    return builder.as_markup()


def get_payment_reminder_keyboard():
    """Клавиатура для суточного напоминания"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔒Открыть все буквы - 1200₽", callback_data="open_payment")
    builder.button(text="❓Задать вопрос", callback_data="ask_question")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data == "open_payment")
async def cb_open_payment(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия 'Открыть все буквы — 1200 ₽'"""
    await callback.answer()
    # Сохраняем время нажатия кнопки оплаты для напоминаний
    await set_payment_requested(callback.from_user.id)
    # Переводим пользователя в состояние ожидания чека
    await state.set_state(PaymentState.waiting_for_receipt)
    # Отправляем QR-код с текстом в подписи
    qr_file = FSInputFile(QR_PATH)
    await callback.message.answer_photo(
        photo=qr_file,
        caption=(
            "💳 Как оплатить: \n\n"
            "📌Оплата 1200₽ на сбербанк по QR-коду или по ссылке:\n"
            "https://www.sberbank.com/sms/pbpn?requisiteNumber=79217642011\n\n"
            "После оплаты отправьте скриншот или PDF чека прямо сюда 👇"
        ),
    )


@router.callback_query(F.data == "ask_question")
async def cb_ask_question(callback: CallbackQuery, state: FSMContext):
    """Обработчик нажатия 'Задать вопрос'"""
    await callback.answer()
    # Переводим пользователя в состояние ожидания вопроса
    await state.set_state(PaymentState.waiting_for_question)
    await callback.message.answer(
        f"Напиши свой вопрос — я передам Ксении ✨\n"
        f"Или напиши ей напрямую: @{ADMIN_USERNAME}"
    )


@router.message(PaymentState.waiting_for_question, F.text)
async def handle_question_text(message: Message, bot: Bot):
    """Обработчик текстового вопроса от пользователя"""
    user = message.from_user
    username = user.username or "без username"
    # Пересылаем вопрос администратору
    await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            f"❓ Вопрос от {user.first_name} (@{username}, ID: {user.id}):\n\n"
            f"{message.text}"
        ),
    )
    await message.answer(
        f"Напиши свой вопрос — я передам Ксении ✨\n"
        f"Или напиши ей напрямую: @{ADMIN_USERNAME}"
    )


async def issue_access(message: Message, bot: Bot, file_id: str = None, is_document: bool = False):
    """Выдать доступ пользователю после получения чека"""
    user = message.from_user
    await upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )
    # Генерируем уникальный токен — 32 символа
    token = secrets.token_hex(16)
    await save_token(user_id=user.id, token=token)

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    username = user.username or "без username"

    # Отправляем пользователю персональную ссылку
    await message.answer(
        f"🎉 Доступ открыт!\n\n"
        f"Вот твоя персональная ссылка на читалку:\n"
        f"🔗 {APP_URL}?token={token}\n\n"
        f"Сохрани её — это твой личный вход 🔑\n\n"
        f"📌 Ссылка работает только для тебя.\n"
        f"Если потеряешь — напиши /mylink и я пришлю снова."
    )

    # Уведомляем администратора
    await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=(
            f"💰 Новая оплата!\n"
            f"👤 Имя: {user.first_name}\n"
            f"🆔 ID: {user.id}\n"
            f"📎 Username: @{username}\n"
            f"🔗 Токен: {token}\n"
            f"📅 Дата: {now}"
        ),
    )

    # Пересылаем файл (скрин/PDF) администратору
    if file_id:
        if is_document:
            await bot.send_document(chat_id=ADMIN_CHAT_ID, document=file_id)
        else:
            await bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=file_id)


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot, state: FSMContext):
    """Обработчик фото — считаем любое фото чеком оплаты"""
    # Берём фото в наилучшем качестве
    file_id = message.photo[-1].file_id
    await state.clear()
    await issue_access(message, bot, file_id=file_id, is_document=False)


@router.message(F.document)
async def handle_document(message: Message, bot: Bot, state: FSMContext):
    """Обработчик документа (PDF и др.) — считаем любой документ чеком оплаты"""
    file_id = message.document.file_id
    await state.clear()
    await issue_access(message, bot, file_id=file_id, is_document=True)


@router.message(PaymentState.waiting_for_receipt, F.text)
async def handle_wrong_message_in_payment(message: Message):
    """Обработчик текстового сообщения вместо чека"""
    await message.answer(
        "📩 Отправь, пожалуйста, чек или скрин оплаты\n"
        "Если возникли сложности — напиши оператору 💬",
        reply_markup=get_operator_keyboard(),
    )
