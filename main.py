import sqlite3
import telebot
import sqlite3

from icecream import ic
from database import Database

token = '1720790674:AAFVmWMGe3p3a3O5xX63AAsrAie0WqYl_1Y'
db_path = 'data.db'

db = Database(db_path)
bot = telebot.TeleBot(token, parse_mode=None)

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(f'SELECT COUNT(*) FROM users WHERE login=?', (message.from_user.username,))
        data = cur.fetchall()

        ans = 'Найден' if data[0][0] != 0 else 'Не найден!'
        bot.send_message(message.from_user.id, ans)

bot.polling()
db.close()