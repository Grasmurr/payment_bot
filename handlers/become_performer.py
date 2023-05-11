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
    performer_experience = State()
    performer_subject = State()
    suggestions = State()


async def start_client_fsm(callback: CallbackQuery, state: FSMContext):
    await FSMClient.user_status.set()
    async with state.proxy() as data:
        data['user_tag'] = callback.from_user.username


@dp.message_handler(text='Хочу стать вашим исполнителем')
async def become_performer(message: Message, state: FSMContext):
    await message.answer(text='Выберите предмет', reply_markup=client_kb.subjects_inkb)
    await FSMClient.performer_subject.set()


@dp.callback_query_handler(state=FSMClient.performer_subject)
async def choose_performer_subject(callback: types.CallbackQuery, state: FSMContext):
    await start_client_fsm(callback, state)
    await FSMClient.performer_subject.set()
    async with state.proxy() as data:
        data['performer_id'] = callback.from_user.id
        data['subject'] = callback.data
    await FSMClient.performer_experience.set()
    await callback.message.edit_text("Опишите свой опыт и навыки", reply_markup=client_kb.cancel_inkb)


@dp.message_handler(state=FSMClient.performer_experience)
async def get_performer_details(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['performer_details'] = message.text
    await database.database.sql_add_command(state=state, table_name='performers')
    await state.finish()
    await message.answer(text="Ожидайте ответа, мы с Вами скоро свяжемся!",
                         reply_markup=client_kb.main_menu)
