import hashlib
import requests
import json

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, CallbackQuery


from database import database
from keyboards import client_kb
from loader import bot, dp


class FSMClient(StatesGroup):
    client_subject = State()
    user_status = State()
    client_details = State()
    suggestions = State()
    order_work = State()
    work_type = State()


class FSMOrder(StatesGroup):
    get_price = State()


async def start_client_fsm(callback: CallbackQuery, state: FSMContext):
    await FSMClient.user_status.set()
    async with state.proxy() as data:
        data['user_tag'] = callback.from_user.username


@dp.message_handler(commands=['Закрыть_чат'])
async def close_chat(message: types.Message):
    chat_id = database.database.get_active_chat(message.from_user.id)
    await message.answer(text="Чат закрыт", reply_markup=client_kb.main_menu)
    await bot.send_message(chat_id=chat_id, text="Чат закрыт", reply_markup=client_kb.main_menu)

    database.database.delete_from_chats(chat_id=chat_id)
    database.database.free_performer(id_1=chat_id, id_2=message.from_user.id)


@dp.message_handler(text='Хочу купить работу')
async def become_client(message: Message, state: FSMContext):
    await message.answer(text='Выберите предмет', reply_markup=client_kb.subjects_inkb)
    await FSMClient.order_work.set()


@dp.callback_query_handler(state="*", text='cancel')
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await callback.message.reply("Нечего отменять")
        await callback.answer()
        return
    await state.finish()
    await callback.message.edit_text(text="Запрос отменен.",
                                     reply_markup=None)
    await callback.message.answer(text='Хотите начать сначала ?',
                                  reply_markup=client_kb.main_menu)
    await callback.answer()


@dp.callback_query_handler(state=FSMClient.order_work)
async def choose_client_subject(callback: types.CallbackQuery, state: FSMContext):
    await start_client_fsm(callback, state)
    async with state.proxy() as data:
        data['subject'] = callback.data
        if data['subject'] != 'Другое (укажите Ваш предмет)':
            # Отправка сообщения с выбором типа работы
            await callback.message.edit_text(text="Выберите тип работы")
            await callback.message.edit_reply_markup(reply_markup=client_kb.work_type_keyboard())
        else:
            await callback.message.edit_text(text="Введите название предмета")
            await callback.message.edit_reply_markup(reply_markup=client_kb.cancel_inkb)
        await FSMClient.work_type.set()


@dp.callback_query_handler(state=FSMClient.work_type)
async def choose_work_type(callback: types.CallbackQuery, state: FSMContext):
    work_type = callback.data.split(":")[1]
    if work_type in ['<<', '>>']:
        async with state.proxy() as data:
            if data['subject'] != 'Другое (укажите Ваш предмет)':
                # Отправка сообщения с выбором типа работы
                await callback.message.edit_text(text="Выберите тип работы")
                if work_type == '>>':
                    await callback.message.edit_reply_markup(reply_markup=client_kb.work_type_keyboard_2())
                elif work_type == '<<':
                    await callback.message.edit_reply_markup(reply_markup=client_kb.work_type_keyboard())
            else:
                await callback.message.edit_text(text="Введите название предмета")
                await callback.message.edit_reply_markup(reply_markup=client_kb.cancel_inkb)
    else:
        async with state.proxy() as data:
            data['work_type'] = work_type
            await FSMClient.client_details.set()
            await callback.message.edit_text(text='Конкретизируйте Ваш заказ (сроки, детали, иные пожелания)')
            await callback.message.edit_reply_markup(reply_markup=client_kb.cancel_inkb)
            await FSMClient.client_details.set()


@dp.message_handler(state=FSMClient.client_details)
async def get_order_details(message: Message, state: FSMContext):
    async with state.proxy() as data:
        order_id = message.from_user.id
        subject_id = client_kb.subjects_dict[data['subject']]
        data['order_details'] = message.text
        data['order_id'] = order_id
        message_id = (await bot.send_message(chat_id=message.from_user.id,
                                             text=data['order_details'] + f"\n{order_id}",
                                             reply_markup=client_kb.reply_inkb)).message_id
        data['message_id'] = message_id

    await database.database.sql_add_command(state=state, table_name='orders')

    await message.answer(text="Спасибо, мы свяжемся с Вами в ближайшее время!", reply_markup=client_kb.main_menu)
    await state.finish()


