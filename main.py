import telebot
from telebot import types
import globals
import json

TOKEN = open('token.txt', 'r').read().strip()

bot = telebot.TeleBot(TOKEN)
globals.bot = bot

import logging

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

from functools import wraps
from database import *
from helpers import *
from game_states import GAME_STATES


def unknown_user_handler(**kwargs):
    def decorator(func):
        @wraps(func)
        @bot.message_handler(**kwargs, func=lambda m: get_user_state(m) is None)
        def wrapper(message):
            return func(message)
        return wrapper
    return decorator

def user_handler(state=None, game_state=None, **kwargs):
    def decorator(func):
        @wraps(func)
        @bot.message_handler(**kwargs, func=lambda m: get_user_state(m) is not None and
                                                        ((state is None) or (get_user_state(m).state == state))
                                                        and ((game_state is None) or (get_admin().game_state == game_state)))
        def wrapper(message):
            return func(message, get_user_state(message))
        return wrapper
    return decorator



@bot.message_handler(commands=['start', 's'], func=is_admin())
def admin_start(message):
    admin = get_admin()
    admin.state = None
    admin.state_arg = None
    admin.save()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Удалить команду', callback_data='delete_team'))
    markup.add(types.InlineKeyboardButton('Показать состояние игры', callback_data='show_game_state'))
    markup.add(types.InlineKeyboardButton('Перевести игру в новое состояние', callback_data='change_game_state'))
    bot.send_message(message.chat.id, 'Reset interaction state', reply_markup=markup)

@bot.callback_query_handler(func=AND(lambda call: call.data == 'delete_team', is_admin()))
def delete(call):
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for team in Team.select():
        markup.add(str(team.id) + '. ' + team.name)

    bot.send_message(call.message.chat.id, 'Введите номер команды для удаления', reply_markup=markup)
    bot.register_next_step_handler(call.message, delete_team_by_id)

def delete_team_by_id(message):
    id = message.text.split('.')[0]
    try:
        id = int(id)
    except ValueError:
        bot.send_message(message.chat.id, 'Неверный формат номера')
        return
    try:
        team = Team.select().where(Team.id == id).get()
        team.delete_instance()
        bot.send_message(message.chat.id, "Команда {} удалена".format(message.text))
        bot.send_message(team.telegram_id, f"Ваша команда {team.name} была удалена.")
    except Team.DoesNotExist:
        bot.send_message(message.chat.id, 'Команда не найдена')


@bot.callback_query_handler(func=AND(lambda call: call.data == 'show_game_state', is_admin()))
def show_game_state(call):
    bot.answer_callback_query(call.id)
    admin = get_admin()
    memory_str = ''
    team_count = 0
    for team in Team.select():
        team_count += 1
        memory_str += str(team.id) + '. ' + str(team.name) + ': ' + str(json.loads(team.memory or '{}')) + '\n'
    state = f'''Current state: {admin.game_state} : {admin.game_state_arg}
Teams: {team_count}
Memory:
''' + memory_str

    bot.send_message(call.message.chat.id, state)

@bot.callback_query_handler(func=AND(lambda call: call.data == 'change_game_state', is_admin()))
def change_game_state(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)
    admin = get_admin()
    markup = types.InlineKeyboardMarkup()
    for state in GAME_STATES:
        markup.add(types.InlineKeyboardButton(state.name, callback_data='set_game_state:' + state.name))
    bot.send_message(call.message.chat.id, 'Выберите новое состояние игры', reply_markup=markup)

@bot.callback_query_handler(func=AND(lambda call: call.data.startswith('set_game_state:'), is_admin()))
def set_game_state(call):
    bot.answer_callback_query(call.id)
    target_state = call.data.split(':')[1]
    admin = get_admin()
    markup = types.ReplyKeyboardMarkup(input_field_placeholder='game_state_arg')
    markup.add(X)
    bot.send_message(call.message.chat.id, 'Введите аргумент для состояния игры', reply_markup=markup)
    bot.register_next_step_handler(call.message, set_game_state_arg, target_state)

def set_game_state_arg(message, target_state):
    if X in message.text:
        bot.send_message(message.chat.id, 'Отмена!')
        return
    admin = get_admin()
    for state in GAME_STATES:
        if state.name == target_state:
            state.enter(message.text)
            return bot.send_message(message.chat.id, 'Состояние игры изменено')
    print("!!! Could not find state", target_state, "despite being chosen by button !!!")
    bot.send_message(message.chat.id, 'Не найдено состояние ' + target_state)


@bot.message_handler(func=is_admin())
def unknown_admin_handler(message):
    bot.send_message(message.chat.id, 'Unknown message')
    return admin_start(message)

@bot.message_handler(regexp='Добавить команду', func=is_unknown_user())
def add_team(message):
    team = Team.create(telegram_id=message.from_user.id, name=None)
    bot.send_message(message.chat.id, 'Введите название вашей команды. Это нельзя будет изменить!')
    team.state = 'creating_team'
    team.save()
    bot.register_next_step_handler(message, set_new_team_name)

def set_new_team_name(message):
    if X in message.text:
        team = get_user_state(message)
        team.delete_instance()
        bot.send_message(message.chat.id, 'Создание команды отменено. Нажмите /start, чтобы продолжить.')
    team = get_user_state(message)
    team.name = message.text
    team.state = None
    team.save()
    bot.send_message(message.chat.id, "Готово! Теперь ваша команда называется: {}".format(team.name))
    bot.send_message(GET_ADMIN_ID(), "Команда {} добавлена".format(team.name))



@bot.message_handler(func=is_unknown_user())
def unknown_user(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Добавить команду')
    bot.send_message(message.chat.id, 'Добро пожаловать в игру Завалинка! Сейчас вы не являетесь капитаном команды.'\
                     'Чтобы создать команду, нажмите на кнопку "Добавить команду".', reply_markup=markup)
    



@bot.message_handler()
def unknown_command(message: types.Message):
    bot.send_message(message.chat.id, 'Я не знаю, что делать с этим сообщением. Пожалуйста, попробуйте ещё раз.')

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

bot.infinity_polling()
