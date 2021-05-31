# < Зависимости >

import telebot
import logging as log
import math
import random

from telebot import types
from telebot.apihelper import send_message, unpin_all_chat_messages
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton

from database import Database
from config import *

# < Константы >

bot = telebot.TeleBot(TOKEN, parse_mode='Markdown')
db = Database(DB_PATH)

interests = db.get_all_interests()
interests_dict = {name.lower(): id for id, name in interests}

start_commands = ['/start', 'привет', 'кто ты?', 'кто ты', 'старт']

select_interests_commands = [
    '/add', 'выбрать категории интересов', 'выбрать интересы ⚙️', 'интересы']

help_commands = ['/help', 'помощь 💊', 'помоги мне',
                 'помоги', 'как с тобой работать', 'что мне делать']

get_info_commands = ['/info', 'узнать интересную информацию 👀',
                     'интересная информация', 'интересные факты', 'информация', 'факты', 'получить факты']

reset_commands = ['/reset', 'сбросить интересы']

admins_commands = ['Посмотреть список фактов', 'Посмотреть категории интересов', 'Показать описание факта',
                   'Добавить факт', 'Добавить тег', 'Удалить факт', 'Удалить тег', 'Добавить категории интересов у факта', 'Сбросить категории интересов у факта', 'Назад']

# < Callback - Функции бота >


@bot.message_handler(commands=['start'])
def start_bot(message):
    log.info(f'Start chatting with ({message.from_user.username})')

    if not db.is_user_in_db(message.from_user.username):
        keyboard = get_main_keyboard()
        bot.send_message(message.chat.id, f'*Здравствуйте, {message.from_user.username}!* 🙃  \n\nЯ смотрю, вы здесь первый раз.\n Давайте я Вам все расскажу! \n\nЯ - бот, который помогает найти интересную информацию для Вас на основе ваших предпочтений и интересов. \n\nДля начала мне нужно узнать ваши интересы. Нажимайте кнопочки под чатом, чтобы выбрать интересующую Вас категорию. \nПосле выбора всех интересующих Вас категорий нажмите кнопку "Закончить выбор", чтобы я начал вам выдавать интересную информацию. \n\nТакже перечисляю ниже свои команды: \n1. /info - Выдать интересную информацию \n2. /add - Добавить интересы\n3. /help - Помощь\n4. /reset - Перевыбрать интересы\n', reply_markup=keyboard)

        db.add_user(message.from_user.username)
    else:
        send_main_message(message)


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
def select_interests_bot(message):
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
    no_shown = [i for i in info if i[2]]

    if len(no_shown):
        doc_id = no_shown[0][0]
    else:
        doc_id = info[random.randint(0, len(info) - 1)][0]

    doc = db.get_doc(doc_id)

    markup = InlineKeyboardMarkup()
    markup.row_width = 5

    is_already_estimated = db.is_already_estimated(
        message.from_user.username, doc_id)

    if not is_already_estimated:
        btn = []
        for i in range(1, 6, 1):
            btn.append(InlineKeyboardButton(
                f'{i}', callback_data=f'{doc_id};{i}'))
        markup.add(*btn)

    bot.send_message(
        message.chat.id, f'{doc[0]}\n\n{doc[1]}', reply_markup=markup)

    if is_already_estimated:
        bot.send_message(
            message.chat.id, 'Пожалуйста, оцените предоставленную информацию. \nЭто поможет мне лучше подбирать для Вас интересную информацию!')
        db.set_shown_info(message.from_user.username, doc_id)


@bot.callback_query_handler(func=lambda call: True)
def handle_query_bot(call):
    text = call.data
    doc_id, rating = str(text).split(';')

    log.info(
        f'({call.from_user.username} set rating ({rating}) to doc({doc_id}))')

    db.set_rating_info(call.from_user.username, doc_id, rating)
    bot.send_message(
        call.from_user.id, 'Спасибо за поставленный рейтинг! \nБлагодаря этому Вы сделали меня лучше! 😉')


# < Дополнительные функции для упрощения работы с ботом >


def show_tegs_admin(message):
    tegs = db.get_all_interests()
    msg = 'Список категорий интересов (индентификаторы и названия): \n\n'
    for teg in tegs:
        msg += '{index}. {name}\n'.format(index=teg[0], name=teg[1])
    bot.send_message(message.chat.id, msg)


