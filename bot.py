import os
import json
from threading import Thread
from flask import Flask

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = 'ТВОЙ_ТОКЕН'
OWNER_ID = 123456789  # укажи свой

app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

flask_thread = Thread(target=run_flask)
flask_thread.start()

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

counter_file = "counter.txt"
mapping_file = "messages_map.json"

# Храним map: {message_id: user_id}
def load_mapping():
    if os.path.exists(mapping_file):
        with open(mapping_file, "r") as f:
            return json.load(f)
    return {}

def save_mapping(mapping):
    with open(mapping_file, "w") as f:
        json.dump(mapping, f)

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

# FSM для ответа на сообщение
class ReplyState(StatesGroup):
    waiting_for_text = State()

@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.reply(
        "Привет! Наверное ты хочешь что-то написать... Напиши сообщение, но учти, ответить, увы, не смогу. Но может оно и к лучшему?"
    )

@dp.message_handler(content_types=types.ContentType.ANY)
async def anonymous_message(message: types.Message):
    if message.text and message.text.startswith('/start'):
        return

    message_id = get_next_id()
    user_id = message.from_user.id

    # Сохраняем соответствие обращения и пользователя
    mapping = load_mapping()
    mapping[str(message_id)] = user_id
    save_mapping(mapping)

    user = message.from_user
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = f"@{user.username}" if user.username else "Без ника"
    phone = "Без телефона"
    if message.contact and message.contact.phone_number:
        phone = message.contact.phone_number

    notification = (
        f'⚡️Новое анонимное обращение №{message_id} от пользователя "{first_name}" "{last_name}" {username}, телефон: {phone}'
    )
    content_header = f"📥 Анонимное сообщение №{message_id}:"

    # Кнопка ответить
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Ответить на сообщение", callback_data=f"reply_{message_id}")
    )

    await bot.send_message(OWNER_ID, notification)
    # разный контент
    if message.text:
        await bot.send_message(OWNER_ID, f"{content_header}\n\n{message.text}", reply_markup=keyboard)
    elif message.photo:
        file_id = message.photo[-1].file_id
        await bot.send_photo(OWNER_ID, file_id, caption=content_header + (("\n" + message.caption) if message.caption else ""), reply_markup=keyboard)
    elif message.document:
        await bot.send_document(OWNER_ID, message.document.file_id, caption=content_header + (("\n" + message.caption) if message.caption else ""), reply_markup=keyboard)
elif message.video:
        await bot.send_video(OWNER_ID, message.video.file_id, caption=content_header + (("\n" + message.caption) if message.caption else ""), reply_markup=keyboard)

    await message.reply("Ваше анонимное обращение отправлено!")

# Обработка кнопки "Ответить"
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('reply_'))
async def process_callback_reply(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != OWNER_ID:
        return await callback_query.answer("Только админ может отвечать!", show_alert=True)
    message_id = callback_query.data.split('_')[1]
    await state.update_data(answer_to_id=message_id)
    await bot.send_message(OWNER_ID, f"Введите ответ для обращения №{message_id}:")
    await ReplyState.waiting_for_text.set()
    await callback_query.answer()

@dp.message_handler(state=ReplyState.waiting_for_text, content_types=types.ContentType.ANY)
async def process_admin_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get('answer_to_id')
    mapping = load_mapping()
    user_id = mapping.get(str(message_id))
    if not user_id:
        await message.reply("Ошибка: пользователь не найден.")
        await state.finish()
        return
    try:
        await bot.send_message(user_id, "‼️ Получен ответ на вашу анонимку!")
        if message.text:
            await bot.send_message(user_id, message.text)
        elif message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
        elif message.document:
            await bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
        elif message.video:
            await bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
        else:
            await bot.send_message(user_id, "Получен ответ, но его формат неизвестен.")
        await message.reply("Ответ отправлен пользователю!")
    except Exception as e:
        await message.reply("Ошибка отправки пользователю (вероятно, он заблокировал бота).")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