# offer price
@dp.callback_query_handler(text='reply')
async def reply_to_order(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    info = database.database.is_performer_busy(performer_id=user_id)

    # if not info:
    #     await callback.bot.send_message(text="Вы не являетесь исполнителем",
    #                                     chat_id=user_id)
    #     await callback.answer()
    #     return
    #
    # is_busy = info[0][0]
    # if is_busy:
    #     await callback.bot.send_message(text="У Вас есть текущий заказ",
    #                                     chat_id=user_id)
    #     return
    await callback.bot.send_message(text=callback.message.text,
                                    reply_markup=client_kb.price_inkb,
                                    chat_id=user_id)


@dp.callback_query_handler(text="ask price", state=None)
async def ask_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup()
    await FSMOrder.get_price.set()
    async with state.proxy() as data:
        message_text = callback.message.text.split("\n")
        order_id = int(message_text[-1])
        data['order_id'] = order_id
        data['performer_id'] = callback.from_user.id
        await callback.bot.send_message(text=f"Введите свою цену: {order_id}", chat_id=callback.from_user.id)


@dp.message_handler(state=FSMOrder.get_price)
async def get_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        price = message.text
        if not price.isnumeric():
            await message.answer("Неправильный формат цены, введите еще раз")
            return
        price = int(price)
        price_res = price * 1.25
        data['price'] = price_res
        await message.answer(text=f"Ваша цена записана: {price}")
        print(data)
        # description = database.database.get_performer_description(performer_id=data['performer_id'])

        text = f"{data['performer_id']}: \nЦена: {price_res:.0f}"
        await client_kb.send_performer_suggestion(client_id=data['order_id'],
                                                  text=text)


def init_tinkoff_payment_session(terminal_key, amount, order_id, ip, description, customer_key=None, currency=None, recurrent=None, pay_type=None, language=None):
    base_url = "https://rest-api-test.tinkoff.ru/v2/Init/"

    payload = {
        "TerminalKey": terminal_key,
        "Amount": amount,
        "OrderId": order_id,
        "IP": ip,
        "Description": description
    }

    if customer_key:
        payload["CustomerKey"] = customer_key
    if currency:
        payload["Currency"] = currency
    if recurrent:
        payload["Recurrent"] = recurrent
    if pay_type:
        payload["PayType"] = pay_type
    if language:
        payload["Language"] = language

    # Формирование подписи
    # sorted_payload = sorted(payload.items(), key=lambda x: x[0])
    # sorted_payload_str = "".join(f"{key}={value}" for key, value in sorted_payload)
    # token = hashlib.sha256((sorted_payload_str).encode("utf-8")).hexdigest()
    # payload["Token"] = token

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(base_url, data=json.dumps(payload), headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} {response.text}")
        return {}


@dp.callback_query_handler(text='accept price', state=FSMOrder.get_price)
async def accept_price(callback: types.CallbackQuery, state: FSMContext):
    performer_id = int(callback.message.text.split(":")[0]) // 2
    order_id = callback.from_user.id
    subject, message_id, details = database.database.get_order_info(order_id=order_id)


    # subject_id = client_kb.subjects_dict[subject]
    # message_id = int(message_id)
    # await bot.edit_message_text(chat_id=subject_id,
    #                             message_id=message_id,
    #                             text=f"{details} (в процессе)",)

    # database.database.keep_performer(performer_id=performer_id)
    # database.database.create_chat(order_id=order_id, performer_id=performer_id)

    # await bot.send_message(chat_id=subject_id,
    #                        text=f"Вы получили заказ:\n{details}.\nЧат с заказчиком открыт",
    #                        reply_markup=client_kb.close_chat_kb)
    markup = types.InlineKeyboardMarkup()
    async with state.proxy() as data:
        terminal_key = '1681241846285DEMO'
        password = 'sacxht4n33v1p19j'
        print(data)
        amount = data['price'] * 100  # сумма в копейках
        order_id = '2'
        customer_key = 'callback.from_user.id'

        # Заполнение необходимых данных для запроса Init
        payload = {
            'TerminalKey': terminal_key,
            'Amount': amount,
            'OrderId': order_id,
            'CustomerKey': customer_key,
            'Password': password,
        }

        # Вычисление и добавление подписи к запросу
        data_to_hash = ''.join([str(payload[key]) for key in sorted(payload.keys())])
        payload['Token'] = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()

        response = requests.post('https://securepay.tinkoff.ru/v2/Init', json=payload)

        # Обработка ответа от Tinkoff API
        if response.status_code == 200:
            response_json = response.json()
            if response_json['Success']:
                payment_url = response_json['PaymentURL']
                payment_id = response_json['PaymentId']
                print(f"Ссылка на оплату: {payment_url}")
                print(f"ID платежа: {payment_id}")
                keyboard = types.InlineKeyboardMarkup()
                pay_button = types.InlineKeyboardButton(text='Оплатить', url=payment_url)
                keyboard.add(pay_button)

                await callback.message.reply("Пожалуйста, нажмите кнопку ниже, чтобы перейти к оплате:",
                                             reply_markup=keyboard)
            else:
                print(f"Ошибка при создании платежа: {response_json['Message']}")
        else:
            print(f"Ошибка при выполнении запроса: {response.status_code}")

    # await callback.message.edit_reply_markup()
    # await callback.message.answer(text="Пожалуйста, оплатите 50% от суммы по номеру (номер)\n"
    #                                    "Переносим Вас в чат с исполнителем",
    #                               reply_markup=client_kb.close_chat_kb)


@dp.callback_query_handler(text='deny price')
async def deny_price(callback: types.CallbackQuery):
    await callback.message.edit_text(text="Ожидайте следующих заявок от исполнителей",
                                     reply_markup=None)


@dp.message_handler(state=FSMClient.suggestions)
async def get_another_suggestions(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['suggestions'] = message.text
    await database.database.sql_add_command(state=state, table_name='others')
    await message.answer(text="Ожидайте ответа, мы с Вами скоро свяжемся!",
                         reply_markup=client_kb.main_menu)
    await state.finish()

