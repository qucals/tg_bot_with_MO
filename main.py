import telebot
import sqlite3
import sqlite3
import logging as log

from os import device_encoding
from sqlite3.dbapi2 import sqlite_version_info

from telebot import types
from telebot.apihelper import send_message
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton

from database import Database

# Constants

token = '1720790674:AAFVmWMGe3p3a3O5xX63AAsrAie0WqYl_1Y'
db_path = '/Users/totalboy/Desktop/Diploma/data.db'

# Main handles

log.basicConfig(filename='logfile.log',
                format='[%(levelname)s] : %(asctime)s > %(message)s', level=log.INFO)
bot = telebot.TeleBot(token, parse_mode='Markdown')
db = Database(db_path)

# Bot's functions


@bot.message_handler(commands=['start'])
def start_bot(message):
    log.info(f'Start chatting with user({message.from_user.username})')
    send_welcome(message.chat.id, message.from_user.username)

    if not db.is_user_in_db(message.from_user.username):
        db.add_user(message.from_user.username)


@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.from_user.id, 'Я - бот, который помогает найти интересную информацию для вас на основе ваших предпочтений и интересов.\nЯ обладаю следующими командами:\n1. /start - Начать диалог\n2. /help - Помощь по боту\n3. /info - Выдать интересную информацию\n4. /reset - Перевыбрать интересы\n')


@bot.message_handler(content_types=['text'])
def process_buttons(message):
    username = message.from_user.username
    chat_id = message.chat.id
    text = message.text.lower()

    if text in 'помощь':
        send_help(message)
    elif text == 'узнать интересную информацию':
        db.get_no_user_interests(username)
    elif text == 'добавить интересы':
        interests = db.get_no_user_interests(username)
        select_interests(build_keybord_with_interests(interests), chat_id)
    elif text == 'сбросить интересы':
        pass
    elif text == 'назад':
        send_main_message(chat_id)
    else:
        send_error(message)

# Additional functions for bot


def send_main_message(chat_id):
    keyboard = get_main_keyboard()
    bot.send_message(
        chat_id, 'Выберите одну из функций с помощью кнопок.', reply_markup=keyboard)


def send_welcome(chat_id, username):
    keyboard = get_main_keyboard()
    bot.send_message(chat_id, f'*Здравствуйте, {username}!*\n\nЯ смотрю, вы первый раз здесь.\nДавайте я вам все расскажу!\n\nЯ - бот, который помогает найти интересную информацию для вас на основе ваших предпочтений и интересов.\n\nДля начала мне нужно узнать ваши интересы. Нажимайте кнопочки под чатом, чтобы выбрать интересующую вас категорию.\nПосле выбора всех интересующих вас категорий нажмите кнопку "Закончить выбор", чтобы я начал вам выдавать интересную информацию.\n\nТакже перечисляю ниже свои команды:\n1. /start - Начать диалог\n2. /help - Помощь по боту\n3. /info - Выдать интересную информацию\n4. /reset - Перевыбрать интересы\n', reply_markup=keyboard)


def send_error(message):
    bot.send_message(message.chat.id,
                     'Я не знаю такую команду!\nВоспользуйтесь командой /help для того, чтобы узнать мои команды.\n')


def select_interests(keyboard, chat_id):
    bot.send_message(
        chat_id, 'Выберите соответствущие категории, которые вам подходят, нажимая на кнопки.', reply_markup=keyboard)


def get_main_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    main_list = ['Помощь', 'Узнать интересную информацию',
                 'Добавить интересы', 'Сбросить интересы']
    btns = [KeyboardButton(name) for name in main_list]
    keyboard.add(*btns)
    return keyboard


def build_keybord_with_interests(interests):
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    btns = [KeyboardButton(item[1]) for item in interests]
    btns.append(get_back_button())
    keyboard.add(*btns)
    return keyboard


def get_back_button():
    return KeyboardButton('Назад')


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.polling()
