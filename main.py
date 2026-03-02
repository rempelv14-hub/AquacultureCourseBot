import os
import asyncio
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "PASTE_YOUR_BOT_TOKEN_HERE"
if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
    raise RuntimeError("BOT_TOKEN не задан. Вставь токен в код или передай через переменную окружения BOT_TOKEN.")

ADMIN_TG_ID = 632308904

DELAY_SECONDS = 2 * 60
DB_PATH = "bot.db"

SUPPORT_WA_LINK = "https://wa.me/77072102513"
MATERIALS_LINK = "https://disk.yandex.com/d/Yyum24diLez7Zw"

# ================== VIDEO file_id ==================
INTRO_VIDEO_ID = "BAACAgIAAxkBAANpaaRSWp8aOkE3mcivVcQDJ9hEAAECAAIOkgACuEEgSZZk99fCbt-oOgQ"

REVIEW_VIDEO_IDS = [
    "BAACAgIAAxkBAAN1aaRTG8n4WCTld4QhNf4nBtm6c3kAAiCSAAK4QSBJwJLxdJEE2VU6BA",
    "BAACAgIAAxkBAAN3aaRTMrIxxmDfUV4fDtcL_WqA7VgAAieSAAK4QSBJ0AABt8XJic8LOgQ",
    "BAACAgIAAxkBAAN5aaRTTEpDNNK9RHRJEiRaiu0zX3UAAiuSAAK4QSBJpfcnXUqCPF86BA",
    "BAACAgIAAxkBAAN7aaRTZC-mV7sEgpsyZohoK9BV4KkAAi-SAAK4QSBJlk-ilX5qJ6s6BA",
    "BAACAgIAAxkBAAN9aaRT3HldPJ1gSpveLSmQ06d1nYAAAkSSAAK4QSBJ4Own9SEfFsY6BA",
]

# ================== DB (SQLite) ==================
DB_LOCK = asyncio.Lock()

def _connect():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    return con

