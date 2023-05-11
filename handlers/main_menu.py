from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery


from database import database
from keyboards import client_kb
from loader import bot, dp


class FSMClient(StatesGroup):
    user_status = State()
    suggestions = State()


async def start_client_fsm(message: Message, state: FSMContext):
    await FSMClient.user_status.set()
    async with state.proxy() as data:
        data['user_tag'] = message.from_user.username

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await bot.send_message(
        text="Привет! Я чат-бот Артель",
        chat_id=message.from_user.id,
        reply_markup=client_kb.ReplyKeyboardRemove()
    )
    await message.answer(
        text="Чем могу помочь?",
        reply_markup=client_kb.user_inkb
    )


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await bot.send_message(
        text="Привет! Я чат-бот Артель",
        chat_id=message.from_user.id,
        reply_markup=client_kb.ReplyKeyboardRemove()
    )
    await message.answer("Чем могу помочь?",
                         reply_markup=client_kb.user_inkb)


@dp.message_handler(text='Другое', state=None)
async def become_other(message: Message, state: FSMContext):
    await start_client_fsm(message, state)
    # await FSMClient.suggestions.set()
    await message.answer(text='Оставьте заявку, и мы свяжемся по Вашему вопросу',
                                     reply_markup=client_kb.cancel_inkb)