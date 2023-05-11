import json
import sqlite3

from loader import bot, ABRAM_ID, DASHA_ID, KIRILL_ID


class Database:
    def __init__(self, filename):
        self.base = sqlite3.connect(filename)
        self.cursor = self.base.cursor()
        if self.base:
            print('Database connected!')

    def create_database(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS "
                            "orders (user_tag VARCHAR(64) NOT NULL,"
                            "subject VARCHAR(128) NOT NULL,"
                            "order_details TEXT,"
                            "order_id VARCHAR(64),"
                            "work_type TEXT,"
                            "message_id VARCHAR(64))")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS "
                            "performers (user_tag VARCHAR(64) NOT NULL, "
                            "performer_id VARCHAR(64), "
                            "subject VARCHAR(128) NOT NULL, "
                            "performer_details TEXT,"
                            "is_busy INTEGER DEFAULT 0)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS "
                            "others (user_tag VARCHAR(64) NOT NULL, "
                            "suggestions TEXT)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS "
                            "perf_description "
                            "(performer_id VARCHAR(64) NOT NULL, "
                            "description TEXT NOT NULL)")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS "
                            "chats (chat_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                            "chat_one VARHCAR(64) NOT NULL, "
                            "chat_two VARHCAR(64) NOT NULL)")

        # Новая таблица с информацией о заказах
        self.cursor.execute("CREATE TABLE IF NOT EXISTS "
                            "order_info (order_id VARCHAR(64) PRIMARY KEY, "
                            "customer_id VARCHAR(64) NOT NULL, "
                            "performer_id VARCHAR(64) NOT NULL, "
                            "price INTEGER NOT NULL, "
                            "days INTEGER NOT NULL)")

        self.base.commit()

    async def sql_add_command(self, table_name, state):
        async with state.proxy() as data:
            self.cursor.execute("INSERT INTO %s %s VALUES %s" %
                                (table_name, tuple(data.keys()), tuple(data.values())))

            await notify(data=data)
            self.base.commit()

    def get_order_info(self, order_id):
        return self.cursor.execute("SELECT subject, message_id, order_details "
                                   "FROM orders "
                                   "WHERE order_id = ?", (order_id,)).fetchmany(1)[0]

    def is_performer_busy(self, performer_id):
        return self.cursor.execute("SELECT is_busy "
                                   "FROM performers "
                                   "WHERE performer_id = ?", (performer_id,)).fetchmany(1)

    def get_performer_description(self, performer_id):
        return self.cursor.execute("SELECT description "
                                   "FROM perf_description "
                                   "WHERE performer_id = ?", (performer_id,)).fetchmany(1)[0][0]

    def keep_performer(self, performer_id):
        self.cursor.execute("UPDATE performers "
                            "SET is_busy = 1 "
                            "WHERE performer_id = ?", (performer_id,))

    def free_performer(self, id_1, id_2):
        self.cursor.execute("UPDATE performers "
                            "SET is_busy = 0 "
                            "WHERE performer_id = ? OR performer_id = ?", (id_1, id_2,))

    def get_active_chat(self, user_id):
        chat_id = self.cursor.execute("SELECT chat_two "
                                      "FROM chats "
                                      "WHERE chat_one = ?", (user_id,)).fetchmany(1)
        if not chat_id:
            chat_id = self.cursor.execute("SELECT chat_one "
                                          "FROM chats "
                                          "WHERE chat_two = ?", (user_id,)).fetchmany(1)
        return chat_id[0][0] if chat_id else 0

    def create_chat(self, order_id, performer_id):
        self.cursor.execute("DELETE FROM orders "
                            "WHERE order_id = ?", (order_id,))

        self.cursor.execute("INSERT INTO chats (chat_one, chat_two)"
                            "VALUES (?, ?)", (order_id, performer_id,))

    def delete_from_chats(self, chat_id):
        self.cursor.execute("DELETE FROM chats "
                            "WHERE chat_one = ? OR chat_two = ?", (chat_id, chat_id))


async def notify(data):
    message_text = "Пришел новый заказ:\n" + json.dumps(dict(data), indent=4, ensure_ascii=False)
    for admin_id in [ABRAM_ID, DASHA_ID, KIRILL_ID]:
        await bot.send_message(
            chat_id=admin_id,
            text=message_text
        )


database = Database("artel.db")
database.create_database()