def show_docs_admin(message):
    docs = db.get_all_docs()
    msg = 'Список фактов (индентификаторы, названия и теги): \n\n'
    for doc in docs:
        tegs = ', '.join(doc[2])
        msg += '{index}. {name} '.format(index=doc[0], name=doc[1])
        if len(tegs) > 0:
            msg += '({tegs}) \n'.format(tegs=tegs)
        else:
            msg += '\n'
    msg += '\nЕсли выхотите посмотреть описание факта, напишите следующую команду: /get\_teg \*id\*. \nНапример, так: /get\_teg 3\n'
    bot.send_message(message.chat.id, msg)


def show_desc_of_doc_admin(message):
    bot.send_message(
        message.chat.id, 'Напишите идентификатор факта о городе, о котором хотите получить описание. \nДля отмены действия напишите команду /break')
    bot.send_message(
        message.chat.id, 'Введите название факта, а затем с новой строки его описание.')
    bot.register_next_step_handler_by_chat_id(
        message.chat.id, c_show_desc_of_doc_admin)


def c_show_desc_of_doc_admin(message):
    if (message.text != '/break'):
        if message.text.isdigit():
            desc = db.get_doc_for_admin(int(message.text))[1]
            bot.send_message(message.chat.id, '{desc}'.format(desc=desc))
        else:
            bot.send_message(message.chat.id, 'Некорректный ввод данных!')
    else:
        bot.send_message(message.chat.id, 'Действие успешно отменено!')


def add_doc_admin(message):
    bot.send_message(message.chat.id, 'Давайте добавим новый факт! \nОбратите внимание, если название совпадет с названием уже существующего факта, то таким образом вы лишь обновите информацию о нем \nДля отмены действия напишите команду /break')
    bot.send_message(
        message.chat.id, 'Введите название факта, а затем с новой строки его описание.')
    bot.register_next_step_handler_by_chat_id(message.chat.id, c_add_doc_admin)


def c_add_doc_admin(message):
    if (message.text != '/break'):
        try:
            name, desc = message.text.split('\n', maxsplit=1)
            db.add_doc(name, desc)
            bot.send_message(message.chat.id, 'Факт успешно добавлен!')
        except Exception as e:
            bot.send_message(message.chat.id, 'Некорректный ввод данных!')
    else:
        bot.send_message(message.chat.id, 'Действие успешно отменено!')


def add_interest_user(message):
    is_added = db.add_user_interest(
        message.from_user.username, interests_dict.get(message.text.lower()))
    if is_added:
        send_added_interest_message(
            message.from_user.username, message.chat.id, message.text)
    else:
        send_no_added_interest_message(message.chat.id)


def add_interest_admin(message):
    bot.send_message(
        message.chat.id, 'Давайте добавим новую категорию интересов! \nДля отмены действия напишите команду /break')
    bot.send_message(
        message.chat.id, 'Введите название категории интересов.')
    bot.register_next_step_handler_by_chat_id(
        message.chat.id, c_add_interest_admin)


def c_add_interest_admin(message):
    if (message.text != '/break'):
        db.add_interest(message.text)
        bot.send_message(
            message.chat.id, 'Категория интересов успешно добавлена!')
    else:
        bot.send_message(message.chat.id, 'Действие успешно отменено!')


def remove_doc_admin(message):
    bot.send_message(
        message.chat.id, 'Введите уникальный идентификатор факта. \nДля отмены действия напишите команду /break')
    bot.register_next_step_handler_by_chat_id(
        message.chat.id, c_remove_doc_admin)


def c_remove_doc_admin(message):
    if (message.text != '/break'):
        if message.text.isdigit():
            db.remove_doc(int(message.text))
            bot.send_message(message.chat.id, 'Факт успешно удален!')
        else:
            bot.send_message(message.chat.id, 'Некорректный ввод данных!')
    else:
        bot.send_message(message.chat.id, 'Действие успешно отменено!')


def remove_interest_admin(message):
    bot.send_message(
        message.chat.id, 'Введите уникальный идентификатор категории интереса. \nДля отмены действия напишите команду /break')
    bot.register_next_step_handler_by_chat_id(
        message.chat.id, c_remove_interest_admin)


def c_remove_interest_admin(message):
    if (message.text != '/break'):
        if message.text.isdigit():
            db.remove_interest(int(message.text))
            bot.send_message(
                message.chat.id, 'Категория интереса успешно удалена!')
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка!')
    else:
        bot.send_message(message.chat.id, 'Действие успешно отменено!')


