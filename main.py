import telebot
from telebot import types

TOKEN = open('token.txt', 'r').read().strip()

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Test')
    btn2 = types.KeyboardButton('Test2')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, 'Welcome', reply_markup=markup)

bot.infinity_polling()
