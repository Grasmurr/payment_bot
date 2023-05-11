import base64
import re
import requests
import json
import hashlib

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery


from database import database
from keyboards import client_kb
from loader import bot, dp


phone_pat = re.compile(r"(\d\s*){11}")
link_pat = re.compile(r"(https://(www.)?)?(instagram|vk|t).(com|me).*")
tag_pat = re.compile(r"@.+")
words_pat = re.compile(r"\b(тг|tg|вк|vk|vkontakte|инстаграмм|инст(а|ы|ой|у|е)?|inst)\b")


def is_allowed_message(text):
    phone_match = re.match(string=text, pattern=phone_pat)
    link_match = re.match(string=text, pattern=link_pat)
    tag_match = re.match(string=text, pattern=tag_pat)
    words_match = re.match(string=text, pattern=words_pat)
    return not (phone_match or link_match or tag_match or words_match)


async def send_message(message: types.Message):
    if message.chat.type == "private":
        chat_id = database.database.get_active_chat(message.from_user.id)
        if chat_id:
            if message.content_type == 'text' and is_allowed_message(message.text):
                await bot.send_message(text=message.text, chat_id=chat_id)
            if message.content_type == 'document':
                await bot.send_document(document=message.document.file_id, chat_id=chat_id)


async def cancel_handler(message: types.Message, state=FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.reply("Нечего отменять")
        return
    await state.finish()
    await message.reply("Заказ отменен.\nЕсли хотите начать сначала, введите /start")


def register_callbacks_and_handlers_client(dp: Dispatcher):
    dp.register_message_handler(cancel_handler, state="*", commands='отмена')
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state="*")
    dp.register_message_handler(send_message, content_types=['text', 'document'])
    dp.register_pre_checkout_query_handler(lambda query: True)
