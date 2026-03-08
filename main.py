import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

# ВСТАВЬ СВОЙ ТОКЕН
BOT_TOKEN = "ТВОЙ_BOT_TOKEN"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()


# Старт
@dp.message()
async def start(m: Message):
    await m.answer("Отправь мне видео или файл, и я покажу file_id")


# Если это видео
@dp.message(F.video)
async def get_video_id(m: Message):
    file_id = m.video.file_id
    await m.answer(
        f"🎬 VIDEO file_id:\n<code>{file_id}</code>"
    )


# Если это файл (например mov)
@dp.message(F.document)
async def get_document_id(m: Message):
    file_id = m.document.file_id
    await m.answer(
        f"📁 DOCUMENT file_id:\n<code>{file_id}</code>"
    )


async def main():
    print("Бот запущен. Отправь файл...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
