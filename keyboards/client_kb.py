from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton,\
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from loader import bot

# start menu keyboard
help_button = KeyboardButton('/help')
main_menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
main_menu.add(help_button)


# inline keyboard markup
user_inkb = ReplyKeyboardMarkup(resize_keyboard=True)

become_client = KeyboardButton(text="Хочу купить работу")
become_performer = KeyboardButton(text="Хочу стать вашим исполнителем")
become_other = KeyboardButton(text="Другое")
cancel_button = InlineKeyboardButton(text="Отмена",
                                     callback_data='cancel')

cancel_inkb = InlineKeyboardMarkup().add(cancel_button)
user_inkb.add(become_client)
user_inkb.add(become_performer)
user_inkb.add(become_other)

subjects_dict = {
    "test": -1001674582859,
    "Юриспруденция": -1001790959600,
    "Экономика": -1001852643314,
    "Политология": -1001679302522,
    "Социология": -1001608456987,
    "История": -1001804798141,
    "Философия": -1001806183269,
    "Психология": -1001631922451,
    "Программирование": -1001590590211,
    "Лингвистика и иностранные языки": -1001862273326,
    "Математика": -1001763954483,
    "Филология и литература": -1001823585368,
    "Искусство": -1001711068367,
    "Государственное управление": -1001881088844,
    "Международные отношения": -1001874994032,
    "Архитектура и урбанистика": -1001854906965,
    "Маркетинг и бизнес": -1001808316216,
    "Реклама и журналистика": -1001664717218,
    "Финансы, аудит и бухучет": -1001804298079,
    "Биология и медицина": -1001866691571,
    "Физика": -1001895191555,
    "Транскрипты": -1001810132774
}

subjects_inkb = InlineKeyboardMarkup(row_width=2)
for subject in subjects_dict:
    subjects_inkb.insert(InlineKeyboardButton(text=subject, callback_data=subject))
subjects_inkb.add(cancel_button)

price_button = InlineKeyboardButton(text="Предложить цену", callback_data="ask price")
price_inkb = InlineKeyboardMarkup(row_width=1)
price_inkb.add(price_button)

reply_button = InlineKeyboardButton(text="Откликнуться", callback_data="reply")
reply_inkb = InlineKeyboardMarkup()
reply_inkb.add(reply_button)


close_chat_button = KeyboardButton('/Закрыть_чат')
close_chat_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
close_chat_kb.add(close_chat_button)


async def send_performer_suggestion(client_id, text):
    accept_button = InlineKeyboardButton(text=f"Принять", callback_data="accept price")
    deny_button = InlineKeyboardButton(text=f"Отклонить", callback_data="deny price")
    suggestion_inkb = InlineKeyboardMarkup()
    suggestion_inkb.add(accept_button, deny_button)
    # № знак номера
    await bot.send_message(text=text, reply_markup=suggestion_inkb, chat_id=client_id)


def work_type_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)

    buttons = [
        "Презентация", "Транскрипт или кодировка", "Доклад",
        "Аналитическая записка", "Эссе", "Решение задач",
        "Реферат", "Рецензия", ">>"

    ]

    for button_text in buttons:
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"work_type:{button_text}"))

    return keyboard


def work_type_keyboard_2():
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        "Тест", "Контрольная работа",
        "Кейс", "Курсовая работа", "Другое", "Бакалаврский диплом",
        "Магистерская диссертация", "Другая ВКР", "<<"
    ]

    for button_text in buttons:
        keyboard.add(InlineKeyboardButton(text=button_text, callback_data=f"work_type:{button_text}"))
    return keyboard

