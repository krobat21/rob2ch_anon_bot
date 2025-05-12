import os
import asyncio
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = os.environ['7481273027:AAERR7vI_rCaywsfD5cU36CCDyHp6k5L1QQ']
OWNER_ID = int(os.environ['58715694'])

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

counter_file = "counter.txt"

async def get_next_id():
    if not os.path.exists(counter_file):
        with open(counter_file, "w") as f:
            f.write("1")
            return 1
    with open(counter_file, "r+") as f:
        value = int(f.read().strip())
        next_value = value + 1
        f.seek(0)
        f.write(str(next_value))
        f.truncate()
    return next_value

@dp.message_handler(content_types=types.ContentType.ANY)
async def anonymous_message(message: types.Message):
    message_id = await get_next_id()
    notification = f"⚡️Новое анонимное обращение №{message_id}"
    content_header = f"📥 Анонимное сообщение №{message_id}:"

    # Уведомление о поступлении
    await bot.send_message(OWNER_ID, notification)

    if message.text:
        await bot.send_message(OWNER_ID, f"{content_header}\n\n{message.text}")

    if message.photo:
        file_id = message.photo[-1].file_id
        await bot.send_photo(OWNER_ID, file_id, caption=content_header + (("\n" + message.caption) if message.caption else ""))

    if message.document:
        await bot.send_document(OWNER_ID, message.document.file_id, caption=content_header + (("\n" + message.caption) if message.caption else ""))

    if message.video:
        await bot.send_video(OWNER_ID, message.video.file_id, caption=content_header + (("\n" + message.caption) if message.caption else ""))

    await message.reply("Ваше анонимное обращение отправлено!")

if __name__ == '__main__':
    executor.start_polling(dp)
