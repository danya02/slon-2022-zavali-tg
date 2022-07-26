import telebot
from telebot import types
from functools import wraps
from database import *

TOKEN = open('token.txt', 'r').read().strip()
GET_ADMIN_ID = lambda: int(open('admin.txt', 'r').read().strip())

bot = telebot.TeleBot(TOKEN)

def get_admin():
    try:
        return Admin.select().get()
    except Admin.DoesNotExist:
        return Admin.create(state=None, state_arg=None)

def get_user_state(message):
    try:
        return Team.select().where(Team.telegram_id == message.from_user.id).get()
    except Team.DoesNotExist:
        return None

def admin_handler(**kwargs):
    def decorator(func):
        @wraps(func)
        @bot.message_handler(**kwargs, func=lambda m: m.from_user.id == int(open('admin.txt', 'r').read().strip()))
        def wrapper(message):
            admin = get_admin()
            return func(message, admin)
    return decorator

def unknown_user_handler(**kwargs):
    def decorator(func):
        @wraps(func)
        @bot.message_handler(**kwargs, func=lambda m: get_user_state(m) is None)
        def wrapper(message):
            return func(message)
        return wrapper
    return decorator

def user_handler(state=None, **kwargs):
    def decorator(func):
        @wraps(func)
        @bot.message_handler(**kwargs, func=lambda m: get_user_state(m) is not None and ((state is None) or (get_user_state(m).state == state)))
        def wrapper(message):
            return func(message, get_user_state(message))
        return wrapper
    return decorator



@admin_handler(commands=['start'])
def start(message, admin):
    admin.state = None
    admin.state_arg = None
    admin.save()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder="test")
    markup.add('Добавить команду', 'Удалить команду')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Удалить команду', callback_data='delete_team'))
    bot.send_message(message.chat.id, 'Reset interaction state', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'delete_team' and call.from_user.id == GET_ADMIN_ID())
def delete(call):
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



@unknown_user_handler(regexp='Добавить команду')
def add_team(message):
    team = Team.create(telegram_id=message.from_user.id, name=None)
    bot.send_message(message.chat.id, 'Введите название вашей команды. Это нельзя будет изменить!')
    team.state = 'creating_team'
    team.save()
    bot.register_next_step_handler(message, set_new_team_name)

def set_new_team_name(message):
    team = get_user_state(message)
    team.name = message.text
    team.state = None
    team.save()
    bot.send_message(message.chat.id, "Готово! Теперь ваша команда называется: {}".format(team.name))
    bot.send_message(GET_ADMIN_ID(), "Команда {} добавлена".format(team.name))


@unknown_user_handler()
def unknown_user(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Добавить команду')
    bot.send_message(message.chat.id, 'Добро пожаловать в игру Завалинка! Сейчас вы не являетесь капитаном команды.'\
                     'Чтобы создать команду, нажмите на кнопку "Добавить команду".', reply_markup=markup)
    



@bot.message_handler()
def unknown_command(message: types.Message):
    bot.send_message(message.chat.id, 'Я не знаю, что делать с этим сообщением. Пожалуйста, попробуйте ещё раз.')

bot.infinity_polling()
