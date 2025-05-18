import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '7785178596:AAFLk9YvCxtZe-HrqK3c5S3QC8u2rPGh8jw'
OWNER_ID = 58715694

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

mapping_file = "messages_map.json"

def load_mapping():
    if os.path.exists(mapping_file):
        with open(mapping_file, "r") as f:
            return json.load(f)
    return {}

def save_mapping(mapping):
    with open(mapping_file, "w") as f:
        json.dump(mapping, f)

class ReplyState(StatesGroup):
    waiting_for_admin = State()

@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.reply(
        "Привет! Теперь можешь отправить свое анонимное сообщение."
    )

@dp.message_handler(content_types=types.ContentType.ANY)
async def anonymous_message(message: types.Message):
    if message.text and message.text.startswith('/start'):
        return

    user = message.from_user
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = f"@{user.username}" if user.username else "Без ника"

    user_info = (
        f'⚡️Анонимное сообщение от пользователя "{first_name}" "{last_name}" {username}'
    )

    # Генерируем уникальный message_id для обратной связи
    message_id = str(message.message_id) + "_" + str(user.id)

    # Сохраняем user_id по message_id
    mapping = load_mapping()
    mapping[message_id] = user.id
    save_mapping(mapping)

    # Готовим кнопку "Ответить"
    reply_kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Ответить", callback_data=f"reply_{message_id}")
    )

    # 1. Текст
    if message.text:
        await bot.send_message(
            OWNER_ID,
            f"{user_info}\n\n{message.text}",
            reply_markup=reply_kb
        )
    # 2. Фото
    elif message.photo:
        await bot.send_message(OWNER_ID, user_info, reply_markup=reply_kb)
        await bot.send_photo(
            OWNER_ID,
            message.photo[-1].file_id,
            caption=message.caption or ""
        )
    elif message.document:
        await bot.send_message(OWNER_ID, user_info, reply_markup=reply_kb)
        await bot.send_document(
            OWNER_ID,
            message.document.file_id,
            caption=message.caption or ""
        )
    elif message.video:
        await bot.send_message(OWNER_ID, user_info, reply_markup=reply_kb)
        await bot.send_video(
            OWNER_ID,
            message.video.file_id,
            caption=message.caption or ""
        )
    elif message.sticker:
        await bot.send_message(OWNER_ID, user_info, reply_markup=reply_kb)
        await bot.send_sticker(
            OWNER_ID,
            message.sticker.file_id
        )
    elif message.voice:


await bot.send_message(OWNER_ID, user_info, reply_markup=reply_kb)
        await bot.send_voice(
            OWNER_ID,
            message.voice.file_id,
            caption=message.caption or ""
        )
    elif message.audio:
        await bot.send_message(OWNER_ID, user_info, reply_markup=reply_kb)
        await bot.send_audio(
            OWNER_ID,
            message.audio.file_id,
            caption=message.caption or ""
        )
    else:
        await bot.send_message(OWNER_ID, f"{user_info}\n[Тип сообщения не поддерживается ботом для отправки]", reply_markup=reply_kb)

    await message.reply("Ваше анонимное обращение отправлено!")

# Обработка кнопки "Ответить"
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('reply_'))
async def process_callback_reply(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != OWNER_ID:
        return await callback_query.answer("Только админ может отвечать!", show_alert=True)
    message_id = callback_query.data.split('reply_')[1]
    await state.update_data(answer_to_id=message_id)
    await bot.send_message(OWNER_ID, "Введите текст ответа пользователю:")
    await ReplyState.waiting_for_admin.set()
    await callback_query.answer()

@dp.message_handler(state=ReplyState.waiting_for_admin)
async def process_admin_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get('answer_to_id')
    mapping = load_mapping()
    user_id = mapping.get(message_id)
    if not user_id:
        await message.reply("Ошибка: пользователь не найден (возможно, он уже не онлайн).")
        await state.finish()
        return
    try:
        await bot.send_message(user_id, "‼️ Получен ответ на вашу анонимку!")
        await bot.send_message(user_id, message.text)
        await message.reply("Ответ отправлен пользователю.")
    except Exception as e:
        await message.reply("Ошибка отправки пользователю.")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp)
