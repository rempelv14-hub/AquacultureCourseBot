import os
import asyncio
import sqlite3
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest

# ================== ЛОГИ ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ================== НАСТРОЙКИ ==================
BOT_TOKEN = os.getenv("BOT_TOKEN") or "PASTE_YOUR_BOT_TOKEN_HERE"
if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
    raise RuntimeError("BOT_TOKEN не задан. Вставь токен в код или передай через переменную окружения BOT_TOKEN.")

ADMIN_TG_ID = 632308904
DELAY_SECONDS = 1 * 60
DB_PATH = "bot.db"

SUPPORT_WA_LINK = "https://wa.me/77072102513"

# ================== VIDEO file_id ==================
INTRO_VIDEO_IDS = {
    "ru": "BAACAgIAAxkBAANpaaRSWp8aOkE3mcivVcQDJ9hEAAECAAIOkgACuEEgSZZk99fCbt-oOgQ",
    "kz": "BAACAgIAAxkBAAIBc2mtqNxyStaoSE1uyjXCXFDK8hgoAAINoQACGNFpSfLvyNZl-xbfOgQ",
}

REVIEW_VIDEO_IDS = {
    "ru": [
        "BAACAgIAAxkBAAN3aaRTMrIxxmDfUV4fDtcL_WqA7VgAAieSAAK4QSBJ0AABt8XJic8LOgQ",
        "BAACAgIAAxkBAAN1aaRTG8n4WCTld4QhNf4nBtm6c3kAAiCSAAK4QSBJwJLxdJEE2VU6BA",
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

# ================== MODULES file_id ==================
MODULE_VIDEO_IDS = {
    "ru": {
        "module_1": [
            "BAACAgIAAxkBAAICOWmwZpyYJqqik0OJxa1TJffEKN88AAL_nwAC356ISTIXISU-fwh4OgQ",
            "BAACAgIAAxkBAAICO2mwaXQaT_y1EKIg_J7U1GjLtVgmAAIwoAAC356ISRNercOELyu4OgQ",
            "BAACAgIAAxkBAAICPWmwaanIBhKP4ox4iOYmXl9clxMNAAIzoAAC356ISd2EVE_WKjdfOgQ",
            "BAACAgIAAxkBAAICS2mwbBd-Te5JMV6YXexG25mEqDnXAAK4oAAC356ISbfmQj_4TMvAOgQ",
        ],
        "module_2": [
            "BAACAgIAAxkBAAICQWmwaq5pBxYBbuuJDuB5LfYg_iJtAAJjoAAC356ISf_9HOwEW9BMOgQ",
            "BAACAgIAAxkBAAID6mmy92sEXWJd3wxj2SFwt-0DKk1ZAAJvjgAC2kOYSZS-VEkeZLlPOgQ",
            "BAACAgIAAxkBAAICRWmwau7nVaBT67G7NtrEEtRGjBg4AAJuoAAC356IScWl85yxPswXOgQ",
            "BAACAgIAAxkBAAICSWmwa594MnTO-gb4Y0aUc5QT1P1iAAKSoAAC356ISb2_P2ehh1gwOgQ",
        ],
        "module_3": [
            "BAACAgIAAxkBAAICTWmwbKMY-YlKMnwUx9jiaSrrjCF6AAK-oAAC356ISd4oan-gCGmVOgQ",
            "BAACAgIAAxkBAAICT2mwbLcZQzXUy0_xUhlD3pMq6w53AALAoAAC356ISbvtQ86CbO1FOgQ",
            "BAACAgIAAxkBAAICUWmwbQdniQl3qlQzTGOAbo51YzAgAALFoAAC356ISRhWi3iuKYbROgQ",
        ],
        "module_4": [
            "BAACAgIAAxkBAAICU2mwbZyfzD24aZeFA8erIO3YMsraAALKoAAC356ISXmCYLT9jomHOgQ",
        ],
        "module_5": [
            "BAACAgIAAxkBAAICVWmwbcgTD5bMUUENyBIyfV3gB3b_AALNoAAC356ISZznewy9kEeROgQ",
            "BAACAgIAAxkBAAICV2mwbeglTjcgVo3QgSpJdr-420CkAALPoAAC356ISfAQsUfywxLgOgQ",
            "BAACAgIAAxkBAAICWWmwbjn5ZaE6_B7Qd-s_iPziCU9-AALYoAAC356ISSKUoLar80vcOgQ",
            "BAACAgIAAxkBAAICW2mwbnn9VhpTYAp6EHwEIQfUbYPMAALboAAC356ISYzfuVObww-eOgQ",
            "BAACAgIAAxkBAAICXWmwboeEOgabha_g36hKvGAfH2AYAALcoAAC356ISQ-_HMr5N8l1OgQ",
            "BAACAgIAAxkBAAID5Gmy500mz6HAM0oQRjSdNmtgn5ROAAIqiwAC2kOQSe3SqNYPMa5mOgQ",
        ],
    },
    "kz": {
        "module_1": [
            "BAACAgIAAxkBAAIB1GmwQYLyE14iK2HRAVHd1vkJIPEwAAJ8nQAC356ISeVbx5xGApzSOgQ",
            "BAACAgIAAxkBAAIB-mmwRY41_mRkr_yWte31cLRLUxv9AAOeAALfnohJbUBW5gIlT206BA",
        ],
        "module_2": [
            "BAACAgIAAxkBAAID6Gmy9o4oP44_TRUDK58ccjr0JGAxAAJpjgAC2kOYST7XH_7xk0M2OgQ",
            "BAACAgIAAxkBAAID8Gmy-SlDuGbl3ASYEfZ2HPZXTENTAAKEjgAC2kOYSRYJiUxM-TRpOgQ ",
            "BAACAgIAAxkBAAID7Gmy982nUHeATK5d1mXEiC9DgAxoAAJ0jgAC2kOYSUFWtByHqfxGOgQ ",
        ],
        "module_3": [
            "BAACAgIAAxkBAAID8mmy-4Wzvy1fyPKmOYcxlTNrM3XIAAKSjgAC2kOYSSMWX31UsycvOgQ",
            "BAACAgIAAxkBAAID9Gmy_Jr47hTgIT-JquSRnuSeKdWJAAKojgAC2kOYSYyGmTCTtPACOgQ",

        ],
        "module_4": [
            "BAACAgIAAxkBAAICEGmwT5FGsLS9jylOCmxympEPePeMAAKcngAC356ISdm1z1rMBh59OgQ",
            "BAACAgIAAxkBAAICFmmwUOVMETRXKZnbwfjg-GwdnZv6AAKsngAC356ISVOz9G0tL1D5OgQ",

        ],
        "module_5": [
            "BAACAgIAAxkBAAICIWmwVEFhgm0ZZU1oLzpyiGdXjmnsAALWngAC356ISfXCjIs23bPKOgQ",
            "BAACAgIAAxkBAAICI2mwVdj3rC5vr0FYsr2ca7I6-N3OAALxngAC356ISTbIV-k6jC4fOgQ",
            "BAACAgIAAxkBAAICKGmwVwMWNU2Su9_r3--9kePX3eyxAAIBnwAC356ISRMZyhAVVh04OgQ",
            "BAACAgIAAxkBAAICKmmwV593jJg7x7T6axtKpaHPDo-FAAIHnwAC356ISdUgdsvRWp5KOgQ",
            "BAACAgIAAxkBAAICLmmwWMaHPA8MrixhElf9QrcPBOgcAAITnwAC356ISfUNbjiv2niHOgQ"
            "BAACAgIAAxkBAAID4mmy5qWoXGJForS1NPouS2voO8QzAAIiiwAC2kOQSSHht26rSatPOgQ",
        ],
    }
}

# ================== DB ==================
DB_LOCK = asyncio.Lock()
START_TASKS: dict[int, asyncio.Task] = {}


def _connect():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    return con


def _protected_kwargs():
    return {
        "protect_content": True
    }


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
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS pending (
            user_id INTEGER PRIMARY KEY,
            plan TEXT
        )
        """)

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


async def get_lang(user_id: int) -> str:
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
            con.execute("REPLACE INTO pending VALUES (?, ?)", (user_id, plan))
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
            current_lang = con.execute("SELECT lang FROM users WHERE user_id=?", (user_id,)).fetchone()
            lang = current_lang[0] if current_lang and current_lang[0] else "ru"

            con.execute(
                "REPLACE INTO users (user_id, plan, is_paid, paid_at, lang) VALUES (?, ?, ?, ?, ?)",
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

# ================== ТЕКСТЫ ==================
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
    "🔥 <b>АКЦИЯ ШЕКТЕУЛІ</b>\n"
    "⏳ Жеңілдік тек қазір қолжетімді\n\n"

    "Тариф 1: «Премиум сүйемелдеу»\n"
    "❌ 250 000 тг\n"
    "✅ <b>150 000 тг (40% жеңілдік)</b>\n\n"

    "Бұл тарифке мыналар кіреді:\n"
    "✅ Бейне курстарға қолжетімділік (барлық оқу базасы).\n"
    "✅ 6 ай толық сүйемелдеу.\n"
    "✅ 6 ай ішінде клиент бизнес бойынша кез келген сұрақпен хабарласа алады.\n"
    "✅ Чат арқылы қолдау.\n"
    "✅ Аптасына 1 рет бейне қоңырау.\n\n"

    "━━━━━━━━━━━━━━━━━━━━━━\n\n"

"Тариф 2: «Базалық оқу»\n" 
"❌ 150 000 тг\n" 
"✅ <b>105 000 тг (30% жеңілдік)</b>\n\n" "Бұл тарифке мыналар кіреді:\n" "
 ✅ Бейне курстарға қолжетімділік (барлық оқу базасы).\n" "
 ✅ 3 ай қолдау.\n" "
 ✅ 3 ай ішінде клиент чат арқылы сұрақ қоя алады.\n" "
 ✅ Маңызды: бейне қоңыраулар қарастырылмаған.\n\n"

    "⚠️ Орын саны шектеулі"
),
        "pay_basic_btn": "💳 Оплатить Базовый",
        "pay_premium_btn": "💳 Оплатить Премиум",
        "reviews_btn": "⭐ Отзывы",
        "support_btn": "🛟 Поддержка",
        "payment": (
            "💳 <b>Оплата Kaspi</b>\n\n"
            "Получатель: <b>YERLAN KEGENOV</b>\n"
            "Номер карты: <b>4400 4302 0609 7443</b>\n\n"
            "После оплаты нажмите <b>«Я оплатил»</b> и отправьте чек."
        ),
        "i_paid_btn": "✅ Я оплатил",
        "send_check": "📎 Отправьте чек (фото или файл)",
        "check_sent": "⏳ Чек отправлен админу. Ожидайте подтверждения.",
        "materials_locked": "🔒 Материалы закрыты.\n\nДоступ откроется после оплаты и подтверждения чека администратором.",
        "modules_btn": "📚 Модули курса",
        "payment_confirmed": "✅ Оплата подтверждена!\n\nНиже кнопка для доступа к модулям курса 👇",
        "payment_rejected": "❌ Оплата отклонена. Свяжитесь с поддержкой.",
        "materials_msg": "📚 Выберите модуль курса:",
        "modules_msg": "📚 Выберите модуль курса:",
        "module_1_btn": "1️⃣ Модуль 1",
        "module_2_btn": "2️⃣ Модуль 2",
        "module_3_btn": "3️⃣ Модуль 3",
        "module_4_btn": "4️⃣ Модуль 4",
        "module_5_btn": "5️⃣ Модуль 5",
        "module_caption": "📘 {module_name} | Урок {lesson_num}",
        "back_modules_btn": "⬅️ Назад к модулям",
        "reviews_found": "⭐ Найдено отзывов: {count}",
        "show_reviews_btn": "▶️ Показать отзывы",
        "back_tariffs_btn": "⬅️ Назад к тарифам",
        "next_review_btn": "▶️ Следующий отзыв",
        "review_caption": "⭐ Отзыв {num} из {total}",
        "reviews_not_set": "⚠️ Отзывы не настроены.",
        "admin_caption": "🧾 Чек на проверку\n\nПользователь: {full_name}\nID: {user_id}\nТариф: {plan}",
        "admin_ok_btn": "✅ Подтвердить",
        "admin_no_btn": "❌ Отклонить",
        "approved_answer": "Подтверждено",
        "rejected_answer": "Отклонено",
        "plan_basic": "Базовый",
        "plan_premium": "Премиум",
        "intro_fail": "Не удалось отправить интро. Проверьте file_id для выбранного языка.",
        "module_not_set": "⚠️ Модуль пока не настроен.",
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
"Тариф 1: «Премиум сопровождение» — 250 000 тг\n\n"
"В этот тариф входит:\n"
"✅ Доступ к видеокурсам (вся обучающая база).\n"
"✅ 6 месяцев полного сопровождения.\n"
"✅ В течение 6 месяцев клиент может обращаться с любыми вопросами по бизнесу.\n"
"✅ Поддержка через чат.\n"
"✅ 1 видеозвонок в неделю.\n\n"
"━━━━━━━━━━━━━━━━━━━━━━\n\n"
"Тариф 2: «Базовое обучение» — 150 000 тг\n\n"
"В этот тариф входит:\n"
"✅ Доступ к видеокурсам (вся обучающая база).\n"
"✅ Поддержка в течение 3 месяцев.\n"
"✅ В течение 3 месяцев клиент может задавать вопросы через чат.\n"
"✅ Важно: видеозвонки не предусмотрены."

        "pay_basic_btn": "💳 Базалықты төлеу",
        "pay_premium_btn": "💳 Премиумды төлеу",
        "reviews_btn": "⭐ Пікірлер",
        "support_btn": "🛟 Қолдау",
        "payment": (
            "💳 <b>Kaspi арқылы төлем</b>\n\n"
            "Алушы: <b>YERLAN KEGENOV</b>\n"
            "Карта нөмірі: <b>4400 4302 0609 7443</b>\n\n"
            "Төлем жасағаннан кейін <b>«Мен төледім»</b> батырмасын басып, чекті жіберіңіз."
        ),
        "i_paid_btn": "✅ Мен төледім",
        "send_check": "📎 Чекті жіберіңіз (фото немесе файл)",
        "check_sent": "⏳ Чек әкімшіге жіберілді. Растауды күтіңіз.",
        "materials_locked": "🔒 Материалдар жабық.\n\nҚолжетімділік төлем жасалып, әкімші чек растағаннан кейін ашылады.",
        "modules_btn": "📚 Курс модульдері",
        "payment_confirmed": "✅ Төлем расталды!\n\nТөменде курс модульдеріне кіру батырмасы берілген 👇",
        "payment_rejected": "❌ Төлем қабылданбады. Қолдау қызметіне хабарласыңыз.",
        "materials_msg": "📚 Модульді таңдаңыз:",
        "modules_msg": "📚 Модульді таңдаңыз:",
        "module_1_btn": "1️⃣ Модуль 1",
        "module_2_btn": "2️⃣ Модуль 2",
        "module_3_btn": "3️⃣ Модуль 3",
        "module_4_btn": "4️⃣ Модуль 4",
        "module_5_btn": "5️⃣ Модуль 5",
        "module_caption": "📘 {module_name} | Сабақ {lesson_num}",
        "back_modules_btn": "⬅️ Модульдерге қайту",
        "reviews_found": "⭐ Табылған пікірлер саны: {count}",
        "show_reviews_btn": "▶️ Пікірлерді көрсету",
        "back_tariffs_btn": "⬅️ Тарифтерге қайту",
        "next_review_btn": "▶️ Келесі пікір",
        "review_caption": "⭐ Пікір {num} / {total}",
        "reviews_not_set": "⚠️ Пікірлер бапталмаған.",
        "admin_caption": "🧾 Тексеруге чек\n\nПайдаланушы: {full_name}\nID: {user_id}\nТариф: {plan}",
        "admin_ok_btn": "✅ Растау",
        "admin_no_btn": "❌ Қабылдамау",
        "approved_answer": "Расталды",
        "rejected_answer": "Қабылданбады",
        "plan_basic": "Базалық",
        "plan_premium": "Премиум",
        "intro_fail": "Интро жіберілмеді. Таңдалған тіл үшін file_id тексеріңіз.",
        "module_not_set": "⚠️ Модуль әлі бапталмаған.",
    }
}


def t(lang: str, key: str, **kwargs):
    lang = lang if lang in TEXTS else "ru"
    text = TEXTS[lang][key]
    return text.format(**kwargs) if kwargs else text


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


def kb_materials(lang: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "module_1_btn"), callback_data="module:module_1")
    kb.button(text=t(lang, "module_2_btn"), callback_data="module:module_2")
    kb.button(text=t(lang, "module_3_btn"), callback_data="module:module_3")
    kb.button(text=t(lang, "module_4_btn"), callback_data="module:module_4")
    kb.button(text=t(lang, "module_5_btn"), callback_data="module:module_5")
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


def kb_back_modules(lang: str):
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "back_modules_btn"), callback_data="back_modules")
    kb.button(text=t(lang, "support_btn"), url=SUPPORT_WA_LINK)
    kb.adjust(1)
    return kb.as_markup()

# ================== БОТ ==================
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ================== ФОН ==================
async def send_tariffs_later(user_id: int, chat_id: int):
    try:
        await asyncio.sleep(DELAY_SECONDS)
        lang = await get_lang(user_id)
        await bot.send_message(chat_id, t(lang, "before_tariffs"), **_protected_kwargs())
        await bot.send_message(
            chat_id,
            t(lang, "tariffs"),
            reply_markup=kb_tariffs(lang),
            **_protected_kwargs()
        )
    except asyncio.CancelledError:
        logging.info("Отложенная отправка тарифов отменена для chat_id=%s", chat_id)
        raise
    finally:
        START_TASKS.pop(chat_id, None)

# ================== ХЕНДЛЕРЫ ==================
@dp.message(CommandStart())
async def start_cmd(m: Message):
    await ensure_user(m.from_user.id)
    await m.answer(t("ru", "choose_lang"), reply_markup=kb_lang(), **_protected_kwargs())


@dp.message(Command("lang"))
async def lang_cmd(m: Message):
    await ensure_user(m.from_user.id)
    await m.answer(t("ru", "choose_lang"), reply_markup=kb_lang(), **_protected_kwargs())


@dp.callback_query(F.data.startswith("lang_"))
async def choose_language(c: CallbackQuery):
    lang = c.data.split("_")[1]
    if lang not in ("ru", "kz"):
        lang = "ru"

    await set_lang(c.from_user.id, lang)
    saved_lang = await get_lang(c.from_user.id)
    logging.info("Пользователь %s выбрал язык %s", c.from_user.id, saved_lang)

    await c.message.answer(
        t(saved_lang, "welcome"),
        reply_markup=kb_start(saved_lang),
        **_protected_kwargs()
    )
    await c.answer()


@dp.callback_query(F.data == "start")
async def start_course(c: CallbackQuery):
    await c.answer()

    user_id = c.from_user.id
    chat_id = c.message.chat.id
    lang = await get_lang(user_id)
    intro_video = INTRO_VIDEO_IDS.get(lang, INTRO_VIDEO_IDS["ru"])

    logging.info("START user_id=%s lang=%s intro_id=%s", user_id, lang, intro_video)

    try:
        await bot.send_video(
            chat_id=chat_id,
            video=intro_video,
            **_protected_kwargs()
        )
    except TelegramBadRequest as e:
        logging.exception("Ошибка интро user_id=%s lang=%s", user_id, lang)
        await c.message.answer(
            f"{t(lang, 'intro_fail')}\n\n<code>{e}</code>",
            **_protected_kwargs()
        )
        return
    except Exception as e:
        logging.exception("Неожиданная ошибка интро user_id=%s lang=%s", user_id, lang)
        await c.message.answer(
            f"{t(lang, 'intro_fail')}\n\n<code>{e}</code>",
            **_protected_kwargs()
        )
        return

    old_task = START_TASKS.get(chat_id)
    if old_task and not old_task.done():
        old_task.cancel()

    START_TASKS[chat_id] = asyncio.create_task(send_tariffs_later(user_id, chat_id))


@dp.callback_query(F.data == "back_tariffs")
async def back_tariffs(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    await c.message.answer(
        t(lang, "tariffs"),
        reply_markup=kb_tariffs(lang),
        **_protected_kwargs()
    )
    await c.answer()


@dp.callback_query(F.data == "pay_basic")
async def pay_basic(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    await c.message.answer(
        t(lang, "payment"),
        reply_markup=kb_payment(lang, "basic"),
        **_protected_kwargs()
    )
    await c.answer()


@dp.callback_query(F.data == "pay_premium")
async def pay_premium(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    await c.message.answer(
        t(lang, "payment"),
        reply_markup=kb_payment(lang, "premium"),
        **_protected_kwargs()
    )
    await c.answer()


@dp.callback_query(F.data.startswith("paid:"))
async def paid(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    plan = c.data.split(":")[1]
    await set_pending(c.from_user.id, plan)
    await c.message.answer(t(lang, "send_check"), **_protected_kwargs())
    await c.answer()


@dp.message(F.photo)
async def receive_check_photo(m: Message):
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

    await bot.send_photo(
        ADMIN_TG_ID,
        m.photo[-1].file_id,
        caption=caption,
        reply_markup=kb_admin(m.from_user.id, plan, user_lang),
        **_protected_kwargs()
    )

    await m.answer(t(user_lang, "check_sent"), **_protected_kwargs())


@dp.message(F.document)
async def receive_check_document(m: Message):
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

    await bot.send_document(
        ADMIN_TG_ID,
        m.document.file_id,
        caption=caption,
        reply_markup=kb_admin(m.from_user.id, plan, user_lang),
        **_protected_kwargs()
    )

    await m.answer(t(user_lang, "check_sent"), **_protected_kwargs())


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
        reply_markup=kb_materials(user_lang),
        **_protected_kwargs()
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
    await bot.send_message(uid, t(user_lang, "payment_rejected"), **_protected_kwargs())

    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await c.answer(t("ru", "rejected_answer"))


@dp.message(Command("materials"))
async def materials_cmd(m: Message):
    lang = await get_lang(m.from_user.id)
    _, paid = await get_access(m.from_user.id)

    if not paid:
        await m.answer(t(lang, "materials_locked"), **_protected_kwargs())
        return

    await m.answer(
        t(lang, "modules_msg"),
        reply_markup=kb_materials(lang),
        **_protected_kwargs()
    )


@dp.callback_query(F.data == "back_modules")
async def back_modules(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    _, paid = await get_access(c.from_user.id)

    if not paid:
        await c.message.answer(t(lang, "materials_locked"), **_protected_kwargs())
        await c.answer()
        return

    await c.message.answer(
        t(lang, "modules_msg"),
        reply_markup=kb_materials(lang),
        **_protected_kwargs()
    )
    await c.answer()


@dp.callback_query(F.data.startswith("module:"))
async def send_module(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    _, paid = await get_access(c.from_user.id)

    if not paid:
        await c.message.answer(t(lang, "materials_locked"), **_protected_kwargs())
        await c.answer()
        return

    module_key = c.data.split(":")[1]
    module_videos = MODULE_VIDEO_IDS.get(lang, {}).get(module_key, [])

    if not module_videos:
        await c.message.answer(t(lang, "module_not_set"), **_protected_kwargs())
        await c.answer()
        return

    module_titles = {
        "module_1": t(lang, "module_1_btn"),
        "module_2": t(lang, "module_2_btn"),
        "module_3": t(lang, "module_3_btn"),
        "module_4": t(lang, "module_4_btn"),
        "module_5": t(lang, "module_5_btn"),
    }

    await c.answer()

    for i, video_id in enumerate(module_videos, start=1):
        await bot.send_video(
            chat_id=c.message.chat.id,
            video=video_id,
            caption=t(lang, "module_caption", module_name=module_titles[module_key], lesson_num=i),
            **_protected_kwargs()
        )

    await bot.send_message(
        c.message.chat.id,
        t(lang, "modules_msg"),
        reply_markup=kb_back_modules(lang),
        **_protected_kwargs()
    )


@dp.callback_query(F.data == "reviews")
async def reviews(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    review_ids = REVIEW_VIDEO_IDS.get(lang, [])

    if not review_ids:
        await c.message.answer(t(lang, "reviews_not_set"), **_protected_kwargs())
        await c.answer()
        return

    await c.message.answer(
        t(lang, "reviews_found", count=len(review_ids)),
        reply_markup=kb_reviews_menu(lang),
        **_protected_kwargs()
    )
    await c.answer()


@dp.callback_query(F.data.startswith("review_show:"))
async def review_show(c: CallbackQuery):
    lang = await get_lang(c.from_user.id)
    review_ids = REVIEW_VIDEO_IDS.get(lang, [])
    total = len(review_ids)

    if total == 0:
        await c.message.answer(t(lang, "reviews_not_set"), **_protected_kwargs())
        await c.answer()
        return

    try:
        idx = int(c.data.split(":")[1])
    except Exception:
        idx = 0

    if idx < 0 or idx >= total:
        idx = 0

    await c.answer()
    await bot.send_video(
        chat_id=c.message.chat.id,
        video=review_ids[idx],
        caption=t(lang, "review_caption", num=idx + 1, total=total),
        reply_markup=kb_review_nav(lang, idx, total),
        **_protected_kwargs()
    )

# ================== ЗАПУСК ==================
async def main():
    db_init()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