def db_init():
    with _connect() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            plan TEXT,
            is_paid INTEGER,
            paid_at TEXT
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS pending (
            user_id INTEGER PRIMARY KEY,
            plan TEXT
        )""")
        con.commit()

async def set_pending(user_id: int, plan: str):
    async with DB_LOCK:
        with _connect() as con:
            con.execute("REPLACE INTO pending VALUES (?,?)", (user_id, plan))
            con.commit()

async def get_pending(user_id: int):
    async with DB_LOCK:
        with _connect() as con:
            row = con.execute("SELECT plan FROM pending WHERE user_id=?", (user_id,)).fetchone()
            return row[0] if row else None

async def clear_pending(user_id: int):
    async with DB_LOCK:
        with _connect() as con:
            con.execute("DELETE FROM pending WHERE user_id=?", (user_id,))
            con.commit()

async def grant_access(user_id: int, plan: str):
    async with DB_LOCK:
        with _connect() as con:
            con.execute(
                "REPLACE INTO users VALUES (?,?,?,?)",
                (user_id, plan, 1, datetime.now().isoformat())
            )
            con.execute("DELETE FROM pending WHERE user_id=?", (user_id,))
            con.commit()

async def get_access(user_id: int):
    async with DB_LOCK:
        with _connect() as con:
            row = con.execute("SELECT plan, is_paid FROM users WHERE user_id=?", (user_id,)).fetchone()
            if not row:
                return None, 0
            return row[0], row[1]

# ================== ТЕКСТЫ ==================
WELCOME_TEXT = (
    "Здравствуй! 👋 Добро пожаловать в курс «Аквакультура с нуля» 🐟\n"
    "Здесь ты шаг за шагом разберёшься, как запустить выращивание "
    "(пруд / садки / УЗВ): от воды и кормления до ошибок, которые стоят денег."
)

BEFORE_TARIFFS_TEXT = "Перед приобретением курса прошу ознакомиться с нашими тарифами и отзывами."

TARIFFS_TEXT = (
    "Тариф 1: «Премиум сопровождение» — 250 000 тг\n\n"
    "В этот тариф включено:\n"
    "✅ Доступ к видеокурсам (вся обучающая база).\n"
    "✅ 6 месяцев полного сопровождения.\n"
    "✅ В течение 6 месяцев клиент может обращаться к нам с любыми вопросами по бизнесу.\n"
    "✅ Поддержка через чат.\n"
    "✅ Еженедельный видео-звонок (1 раз в неделю).\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "Тариф 2: «Базовое обучение» — 150 000 тг\n\n"
    "В этот тариф включено:\n"
    "✅ Доступ к видеокурсам (вся обучающая база).\n"
    "✅ 3 месяца поддержки.\n"
    "✅ В течение 3 месяцев клиент может обращаться к нам с вопросами через чат.\n"
    "✅ Важно: видео-звонки не предусмотрены."
)

PAYMENT_TEXT = (
    "💳 **Оплата Kaspi**\n\n"
    "Получатель: **YERLAN KEGENOV**\n"
    "Номер карты: **4400 4302 0609 7443**\n\n"
    "После оплаты нажмите **«Я оплатил»** и отправьте чек."
)

MATERIALS_LOCKED = (
    "🔒 **Материалы закрыты**\n\n"
    "Доступ откроется после оплаты и подтверждения чека администратором."
)

# ================== КНОПКИ ==================
def kb_start():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Начать", callback_data="start")
    kb.adjust(1)
    return kb.as_markup()

# Материалы НЕ в меню тарифов — они отдельно после оплаты
def kb_tariffs():
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Оплатить Базовый", callback_data="pay_basic")
    kb.button(text="💳 Оплатить Премиум", callback_data="pay_premium")
    kb.button(text="⭐ Отзывы", callback_data="reviews")
    kb.button(text="🛟 Поддержка", url=SUPPORT_WA_LINK)
    kb.adjust(1)
    return kb.as_markup()

def kb_payment(plan: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Я оплатил", callback_data=f"paid:{plan}")
    kb.button(text="🛟 Поддержка", url=SUPPORT_WA_LINK)
    kb.adjust(1)
    return kb.as_markup()

def kb_admin(user_id: int, plan: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data=f"ok:{user_id}:{plan}")
    kb.button(text="❌ Отклонить", callback_data=f"no:{user_id}")
    kb.adjust(2)
    return kb.as_markup()

def kb_materials_url():
    kb = InlineKeyboardBuilder()
    kb.button(text="📚 Материалы курса", url=MATERIALS_LINK)
    kb.button(text="🛟 Поддержка", url=SUPPORT_WA_LINK)
    kb.adjust(1)
    return kb.as_markup()

def kb_reviews_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="▶️ Показать отзывы", callback_data="review_show:0")
    kb.button(text="⬅️ Назад к тарифам", callback_data="back_tariffs")
    kb.adjust(1)
    return kb.as_markup()

def kb_review_nav(i: int, total: int):
    kb = InlineKeyboardBuilder()
    if i + 1 < total:
        kb.button(text="▶️ Следующий отзыв", callback_data=f"review_show:{i+1}")
    kb.button(text="⬅️ Назад к тарифам", callback_data="back_tariffs")
    kb.adjust(1)
    return kb.as_markup()

# ================== БОТ ==================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# ===== фоновая отправка тарифов (чтобы callback не протух) =====
async def send_tariffs_later(chat_id: int):
    await asyncio.sleep(DELAY_SECONDS)
    await bot.send_message(chat_id, BEFORE_TARIFFS_TEXT, protect_content=True)
    await bot.send_message(chat_id, TARIFFS_TEXT, reply_markup=kb_tariffs(), protect_content=True)

@dp.message(CommandStart())
async def start_cmd(m: Message):
    await m.answer(WELCOME_TEXT, reply_markup=kb_start(), protect_content=True)

@dp.callback_query(F.data == "start")
async def start_course(c: CallbackQuery):
    await c.answer()  # ✅ сразу отвечаем на callback

    await c.message.answer_video(INTRO_VIDEO_ID, protect_content=True)

    # ✅ тарифы отправляем в фоне
    asyncio.create_task(send_tariffs_later(c.message.chat.id))

@dp.callback_query(F.data == "back_tariffs")
async def back_tariffs(c: CallbackQuery):
    await c.message.answer(TARIFFS_TEXT, reply_markup=kb_tariffs(), protect_content=True)
    await c.answer()

# ===== Оплата =====
@dp.callback_query(F.data == "pay_basic")
async def pay_basic(c: CallbackQuery):
    await c.message.answer(PAYMENT_TEXT, reply_markup=kb_payment("basic"), protect_content=True)
    await c.answer()

@dp.callback_query(F.data == "pay_premium")
async def pay_premium(c: CallbackQuery):
    await c.message.answer(PAYMENT_TEXT, reply_markup=kb_payment("premium"), protect_content=True)
    await c.answer()

@dp.callback_query(F.data.startswith("paid:"))
async def paid(c: CallbackQuery):
    plan = c.data.split(":")[1]
    await set_pending(c.from_user.id, plan)
    await c.message.answer("📎 Отправьте чек (фото или файл)", protect_content=True)
    await c.answer()

@dp.message(F.photo | F.document)
async def receive_check(m: Message):
    plan = await get_pending(m.from_user.id)
    if not plan:
        return

    caption = (
        f"🧾 Чек на проверку\n\n"
        f"Пользователь: {m.from_user.full_name}\n"
        f"ID: {m.from_user.id}\n"
        f"Тариф: {plan}"
    )

    if m.photo:
        await bot.send_photo(
            ADMIN_TG_ID,
            m.photo[-1].file_id,
            caption=caption,
            reply_markup=kb_admin(m.from_user.id, plan),
            protect_content=True
        )
    else:
        await bot.send_document(
            ADMIN_TG_ID,
            m.document.file_id,
            caption=caption,
            reply_markup=kb_admin(m.from_user.id, plan),
            protect_content=True
        )

    await m.answer("⏳ Чек отправлен админу. Ожидайте подтверждения.", protect_content=True)

@dp.callback_query(F.data.startswith("ok:"))
async def admin_ok(c: CallbackQuery):
    if c.from_user.id != ADMIN_TG_ID:
        return

    _, uid, plan = c.data.split(":")
    uid_int = int(uid)

    await grant_access(uid_int, plan)

    # ✅ Материалы отдельно после оплаты
    await bot.send_message(
        uid_int,
        "✅ **Оплата подтверждена!**\n\nНиже кнопка для доступа к материалам курса 👇",
        reply_markup=kb_materials_url(),
        protect_content=True
    )

    # чтобы админ не жмакал повторно
    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await c.answer("Подтверждено")

@dp.callback_query(F.data.startswith("no:"))
async def admin_no(c: CallbackQuery):
    if c.from_user.id != ADMIN_TG_ID:
        return
    uid = int(c.data.split(":")[1])
    await clear_pending(uid)
    await bot.send_message(uid, "❌ Оплата отклонена. Свяжитесь с поддержкой.", protect_content=True)

    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await c.answer("Отклонено")

# Команда для оплативших, если потеряли сообщение
@dp.message(Command("materials"))
async def materials_cmd(m: Message):
    _, paid = await get_access(m.from_user.id)
    if not paid:
        await m.answer(MATERIALS_LOCKED, protect_content=True)
        return
    await m.answer("📚 Материалы курса по кнопке ниже:", reply_markup=kb_materials_url(), protect_content=True)

# ===== Отзывы (file_id) =====
@dp.callback_query(F.data == "reviews")
async def reviews(c: CallbackQuery):
    if not REVIEW_VIDEO_IDS:
        await c.message.answer("⚠️ Отзывы не настроены.", protect_content=True)
        await c.answer()
        return

    await c.message.answer(
        f"⭐ Найдено отзывов: **{len(REVIEW_VIDEO_IDS)}**",
        reply_markup=kb_reviews_menu(),
        protect_content=True
    )
    await c.answer()

@dp.callback_query(F.data.startswith("review_show:"))
async def review_show(c: CallbackQuery):
    total = len(REVIEW_VIDEO_IDS)
    if total == 0:
        await c.message.answer("⚠️ Отзывы не настроены.", protect_content=True)
        await c.answer()
        return

    try:
        idx = int(c.data.split(":")[1])
    except Exception:
        idx = 0

    if idx < 0 or idx >= total:
        idx = 0

    await c.answer()  # ✅ тоже отвечаем сразу, чтобы не протухало

    await c.message.answer_video(
        video=REVIEW_VIDEO_IDS[idx],
        caption=f"⭐ **Отзыв {idx + 1} из {total}**",
        reply_markup=kb_review_nav(idx, total),
        protect_content=True
    )

# ================== ЗАПУСК ==================
async def main():
    db_init()
    # Важно для polling: никаких вебхуков
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())