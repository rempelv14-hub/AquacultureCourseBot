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

REVIEW_VIDEO_IDS = {
    "ru": [
        "BAACAgIAAxkBAAN1aaRTG8n4WCTld4QhNf4nBtm6c3kAAiCSAAK4QSBJwJLxdJEE2VU6BA",
        "BAACAgIAAxkBAAN3aaRTMrIxxmDfUV4fDtcL_WqA7VgAAieSAAK4QSBJ0AABt8XJic8LOgQ",
        "BAACAgIAAxkBAAN5aaRTTEpDNNK9RHRJEiRaiu0zX3UAAiuSAAK4QSBJpfcnXUqCPF86BA",
        "BAACAgIAAxkBAAN7aaRTZC-mV7sEgpsyZohoK9BV4KkAAi-SAAK4QSBJlk-ilX5qJ6s6BA",
        "BAACAgIAAxkBAAN9aaRT3HldPJ1gSpveLSmQ06d1nYAAAkSSAAK4QSBJ4Own9SEfFsY6BA",
    ],
    "kz": [
        "BAACAgIAAxkBAAMCaaxF4ZQu7VTzzCz7fyGNBX3oz4UAAoGSAALtMGhJNgzVea3o5Po6BA",
        "BAACAgIAAxkBAAMEaaxGHSHOusqnm3o03fEd3m6RwggAAoeSAALtMGhJiWx1YpuQ5aY6BA",
        "BAACAgIAAxkBAAMGaaxGM-IujAw-FTmFhAQrwhh06FYAAoqSAALtMGhJyORgI_IER6M6BA",
        "BAACAgIAAxkBAAMIaaxGaW_xkJ73YxMXz38OpIZmRqwAAo-SAALtMGhJqpgIKtVx1mc6BA",
        "BAACAgIAAxkBAAMKaaxGghIQSR3R57cb2OgKdbIIg5gAApKSAALtMGhJb3QNBQgkkKk6BA",
        "BAACAgIAAxkBAAMMaaxGmbaAlKOGmoBeJ_vYZiD6EoUAApOSAALtMGhJEy9Sc-xqvFw6BA",
        "BAACAgIAAxkBAAMOaaxGsrhGB1PCExSBkXe1pS8TmpgAApWSAALtMGhJ9n10go_afpc6BA",
        "BAACAgIAAxkBAAMQaaxGzkubwDpd1X1lMUOgz7gWbbIAApiSAALtMGhJgc4AAeLJoOWmOgQ",
    ]
}

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
            paid_at TEXT,
            lang TEXT DEFAULT 'ru'
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS pending (
            user_id INTEGER PRIMARY KEY,
            plan TEXT
        )""")

        try:
            cur.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'ru'")
        except sqlite3.OperationalError:
            pass

        con.commit()

async def ensure_user(user_id: int):
    async with DB_LOCK:
        with _connect() as con:
            con.execute(
                "INSERT OR IGNORE INTO users (user_id, plan, is_paid, paid_at, lang) VALUES (?, ?, ?, ?, ?)",
                (user_id, None, 0, None, "ru")
            )
            con.commit()

async def set_lang(user_id: int, lang: str):
    await ensure_user(user_id)
    async with DB_LOCK:
        with _connect() as con:
            con.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
            con.commit()

async def get_lang(user_id: int):
    async with DB_LOCK:
        with _connect() as con:
            row = con.execute("SELECT lang FROM users WHERE user_id=?", (user_id,)).fetchone()
            if not row or not row[0]:
                return "ru"
            return row[0]

async def set_pending(user_id: int, plan: str):
    await ensure_user(user_id)
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
    await ensure_user(user_id)
    async with DB_LOCK:
        with _connect() as con:
            current_lang = con.execute(
                "SELECT lang FROM users WHERE user_id=?",
                (user_id,)
            ).fetchone()
            lang = current_lang[0] if current_lang and current_lang[0] else "ru"

            con.execute(
                "REPLACE INTO users (user_id, plan, is_paid, paid_at, lang) VALUES (?,?,?,?,?)",
                (user_id, plan, 1, datetime.now().isoformat(), lang)
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

# ================== ЛОКАЛИЗАЦИЯ ==================
TEXTS = {
    "ru": {
        "choose_lang": "🌐 Выберите язык / Тілді таңдаңыз",
        "welcome": (
            "Здравствуй! 👋 Добро пожаловать в курс «Аквакультура с нуля» 🐟\n"
            "Здесь ты шаг за шагом разберёшься, как запустить выращивание "
            "(пруд / садки / УЗВ): от воды и кормления до ошибок, которые стоят денег."
        ),
        "start_btn": "🚀 Начать",
        "before_tariffs": "Перед приобретением курса прошу ознакомиться с нашими тарифами и отзывами.",
        "tariffs": (
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
        ),
        "pay_basic_btn": "💳 Оплатить Базовый",
        "pay_premium_btn": "💳 Оплатить Премиум",
        "reviews_btn": "⭐ Отзывы",
        "support_btn": "🛟 Поддержка",
        "payment": (
            "💳 **Оплата Kaspi**\n\n"
            "Получатель: **YERLAN KEGENOV**\n"
            "Номер карты: **4400 4302 0609 7443**\n\n"
            "После оплаты нажмите **«Я оплатил»** и отправьте чек."
        ),
        "i_paid_btn": "✅ Я оплатил",
        "send_check": "📎 Отправьте чек (фото или файл)",
        "check_sent": "⏳ Чек отправлен админу. Ожидайте подтверждения.",
        "materials_locked": (
            "🔒 **Материалы закрыты**\n\n"
            "Доступ откроется после оплаты и подтверждения чека администратором."
        ),
        "materials_btn": "📚 Материалы курса",
        "payment_confirmed": (
            "✅ **Оплата подтверждена!**\n\n"
            "Ниже кнопка для доступа к материалам курса 👇"
        ),
        "payment_rejected": "❌ Оплата отклонена. Свяжитесь с поддержкой.",
        "materials_msg": "📚 Материалы курса по кнопке ниже:",
        "reviews_found": "⭐ Найдено отзывов: **{count}**",
        "show_reviews_btn": "▶️ Показать отзывы",
        "back_tariffs_btn": "⬅️ Назад к тарифам",
        "next_review_btn": "▶️ Следующий отзыв",
        "review_caption": "⭐ **Отзыв {num} из {total}**",
        "reviews_not_set": "⚠️ Отзывы не настроены.",
        "admin_caption": (
            "🧾 Чек на проверку\n\n"
            "Пользователь: {full_name}\n"
            "ID: {user_id}\n"
            "Тариф: {plan}"
        ),
        "admin_ok_btn": "✅ Подтвердить",
        "admin_no_btn": "❌ Отклонить",
        "approved_answer": "Подтверждено",
        "rejected_answer": "Отклонено",
        "plan_basic": "Базовый",
        "plan_premium": "Премиум",
        "lang_btn": "🌐 Сменить язык",
    },
    "kz": {
        "choose_lang": "🌐 Выберите язык / Тілді таңдаңыз",
        "welcome": (
            "Сәлеметсіз бе! 👋 «Аквакультура нөлден» курсына қош келдіңіз 🐟\n"
            "Мұнда сіз балық өсіруді (тоған / тор / УЗВ) кезең-кезеңімен үйренесіз: "
            "судан және азықтандырудан бастап, ақшаға зиян келтіретін қателіктерге дейін."
        ),
        "start_btn": "🚀 Бастау",
        "before_tariffs": "Курсты сатып алмас бұрын тарифтер мен пікірлермен танысып шығуыңызды сұраймыз.",
        "tariffs": (
            "Тариф 1: «Премиум сүйемелдеу» — 250 000 тг\n\n"
            "Бұл тарифке мыналар кіреді:\n"
            "✅ Бейне курстарға қолжетімділік (барлық оқу базасы).\n"
            "✅ 6 ай толық сүйемелдеу.\n"
            "✅ 6 ай ішінде клиент бизнес бойынша кез келген сұрақпен хабарласа алады.\n"
            "✅ Чат арқылы қолдау.\n"
            "✅ Аптасына 1 рет бейне қоңырау.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Тариф 2: «Базалық оқу» — 150 000 тг\n\n"
            "Бұл тарифке мыналар кіреді:\n"
            "✅ Бейне курстарға қолжетімділік (барлық оқу базасы).\n"
            "✅ 3 ай қолдау.\n"
            "✅ 3 ай ішінде клиент чат арқылы сұрақ қоя алады.\n"
            "✅ Маңызды: бейне қоңыраулар қарастырылмаған."
        ),
        "pay_basic_btn": "💳 Базалықты төлеу",
        "pay_premium_btn": "💳 Премиумды төлеу",
        "reviews_btn": "⭐ Пікірлер",
        "support_btn": "🛟 Қолдау",
        "payment": (
            "💳 **Kaspi арқылы төлем**\n\n"
            "Алушы: **YERLAN KEGENOV**\n"
            "Карта нөмірі: **4400 4302 0609 7443**\n\n"
            "Төлем жасағаннан кейін **«Мен төледім»** батырмасын басып, чекті жіберіңіз."
        ),
        "i_paid_btn": "✅ Мен төледім",
        "send_check": "📎 Чекті жіберіңіз (фото немесе файл)",
        "check_sent": "⏳ Чек әкімшіге жіберілді. Растауды күтіңіз.",
        "materials_locked": (
            "🔒 **Материалдар жабық**\n\n"
            "Қолжетімділік төлем жасалып, әкімші чек растағаннан кейін ашылады."
        ),
        "materials_btn": "📚 Курс материалдары",
        "payment_confirmed": (
            "✅ **Төлем расталды!**\n\n"
            "Төменде курс материалдарына кіру батырмасы берілген 👇"
        ),
        "payment_rejected": "❌ Төлем қабылданбады. Қолдау қызметіне хабарласыңыз.",
        "materials_msg": "📚 Курс материалдары төмендегі батырмада:",
        "reviews_found": "⭐ Табылған пікірлер саны: **{count}**",
        "show_reviews_btn": "▶️ Пікірлерді көрсету",
        "back_tariffs_btn": "⬅️ Тарифтерге қайту",
        "next_review_btn": "▶️ Келесі пікір",
        "review_caption": "⭐ **Пікір {num} / {total}**",
        "reviews_not_set": "⚠️ Пікірлер бапталмаған.",
        "admin_caption": (
            "🧾 Тексеруге чек\n\n"
            "Пайдаланушы: {full_name}\n"
            "ID: {user_id}\n"
            "Тариф: {plan}"
        ),
        "admin_ok_btn": "✅ Растау",
        "admin_no_btn": "❌ Қабылдамау",
        "approved_answer": "Расталды",
        "rejected_answer": "Қабылданбады",
        "plan_basic": "Базалық",
        "plan_premium": "Премиум",
        "lang_btn": "🌐 Тілді өзгерту",
    }
}

def t(lang: str, key: str, **kwargs):
    lang = lang if lang in TEXTS else "ru"
    text = TEXTS[lang][key]
    if kwargs:
        return text.format(**kwargs)
    return text

def plan_label(lang: str, plan: str):
    if plan == "basic":
        return t(lang, "plan_basic")
    if plan == "premium":
        return t(lang, "plan_premium")
    return plan

# ================== КНОПКИ ==================
def kb_lang():
    kb = InlineKeyboardBuilder()
    kb.button(text="🇷🇺 Русский", callback_data="lang_ru")
    kb.button(text="🇰🇿 Қазақша", callback_data="lang_kz")
    kb.adjust(2)
    return kb.as_markup()

def kb_start(lang: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "start_btn"), callback_data="start")
    kb.adjust(1)
    return kb.as_markup()

def kb_tariffs(lang: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "pay_basic_btn"), callback_data="pay_basic")
    kb.button(text=t(lang, "pay_premium_btn"), callback_data="pay_premium")
    kb.button(text=t(lang, "reviews_btn"), callback_data="reviews")
    kb.button(text=t(lang, "support_btn"), url=SUPPORT_WA_LINK)
    kb.adjust(1)
    return kb.as_markup()

def kb_payment(lang: str, plan: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "i_paid_btn"), callback_data=f"paid:{plan}")
    kb.button(text=t(lang, "support_btn"), url=SUPPORT_WA_LINK)
    kb.adjust(1)
    return kb.as_markup()

def kb_admin(user_id: int, plan: str, lang: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "admin_ok_btn"), callback_data=f"ok:{user_id}:{plan}")
    kb.button(text=t(lang, "admin_no_btn"), callback_data=f"no:{user_id}")
    kb.adjust(2)
    return kb.as_markup()

def kb_materials_url(lang: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "materials_btn"), url=MATERIALS_LINK)
    kb.button(text=t(lang, "support_btn"), url=SUPPORT_WA_LINK)
    kb.adjust(1)
    return kb.as_markup()

def kb_reviews_menu(lang: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "show_reviews_btn"), callback_data="review_show:0")
    kb.button(text=t(lang, "back_tariffs_btn"), callback_data="back_tariffs")
    kb.adjust(1)
    return kb.as_markup()

def kb_review_nav(lang: str, i: int, total: int):
    kb = InlineKeyboardBuilder()
    if i + 1 < total:
        kb.button(text=t(lang, "next_review_btn"), callback_data=f"review_show:{i+1}")
    kb.button(text=t(lang, "back_tariffs_btn"), callback_data="back_tariffs")
    kb.adjust(1)
    return kb.as_markup()

# ================== БОТ ==================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
dp = Dispatcher()

# ================== ФОН ==================
async def send_tariffs_later(chat_id: int):
    await asyncio.sleep(DELAY_SECONDS)
    lang = await get_lang(chat_id)
    await bot.send_message(chat_id, t(lang, "before_tariffs"), protect_content=True)
    await bot.send_message(chat_id, t(lang, "tariffs"), reply_markup=kb_tariffs(lang), protect_content=True)

# ================== ХЕНДЛЕРЫ ==================
@dp.message(CommandStart())
async def start_cmd(m: Message):
    await ensure_user(m.from_user.id)
    await m.answer(t("ru", "choose_lang"), reply_markup=kb_lang())

@dp.message(Command("lang"))
async def lang_cmd(m: Message):
    await ensure_user(m.from_user.id)
    await m.answer(t("ru", "choose_lang"), reply_markup=kb_lang())

@dp.callback_query(F.data.startswith("lang_"))
async def choose_language(c: CallbackQuery):
    lang = c.data.split("_")[1]
    if lang not in ("ru", "kz"):
        lang = "ru"

    await set_lang(c.from_user.id, lang)
    await c.message.answer(t(lang, "welcome"), reply_markup=kb_start(lang), protect_content=True)
    await c.answer()

@dp.callback_query(F.data == "start")
async def start_course(c: CallbackQuery):
    await c.answer()
    await c.message.answer_video(INTRO_VIDEO_ID, protect_content=True)
    asyncio.create_task(send_tariffs_later(c.message.chat.id))

@dp.callback_query(F.data == "back_tariffs")
async def back_tariffs(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    await c.message.answer(t(lang, "tariffs"), reply_markup=kb_tariffs(lang), protect_content=True)
    await c.answer()

# ===== Оплата =====
@dp.callback_query(F.data == "pay_basic")
async def pay_basic(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    await c.message.answer(t(lang, "payment"), reply_markup=kb_payment(lang, "basic"), protect_content=True)
    await c.answer()

@dp.callback_query(F.data == "pay_premium")
async def pay_premium(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    await c.message.answer(t(lang, "payment"), reply_markup=kb_payment(lang, "premium"), protect_content=True)
    await c.answer()

@dp.callback_query(F.data.startswith("paid:"))
async def paid(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    plan = c.data.split(":")[1]
    await set_pending(c.from_user.id, plan)
    await c.message.answer(t(lang, "send_check"), protect_content=True)
    await c.answer()

@dp.message(F.photo | F.document)
async def receive_check(m: Message):
    plan = await get_pending(m.from_user.id)
    if not plan:
        return

    user_lang = await get_lang(m.from_user.id)

    caption = t(
        user_lang,
        "admin_caption",
        full_name=m.from_user.full_name,
        user_id=m.from_user.id,
        plan=plan_label(user_lang, plan)
    )

    if m.photo:
        await bot.send_photo(
            ADMIN_TG_ID,
            m.photo[-1].file_id,
            caption=caption,
            reply_markup=kb_admin(m.from_user.id, plan, user_lang),
            protect_content=True
        )
    else:
        await bot.send_document(
            ADMIN_TG_ID,
            m.document.file_id,
            caption=caption,
            reply_markup=kb_admin(m.from_user.id, plan, user_lang),
            protect_content=True
        )

    await m.answer(t(user_lang, "check_sent"), protect_content=True)

@dp.callback_query(F.data.startswith("ok:"))
async def admin_ok(c: CallbackQuery):
    if c.from_user.id != ADMIN_TG_ID:
        return

    _, uid, plan = c.data.split(":")
    uid_int = int(uid)

    await grant_access(uid_int, plan)
    user_lang = await get_lang(uid_int)

    await bot.send_message(
        uid_int,
        t(user_lang, "payment_confirmed"),
        reply_markup=kb_materials_url(user_lang),
        protect_content=True
    )

    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await c.answer(t("ru", "approved_answer"))

@dp.callback_query(F.data.startswith("no:"))
async def admin_no(c: CallbackQuery):
    if c.from_user.id != ADMIN_TG_ID:
        return

    uid = int(c.data.split(":")[1])
    user_lang = await get_lang(uid)

    await clear_pending(uid)
    await bot.send_message(uid, t(user_lang, "payment_rejected"), protect_content=True)

    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await c.answer(t("ru", "rejected_answer"))

# ===== Материалы =====
@dp.message(Command("materials"))
async def materials_cmd(m: Message):
    lang = await get_lang(m.from_user.id)
    _, paid = await get_access(m.from_user.id)

    if not paid:
        await m.answer(t(lang, "materials_locked"), protect_content=True)
        return

    await m.answer(
        t(lang, "materials_msg"),
        reply_markup=kb_materials_url(lang),
        protect_content=True
    )

# ===== Отзывы =====
@dp.callback_query(F.data == "reviews")
async def reviews(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    review_ids = REVIEW_VIDEO_IDS.get(lang, [])

    if not review_ids:
        await c.message.answer(t(lang, "reviews_not_set"), protect_content=True)
        await c.answer()
        return

    await c.message.answer(
        t(lang, "reviews_found", count=len(review_ids)),
        reply_markup=kb_reviews_menu(lang),
        protect_content=True
    )
    await c.answer()

@dp.callback_query(F.data.startswith("review_show:"))
async def review_show(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    review_ids = REVIEW_VIDEO_IDS.get(lang, [])
    total = len(review_ids)

    if total == 0:
        await c.message.answer(t(lang, "reviews_not_set"), protect_content=True)
        await c.answer()
        return

    try:
        idx = int(c.data.split(":")[1])
    except Exception:
        idx = 0

    if idx < 0 or idx >= total:
        idx = 0

    await c.answer()

    await c.message.answer_video(
        video=review_ids[idx],
        caption=t(lang, "review_caption", num=idx + 1, total=total),
        reply_markup=kb_review_nav(lang, idx, total),
        protect_content=True
    )

# ================== ЗАПУСК ==================
async def main():
    db_init()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
