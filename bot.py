import os
import json
from threading import Thread
from flask import Flask

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = 'ВАШ_ТОКЕН'
OWNER_ID = ВАШ_ID   # ЦЕЛОЕ ЧИСЛО

# ==== Flask для Ping (по желанию) ====
app = Flask('')

@app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

flask_thread = Thread(target=run_flask)
flask_thread.start()
# ==== END Flask ====

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

counter_file = "counter.txt"
mapping_file = "messages_map.json"

# {message_id: user_id }
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

# FSM для ответа админа
class ReplyState(StatesGroup):
    waiting_for_admin = State()
# FSM для ответа пользователя
class UserReplyState(StatesGroup):
    waiting_for_user = State()

# /start
@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.reply(
        "Привет! Напиши сюда анонимное сообщение, и оно дойдет администратору. Ответить можно будет только через специальные кнопки!"
    )

# Получение анонимного сообщения от пользователя
@dp.message_handler(content_types=types.ContentType.ANY, state="*")
async def anonymous_message(message: types.Message, state: FSMContext):
    if message.text and message.text.startswith('/start'):
        return

    # Для обычного обращения генерируем message_id и маппинг
    message_id = get_next_id()
    user_id = message.from_user.id

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

    # Кнопка "Ответить на сообщение"
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Ответить на сообщение", callback_data=f"reply_{message_id}")
    )

    await bot.send_message(OWNER_ID, notification)

    sent_message = None
    if message.text:
        sent_message = await bot.send_message(OWNER_ID, f"{content_header}\n\n{message.text}", reply_markup=keyboard)
    elif message.photo:
        file_id = message.photo[-1].file_id
        sent_message = await bot.send_photo(OWNER_ID, file_id, caption=content_header + (("\n" + message.caption) if message.caption else ""), reply_markup=keyboard)
    elif message.document:
sentmessage = await bot.senddocument(OWNERID, message.document.fileid, caption=contentheader + (("\n" + message.caption) if message.caption else ""), replymarkup=keyboard)
    elif message.video:
        sentmessage = await bot.sendvideo(OWNERID, message.video.fileid, caption=contentheader + (("\n" + message.caption) if message.caption else ""), replymarkup=keyboard)
    else:
        await bot.sendmessage(OWNERID, f"{contentheader} (неизвестный формат!)", replymarkup=keyboard)

    await message.reply("Ваше анонимное обращение отправлено!")

# Обработка кнопки "Ответить" от администратора
@dp.callbackqueryhandler(lambda c: c.data and c.data.startswith('reply'))
async def processcallbackreply(callbackquery: types.CallbackQuery, state: FSMContext):
    if int(callbackquery.fromuser.id) != int(OWNERID):
        return await callbackquery.answer("Только админ может отвечать!", showalert=True)
    messageid = callbackquery.data.split('')1
    await state.updatedata(answertoid=messageid)
    await bot.sendmessage(OWNERID, f"Введите ответ для обращения №{messageid}:")
    await ReplyState.waitingforadmin.set()
    await callbackquery.answer()

# Когда админ вводит ответ пользователю
@dp.messagehandler(state=ReplyState.waitingforadmin, contenttypes=types.ContentType.ANY)
async def processadminanswer(message: types.Message, state: FSMContext):
    data = await state.getdata()
    messageid = data.get('answertoid')
    mapping = loadmapping()
    userid = mapping.get(str(messageid))
    if not userid:
        await message.reply("Ошибка: пользователь не найден.")
        await state.finish()
        return
    try:
        # 1. Оповещение
        kbcont = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Продолжить диалог", callbackdata=f"continue{messageid}")
        )
        await bot.sendmessage(userid, "‼️ Получен ответ на вашу анонимку!")
        # 2. Ответ (разные типы)
        if message.text:
            await bot.sendmessage(userid, message.text, replymarkup=kbcont)
        elif message.photo:
            await bot.sendphoto(userid, message.photo-1.fileid, caption=(message.caption or ""), replymarkup=kbcont)
        elif message.document:
            await bot.senddocument(userid, message.document.fileid, caption=(message.caption or ""), replymarkup=kbcont)
        elif message.video:
            await bot.sendvideo(userid, message.video.fileid, caption=(message.caption or ""), replymarkup=kbcont)
        else:
            await bot.sendmessage(userid, "Получен ответ, но его формат неизвестен.", replymarkup=kbcont)
        await message.reply("Ответ отправлен пользователю!")
    except Exception as e:
        await message.reply("Ошибка отправки пользователю (возможно, он заблокировал бота).")
    await state.finish()

# Пользователь нажал "Продолжить диалог"
@dp.callbackqueryhandler(lambda c: c.data and c.data.startswith('continue'))
async def processcontinueuser(callbackquery: types.CallbackQuery, state: FSMContext):
    messageid = callbackquery.data.split('')1
    await state.updatedata(dialogid=messageid)
    await bot.sendmessage(callbackquery.fromuser.id, "Напиши следующий анонимный ответ админу.")
    await UserReplyState.waitingforuser.set()
    await callbackquery.answer()

# Пользователь отправляет свой ответ админу
@dp.messagehandler(state=UserReplyState.waitingforuser, contenttypes=types.ContentType.ANY)
async def processuserdialogreply(message: types.Message, state: FSMContext):
    data = await state.getdata()
    dialogid = data.get("dialogid")
    mapping = loadmapping()
    userid = message.fromuser.id
    # Проверить маппинг (userid должен совпадать)
    if mapping.get(str(dialogid)) != userid:
        await message.reply("Ошибка идентификации диалога.")
        await state.finish()
        return

    header = f'✉️ Продолжение анонимного диалога (№{dialogid}):'
    kb = InlineKeyboardMarkup().add(


InlineKeyboardButton("Ответить пользователю", callback_data=f"reply_{dialog_id}")
    )

    if message.text:
        await bot.send_message(OWNER_ID, header + "\n\n" + message.text, reply_markup=kb)
    elif message.photo:
        await bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=header + (("\n" + message.caption) if message.caption else ""), reply_markup=kb)
    elif message.document:
        await bot.send_document(OWNER_ID, message.document.file_id, caption=header + (("\n" + message.caption) if message.caption else ""), reply_markup=kb)
    elif message.video:
        await bot.send_video(OWNER_ID, message.video.file_id, caption=header + (("\n" + message.caption) if message.caption else ""), reply_markup=kb)
    else:
        await bot.send_message(OWNER_ID, header + " (Неизвестный формат сообщения).", reply_markup=kb)

    await message.reply("Ваш ответ отправлен админу! Ждите его новое сообщение.")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
