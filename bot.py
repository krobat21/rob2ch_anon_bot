import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = 'YOUR_BOT_TOKEN'
OWNER_ID = 123456789  # Укажи здесь Telegram ID администратора

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

counter_file = "counter.txt"
mapping_file = "messages_map.json"

# ========== Вспомогательные функции ==========

def get_next_id():
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

# ========== Команды ==========

@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.reply(
        "Привет! Напиши сюда анонимное сообщение, и оно будет отправлено администратору."
    )

# ========== Обработка любых сообщений ==========

@dp.message_handler(content_types=types.ContentType.ANY)
async def anonymous_message(message: types.Message):
    if message.text and message.text.startswith('/start'):
        return

    message_id = get_next_id()
    user = message.from_user
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = f"@{user.username}" if user.username else "Без ника"

    content_header = f"📥 Анонимное сообщение №{message_id}:"
    sender_info = f"👤 Отправитель: {first_name} {last_name} {username}"

    # Отправка админу
    if message.text:
        await bot.send_message(OWNER_ID, f"{content_header}\n\n{message.text}\n\n{sender_info}")
    elif message.photo:
        await bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=f"{content_header}\n\n{sender_info}")
    elif message.document:
        await bot.send_document(OWNER_ID, message.document.file_id, caption=f"{content_header}\n\n{sender_info}")
    elif message.video:
        await bot.send_video(OWNER_ID, message.video.file_id, caption=f"{content_header}\n\n{sender_info}")
    else:
        await bot.send_message(OWNER_ID, f"{content_header}\n\nНеизвестный тип сообщения\n\n{sender_info}")

    await message.reply("✅ Ваше сообщение отправлено!")

# ========== Запуск бота ==========

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
