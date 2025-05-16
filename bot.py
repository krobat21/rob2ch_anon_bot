import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = 'YOUR_BOT_TOKEN'
OWNER_ID = 123456789  # замените на настоящий ID администратора

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

counter_file = "counter.txt"
mapping_file = "messages_map.json"

# ================= Вспомогательные функции =================

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

# ================= Состояния =================

class ReplyState(StatesGroup):
    waiting_for_admin = State()

class UserReplyState(StatesGroup):
    waiting_for_user = State()

# ================= Команды =================

@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.reply(
        "Привет! Напиши сюда анонимное сообщение, и оно дойдет администратору. Ответить можно будет только через кнопки!"
    )

# ================= Пользователь отправляет сообщение =================

@dp.message_handler(content_types=types.ContentType.ANY, state="*")
async def anonymous_message(message: types.Message, state: FSMContext):
    if message.text and message.text.startswith('/start'):
        return

    message_id = get_next_id()
    user_id = message.from_user.id

    mapping = load_mapping()
    mapping[str(message_id)] = user_id
    save_mapping(mapping)

    user = message.from_user
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = f"@{user.username}" if user.username else "Без ника"

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Ответить на сообщение", callback_data=f"reply_{message_id}")
    )

    await bot.send_message(
        OWNER_ID,
        f"⚡️Новое анонимное сообщение №{message_id} от {first_name} {last_name} {username}"
    )

    content_header = f"📥 Анонимное сообщение №{message_id}:"

    if message.text:
        await bot.send_message(OWNER_ID, f"{content_header}\n\n{message.text}", reply_markup=keyboard)
    elif message.photo:
        await bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=content_header, reply_markup=keyboard)
    elif message.document:
        await bot.send_document(OWNER_ID, message.document.file_id, caption=content_header, reply_markup=keyboard)
    elif message.video:
        await bot.send_video(OWNER_ID, message.video.file_id, caption=content_header, reply_markup=keyboard)
    else:
        await bot.send_message(OWNER_ID, f"{content_header} (Неизвестный формат)", reply_markup=keyboard)

    await message.reply("✅ Ваше сообщение отправлено администратору.")

# ================= Админ нажимает «ответить» =================

@dp.callback_query_handler(lambda c: c.data.startswith('reply_'))
async def process_callback_reply(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.from_user.id != OWNER_ID:
        return await callback_query.answer("⛔️ Только админ может отвечать.", show_alert=True)

    message_id = callback_query.data.split('_')[1]
    await state.update_data(answer_to_id=message_id)
    await bot.send_message(OWNER_ID, f"Введите ответ для обращения №{message_id}:")
    await ReplyState.waiting_for_admin.set()
    await callback_query.answer()

# ================= Админ отправляет ответ =================

@dp.message_handler(state=ReplyState.waiting_for_admin, content_types=types.ContentType.ANY)
async def process_admin_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("answer_to_id")
    mapping = load_mapping()
    user_id = mapping.get(str(message_id))

    if not user_id:
        await message.reply("⚠️ Пользователь не найден.")
        return await state.finish()

    try:
        user_id = int(user_id)

        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Ответить администратору", callback_data=f"continue_{message_id}")
        )

        await bot.send_message(user_id, "📩 Администратор ответил на ваше сообщение!")

        if message.text:
            await bot.send_message(user_id, message.text, reply_markup=keyboard)
        elif message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "", reply_markup=keyboard)
        elif message.document:
            await bot.send_document(user_id, message.document.file_id, caption=message.caption or "", reply_markup=keyboard)
        elif message.video:
            await bot.send_video(user_id, message.video.file_id, caption=message.caption or "", reply_markup=keyboard)
        else:
            await bot.send_message(user_id, "Получен ответ в неизвестном формате.", reply_markup=keyboard)

        await message.reply("✅ Ответ отправлен пользователю.")
    except Exception as e:
        await message.reply(f"❌ Ошибка отправки: {e}")
    finally:
        await state.finish()

# ================= Пользователь продолжает диалог =================

@dp.callback_query_handler(lambda c: c.data.startswith("continue_"))
async def process_continue_user(callback_query: types.CallbackQuery, state: FSMContext):
    message_id = callback_query.data.split('_')[1]
    await state.update_data(dialog_id=message_id)
    await bot.send_message(callback_query.from_user.id, "✍️ Напиши ответ администратору.")
    await UserReplyState.waiting_for_user.set()
    await callback_query.answer()

@dp.message_handler(state=UserReplyState.waiting_for_user, content_types=types.ContentType.ANY)
async def process_user_dialog_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    dialog_id = data.get("dialog_id")
    mapping = load_mapping()
    user_id = message.from_user.id

    if str(mapping.get(str(dialog_id))) != str(user_id):
        await message.reply("⚠️ Ошибка идентификации.")
        return await state.finish()

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Ответить пользователю", callback_data=f"reply_{dialog_id}")
    )

    header = f"📨 Продолжение диалога №{dialog_id}:"

    if message.text:
        await bot.send_message(OWNER_ID, header + "\n\n" + message.text, reply_markup=keyboard)
    elif message.photo:
        await bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=header + (("\n" + message.caption) if message.caption else ""), reply_markup=keyboard)
    elif message.document:
        await bot.send_document(OWNER_ID, message.document.file_id, caption=header, reply_markup=keyboard)
    elif message.video:
        await bot.send_video(OWNER_ID, message.video.file_id, caption=header, reply_markup=keyboard)
    else:
        await bot.send_message(OWNER_ID, header + " (неизвестный формат)", reply_markup=keyboard)

    await message.reply("✅ Ответ отправлен администратору.")
    await state.finish()

# ================= Запуск =================

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
