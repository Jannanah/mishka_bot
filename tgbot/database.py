import aiosqlite
import os
from datetime import datetime

# Путь к файлу базы данных
DB_PATH = os.path.join(os.path.dirname(__file__), "bot_data.db")


async def init_db():
    """Инициализация базы данных и создание таблиц"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                token TEXT,
                issued_at TEXT,
                paid INTEGER DEFAULT 0,
                payment_requested_at TEXT,
                reminder_sent INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def get_user(user_id: int):
    """Получить пользователя по ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def upsert_user(user_id: int, username: str, first_name: str):
    """Создать или обновить пользователя (без затирания токена)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username or "", first_name or ""))
        await db.commit()


async def set_payment_requested(user_id: int):
    """Отметить, что пользователь нажал 'Открыть все буквы' (запрос оплаты)"""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute("""
            UPDATE users SET payment_requested_at = ?
            WHERE user_id = ? AND payment_requested_at IS NULL
        """, (now, user_id))
        await db.commit()


async def save_token(user_id: int, token: str):
    """Сохранить токен доступа пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now().isoformat()
        await db.execute("""
            UPDATE users SET token = ?, issued_at = ?, paid = 1
            WHERE user_id = ?
        """, (token, now, user_id))
        await db.commit()


async def get_user_token(user_id: int):
    """Получить токен пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT token FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def get_unpaid_users_for_reminder():
    """Получить пользователей, которым нужно отправить напоминание через 24 часа"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM users
            WHERE paid = 0
            AND payment_requested_at IS NOT NULL
            AND reminder_sent = 0
            AND datetime(payment_requested_at, '+24 hours') <= datetime('now')
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def set_reminder_sent(user_id: int):
    """Отметить, что напоминание отправлено"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET reminder_sent = 1 WHERE user_id = ?", (user_id,)
        )
        await db.commit()
