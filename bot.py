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
