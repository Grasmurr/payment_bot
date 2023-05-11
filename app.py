import logging
import schedule
import time

from threading import Thread

from aiogram import executor

from database import database
from handlers import client, admin
from loader import bot, dp, ADMIN_ID
import handlers


logging.basicConfig(level=logging.INFO)


async def on_startup(dp):
    await bot.send_message(chat_id=ADMIN_ID, text='Бот запущен!')
    database.database.create_database()


async def on_shutdown(dp):
    await bot.send_message(chat_id=ADMIN_ID, text='Бот выключен!')


admin.register_handlers_admin(dp)
client.register_callbacks_and_handlers_client(dp)


# проверяем, нужное ли сейчас время, чтобы отправить ежедневную рассылку
def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)


def function_to_run():
    pass



if __name__ == '__main__':
    schedule.every().day.at("12:00").do(function_to_run)
    Thread(target=schedule_checker).start()
    executor.start_polling(dp,
                           on_startup=on_startup,
                           on_shutdown=on_shutdown,
                           skip_updates=True)