def add_interests_to_doc_admin(message):
    bot.send_message(
        message.chat.id, 'Введите через пробел идентификатор факта и идентификатор категории интереса, который хотите присвоить факту. \nДля отмены действия напишите команду /break')
    bot.register_next_step_handler_by_chat_id(
        message.chat.id, c_add_interests_to_doc_admin)


def c_add_interests_to_doc_admin(message):
    if (message.text != '/break'):
        try:
            doc_id, interest_id = message.text.split(' ', 1)
            db.add_interest_to_doc(doc_id, interest_id)
            bot.send_message(
                message.chat.id, 'Категория интереса у факта успешно удалена!')
        except Exception as e:
            bot.send_message(message.chat.id, 'Произошла ошибка!')
    else:
        bot.send_message(message.chat.id, 'Действие успешно отменено!')


def reset_interests_of_doc_admin(message):
    bot.send_message(
        message.chat.id, 'Введите идентификатор факта, у которого Вы хотите сбросить категории интересов. \nДля отмены действия напишите команду /break')
    bot.register_next_step_handler_by_chat_id(
        message.chat.id, c_reset_interests_of_doc_admin)


def c_reset_interests_of_doc_admin(message):
    if (message.text != '/break'):
        if message.text.isdigit():
            db.reset_interests_of_doc(int(message.text))
            bot.send_message(
                message.chat.id, 'Категория интереса у факта успешно удалена!')
        else:
            bot.send_message(message.chat.id, 'Произошла ошибка!')
    else:
        bot.send_message(message.chat.id, 'Действие успешно отменено!')


def send_main_message(message):
    keyboard = get_main_keyboard()
    bot.send_message(
        message.chat.id, 'Для того, чтобы начать работать, выберите одну из функций с помощью кнопок.', reply_markup=keyboard)


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
    keyboard = telebot.types.ReplyKeyboardMarkup(True, row_width=2)
    _btns = [KeyboardButton(command) for command in admins_commands]
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
                    similarity += (1 - math.log(similarity_interests /
                                                db.get_count_interests_of_doc(unappreciated_id))) / 2

                result.append((unappreciated_id, similarity,
                              db.is_already_shown(username, unappreciated_id)))
    else:
        for unappreciated_id in unappreciated:
            similarity = 0

            similarity_interests = db.get_similarity_interest(
                username, unappreciated_id)

            if similarity_interests != 0:
                similarity += (1 - math.log(similarity_interests /
                                            db.get_count_interests_of_doc(unappreciated_id))) / 2

            result.append((unappreciated_id, similarity,
                          db.is_already_shown(username, unappreciated_id)))

    result.sort(key=lambda x: x[1], reverse=True)
    return result

# < Массив: [команды], функция >


admin_triggers = [
    ('Посмотреть список фактов', show_docs_admin),
    ('Посмотреть категории интересов', show_tegs_admin),
    ('Посмотреть информацию о факте', show_desc_of_doc_admin),
    ('Добавить факт', add_doc_admin),
    ('Добавить тег', add_interest_admin),
    ('Удалить факт', remove_doc_admin),
    ('Удалить тег', remove_interest_admin),
    ('Добавить категории интересов у факта', add_interests_to_doc_admin),
    ('Сбросить категории интересов у факта', reset_interests_of_doc_admin),
    ('Назад', send_main_message)
]


@bot.message_handler(commands=['admin'])
def admin_panel_bot(message):
    text = message.text.lower()
    for command, func in admin_triggers:
        if text == command.lower():
            func(message)


triggers = [
    (start_commands, start_bot),
    (select_interests_commands, select_interests_bot),
    (help_commands, get_help_bot),
    (get_info_commands, get_info_bot),
    (reset_commands, reset_interests_bot),
    ([command.lower() for command in admins_commands], admin_panel_bot),
    (['назад'], send_main_message),
]


@bot.message_handler(content_types=['text'])
def process_triggers_bot(message):
    log.info(
        f'Got a message from ({message.from_user.username}) : ({message.text})')

    text = message.text.lower()

    for commands, func in triggers:
        if text in commands:
            func(message)
            return

    if interests_dict.get(text) != None:
        add_interest_user(message)
    else:
        send_error(message)


bot.polling()
