from database import *
from helpers import *
import telebot
from telebot import types
from globals import bot

class GamePaused:
    @bot.message_handler(func=AND(is_known_user(), game_state_is('game_paused')))
    @staticmethod
    def announce_pause(chat_id):
        if not isinstance(chat_id, int):
            chat_id = chat_id.chat.id
        print("Announcing pause for", chat_id)
        bot.send_message(chat_id, 'Игра теперь на паузе. Ожидайте сообщений от организаторов.', reply_markup=types.ReplyKeyboardRemove())