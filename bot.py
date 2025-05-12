import os
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = 'ТОКЕН_ТВОЕГО_БОТА'
OWNER_ID = ТВОЙ_USER_ID  # целое число!

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

counter_file = "counter.txt"

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

# 1. При запуске бота /start - приветствие пользователю
@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.reply(
        "Привет! Наверное ты хочешь что-то написать... НУ ДАВАЙ, СДЕЛАЙ ЭТО! Напиши сообщение и я его получу. "
        "Но ответить, увы, не смогу. Но может оно и к лучшему?"
    )

@dp.message_handler(content_types=types.ContentType.ANY)
async def anonymous_message(message: types.Message):
    if message.text and message.text.startswith('/start'):
        return  # Позволяет не дублировать приветствие

    message_id = get_next_id()
    user = message.from_user
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    user_link = f'<a href="tg://user?id={user.id}">{user.id}</a>'

    notification = (
        f'⚡️Новое анонимное обращение №{message_id} от пользователя "{first_name}" "{last_name}" {user_link}'
    )
    content_header = f"📥 Анонимное сообщение №{message_id}:"

    # Уведомление о поступлении с данными пользователя
    await bot.send_message(OWNER_ID, notification, parse_mode='HTML')

    if message.text:
        await bot.send_message(OWNER_ID, f"{content_header}\n\n{message.text}")

    if message.photo:
        file_id = message.photo[-1].file_id
        await bot.send_photo(
            OWNER_ID,
            file_id,
            caption=content_header + (("\n" + message.caption) if message.caption else "")
        )

    if message.document:
        await bot.send_document(
            OWNER_ID,
            message.document.file_id,
            caption=content_header + (("\n" + message.caption) if message.caption else "")
        )

    if message.video:
        await bot.send_video(
            OWNER_ID,
            message.video.file_id,
            caption=content_header + (("\n" + message.caption) if message.caption else "")
        )

    await message.reply("Ваше анонимное обращение отправлено!")

if __name__ == '__main__':
    executor.start_polling(dp)
