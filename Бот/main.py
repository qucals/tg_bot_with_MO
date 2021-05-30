import telebot
import sqlite3
import logging as log
import math

from telebot import types
from telebot.apihelper import send_message
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton

from database import Database
from config import *

bot = telebot.TeleBot(TOKEN, parse_mode='Markdown')
db = Database(DB_PATH)

interests = db.get_all_interests()
interests_dict = {name.lower(): id for id, name in interests}

admins_command = ['Посмотреть список фактов', 'Посмотреть список тегов',
                  'Добавить факт', 'Добавить тег', 'Удалить факт', 'Удалить тег']

# Bot's functions


@bot.message_handler(commands=['start'])
def start_bot(message):
    log.info(f'Start chatting with ({message.from_user.username})')

    if not db.is_user_in_db(message.from_user.username):
        keyboard = get_main_keyboard()
        bot.send_message(message.chat.id, f'*Здравствуйте, {message.from_user.username}!* 🙃  \n\nЯ смотрю, вы здесь первый раз.\n Давайте я Вам все расскажу! \n\nЯ - бот, который помогает найти интересную информацию для Вас на основе ваших предпочтений и интересов. \n\nДля начала мне нужно узнать ваши интересы. Нажимайте кнопочки под чатом, чтобы выбрать интересующую Вас категорию. \nПосле выбора всех интересующих Вас категорий нажмите кнопку "Закончить выбор", чтобы я начал вам выдавать интересную информацию. \n\nТакже перечисляю ниже свои команды: \n1. /info - Выдать интересную информацию \n2. /add - Добавить интересы\n3. /help - Помощь\n4. /reset - Перевыбрать интересы\n', reply_markup=keyboard)

        db.add_user(message.from_user.username)
    else:
        send_main_message(message.chat.id)


@bot.message_handler(commands=['help'])
def get_help_bot(message):
    log.info(f'Send help to ({message.from_user.username})')

    bot.send_message(message.chat.id, 'Я - бот, который помогает найти интересную информацию для вас на основе ваших предпочтений и интересов.\nЯ обладаю следующими командами:\n1. /start - Начать диалог\n2. /help - Помощь по боту\n3. /info - Выдать интересную информацию\n4. /reset - Перевыбрать интересы\n')


@bot.message_handler(commands=['reset'])
def reset_interests_bot(message):
    log.info(f'Reset interests of ({message.from_user.username})')

    db.remove_all_interests(message.from_user.username)
    db.remove_user_rating(message.from_user.username)

    bot.send_message(
        message.chat.id, 'Ваши категории интересов успешно сброшены!')


@bot.message_handler(commands=['add'])
def add_interests_bot(message):
    interests = db.get_no_user_interests(message.from_user.username)
    if len(interests) > 0:
        keyboard = get_keybord_with_interests(interests)
        bot.send_message(
            message.chat.id, 'Выберите соответствущие категории, которые Вам подходят, нажимая на кнопки.', reply_markup=keyboard)
    else:
        send_all_interest_added(message.chat.id)


@bot.message_handler(commands=['admin'])
def show_admin_panel(message):
    if db.is_admin(message.from_user.username):
        keyboard = get_admin_keyboard()
        bot.send_message(
            message.chat.id, 'Для администрирования выберите одну из функций с помощью кнопок.', reply_markup=keyboard)
    else:
        send_unvailable_admin(message)


@bot.message_handler(commands=['info'])
def get_info_bot(message):
    log.info(f'Send some info to ({message.from_user.username})')

    info = get_list_info(message.from_user.username)
    doc_id = info[0][0]

    doc = db.get_doc(doc_id)

    markup = InlineKeyboardMarkup()
    markup.row_width = 5

    btn = []
    for i in range(1, 6, 1):
        btn.append(InlineKeyboardButton(
            f'{i}', callback_data=f'{doc_id};{i}'))
    markup.add(*btn)

    bot.send_message(
        message.chat.id, f'{doc[0]}\n\n{doc[1]}', reply_markup=markup)
    bot.send_message(
        message.chat.id, 'Пожалуйста, оцените предоставленную информацию. \nЭто поможет мне лучше подбирать для Вас интересную информацию!')


@bot.callback_query_handler(func=lambda call: True)
def handle_query_bot(call):
    text = call.data
    doc_id, rating = str(text).split(';')

    log.info(
        f'({call.from_user.username} set rating ({rating}) to doc({doc_id}))')

    db.set_rating_info(call.from_user.username, doc_id, rating)
    bot.send_message(
        call.from_user.id, 'Спасибо за поставленный рейтинг! \nБлагодаря этому Вы сделали меня лучше! 😉')


