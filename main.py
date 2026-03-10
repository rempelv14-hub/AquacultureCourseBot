import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart

BOT_TOKEN = "8604598526:AAEN2GGPelc5_QEX6FlZ5kFZjO4NaW-iIxk"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(m: Message):
    await m.answer("Отправь мне видео или файл, и я покажу file_id")


@dp.message(F.video)
async def get_video_id(m: Message):
    file_id = m.video.file_id
    print("VIDEO file_id:", file_id)
    await m.answer(f"🎬 VIDEO file_id:\n<code>{file_id}</code>")