@bot.message_handler(content_types=['text'])
def process_buttons_bot(message):
    log.info(
        f'Got a message from ({message.from_user.username}) : ({message.text})')

    username = message.from_user.username
    chat_id = message.chat.id
    text = message.text.lower()

    if text in ['/start', 'привет', 'кто ты?', 'кто ты', 'старт']:
        start_bot(message)
    elif text in ['/add', 'выбрать категории интересов', 'выбрать интересы ⚙️', 'интересы']:
        add_interests_bot(message)
    elif text in ['/help', 'помощь 💊', 'помоги мне', 'помоги', 'как с тобой работать', 'что мне делать']:
        get_help_bot(message)
    elif text in ['/info', 'узнать интересную информацию 👀', 'интересная информация', 'интересные факты', 'информация', 'факты', 'получить факты']:
        get_info_bot(message)
    elif text in ['/reset', 'сбросить интересы']:
        reset_interests_bot(message)
    elif text in [command.lower() for command in admins_command]:
        if db.is_admin(username):
            if text == 'посмотреть список фактов':
                pass
            elif text == 'посмотреть список тегов':
                pass
            elif text == 'добавить факт':
                pass
            elif text == 'добавить тег':
                pass
            elif text == 'удалить факт':
                pass
            elif text == 'удалить тег':
                pass
        else:
            send_unvailable_admin(message)
    elif text == 'назад':
        send_main_message(message.chat.id)
    elif interests_dict.get(text) != None:
        is_added = db.add_user_interest(username, interests_dict.get(text))
        if is_added:
            send_added_interest_message(username, chat_id, message.text)
        else:
            send_no_added_interest_message(chat_id)
    else:
        send_error(message)

# Additional functions for bot


def send_main_message(chat_id):
    keyboard = get_main_keyboard()
    bot.send_message(
        chat_id, 'Для того, чтобы начать работать, выберите одну из функций с помощью кнопок.', reply_markup=keyboard)


def send_no_added_interest_message(chat_id):
    bot.send_message(chat_id, f'Вы уже добавили данную категорию интересов!')


def send_added_interest_message(username, chat_id, added_interest_name):
    keyboard = get_keybord_with_interests(db.get_no_user_interests(username))
    bot.send_message(
        chat_id, f'Вы успешно выбрали новую категорию интересов – {added_interest_name}!\nВы можете продолжить выбор категорий, либо перейти в главное меню нажатием кнопки "Назад".', reply_markup=keyboard)


def send_all_interest_added(chat_id):
    bot.send_message(
        chat_id, 'Вы выбрали все доступные категории интересов!\nСбросьте свой список интересов (/reset), чтобы выбрать их заново.')


def send_error(message):
    bot.send_message(message.chat.id,
                     'Я не знаю такую команду! 🙁\nВоспользуйтесь командой /help для того, чтобы узнать мои команды.\n')


def send_unvailable_admin(message):
    bot.send_message(message.chat.id, 'Вам не доступна данная команда!')


def get_main_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    main_list = ['Выбрать интересы ⚙️', 'Сбросить интересы',
                 'Помощь 💊', 'Узнать интересную информацию 👀']
    btns = [KeyboardButton(name) for name in main_list]
    keyboard.add(*btns)
    return keyboard


def get_keybord_with_interests(interests):
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    btns = [KeyboardButton(item[1]) for item in interests]
    btns.append(get_back_button())
    keyboard.add(*btns)
    return keyboard


def get_admin_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    _btns = [KeyboardButton(command) for command in admins_command]
    keyboard.add(*_btns)
    return keyboard


def get_back_button():
    return KeyboardButton('Назад')


def get_list_info(username):
    unappreciated = db.get_unappreciated_docs(username)
    appreciated = db.get_appreciated_docs(username)
    matrix = db.get_rating_matrix()

    result = []

    if len(appreciated) > 0:
        for appreciated_id in appreciated:
            for unappreciated_id in unappreciated:
                _sum = 0
                sqrt_1 = 0
                sqrt_2 = 0

                for marks in matrix.values():
                    if marks[appreciated_id] != 0 and marks[unappreciated_id] != 0:
                        _sum += marks[appreciated_id] + \
                            marks[unappreciated_id]
                    sqrt_1 += marks[appreciated_id]**2
                    sqrt_2 += marks[unappreciated_id]**2

                similarity = 0 if sqrt_1 * \
                    sqrt_2 == 0 else _sum / (sqrt_1 * sqrt_2)

                similarity_interests = db.get_similarity_interest(
                    username, unappreciated_id)

                if similarity_interests != 0:
                    similarity += math.log10(similarity_interests)**2

                result.append((unappreciated_id, similarity))
    else:
        for unappreciated_id in unappreciated:
            similarity = 0

            similarity_interests = db.get_similarity_interest(
                username, unappreciated_id)

            if similarity_interests != 0:
                similarity += math.log(similarity_interests)**2

            result.append((unappreciated_id, similarity))

    result.sort(key=lambda x: x[1], reverse=True)
    return result


bot.polling()
