from os import stat
import telebot
from telebot import types
from database import *
from helpers import *
from globals import bot
import json
import traceback

class GameAcceptingAnswers:
    @bot.message_handler(func=AND(is_known_user(), game_state_is(None)))
    def game_not_started(message):
        bot.send_message(message.chat.id, 'Игра пока что не началась, подождите начала игры')
    
    @bot.message_handler(func=AND(is_known_user(), game_state_is('round_accepting_answers')), commands=['start'])
    @staticmethod
    def round_welcome(chat_id):
        if not isinstance(chat_id, int):
            chat_id = chat_id.chat.id
        print("Round welcome for", chat_id)
        admin = get_admin()
        if admin.game_state != 'round_accepting_answers': 
            print("!!! Called round_welcome while game_state is", admin.game_state, "and not round_accepting_answers !!!")
        try:
            team = Team.get(Team.telegram_id == chat_id)
        except Team.DoesNotExist:
            print("!!! Called round_welcome while team with chat_id", chat_id, "does not exist !!!")
            return

        words = get_words()
        current_round = words[admin.game_state_arg]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        team_memory = json.loads(team.memory or '{}')
        for index, word in enumerate(current_round):
            is_submitted = X
            if str(index) in team_memory:
                is_submitted = TICK

            line = f'{index + 1}. {word} {is_submitted}'
            markup.add(line)


        bot.send_message(chat_id, f'Сейчас идет раунд {current_round["name"]}. Выберите слово, обманку которого вы хотите предложить', reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, GameAcceptingAnswers.choose_word_to_submit_fake)

    
    @staticmethod
    def choose_word_to_submit_fake(message):
        admin = get_admin()
        if admin.game_state != 'round_accepting_answers': 
            print("!!! Called choose_word_to_submit_fake while game_state is", admin.game_state, "and not round_accepting_answers !!!")
            bot.reply_to(message, 'Сейчас нельзя отправить обманку. Нажмите /start для продолжения')
            return
        try:
            team = Team.get(Team.telegram_id == message.chat.id)
        except Team.DoesNotExist:
            print("!!! Called choose_word_to_submit_fake while team with chat_id", message.chat.id, "does not exist !!!")
            bot.reply_to(message, 'Сейчас нельзя отправить обманку. Нажмите /start для продолжения')
            return
        
        words = get_words()
        current_round = words[admin.game_state_arg]
        try:
            index = message.text.split('.')[0]
            index = int(index) - 1
            word = current_round['words'][index]
        except:
            bot.reply_to(message, traceback.format_exc())
            bot.send_message(message.chat.id, 'Такое слово не найдено, попробуйте еще раз')
            return GameAcceptingAnswers.round_welcome(message.chat.id)
        
        team_memory = json.loads(team.memory or '{}')
        if str(index) in team_memory:
            bot.send_message(message.chat.id, 'Вы уже отправили обманку на это слово:')
            bot.send_message(message.chat.id, team_memory[str(index)])
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Новая обманка')
            markup.add(X + ' Не изменять эту обманку')
            bot.send_message(message.chat.id, 'Напишите новую обманку на замену этой или нажмите на кнопку отмены:', reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(message.chat.id, GameAcceptingAnswers.submit_fake, word_index=index)
            return
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, input_field_placeholder='Новая обманка')
            markup.add(X + ' Не писать обманку')
            bot.send_message(message.chat.id, 'На это слово пока что не отправлена обманка. Напишите обманку для этого слова (потом её можно изменить), или нажмите на кнопку отмены:')
            bot.register_next_step_handler_by_chat_id(message.chat.id, GameAcceptingAnswers.submit_fake, word_index=index)
    
    
    @staticmethod
    def submit_fake(message, word_index):
        admin = get_admin()
        if admin.game_state != 'round_accepting_answers': 
            print("!!! Called choose_word_to_submit_fake while game_state is", admin.game_state, "and not round_accepting_answers !!!")
            bot.reply_to(message, 'Сейчас нельзя отправить обманку. Нажмите /start для продолжения')
            return
        try:
            team = Team.get(Team.telegram_id == message.chat.id)
        except Team.DoesNotExist:
            print("!!! Called choose_word_to_submit_fake while team with chat_id", message.chat.id, "does not exist !!!")
            bot.reply_to(message, 'Сейчас нельзя отправить обманку. Нажмите /start для продолжения')
            return
        
        words = get_words()
        current_round = words[admin.game_state_arg]
        current_word = current_round['words'][word_index]
        fake = message.text
        if X in fake:
            bot.send_message(message.chat.id, f'''Обманка на слово "{current_word['text']}" не изменена.''')
            return GameAcceptingAnswers.round_welcome(message.chat.id)
        else:
            team_memory = json.loads(team.memory or '{}')
            team_memory[str(word_index)] = fake
            team.memory = json.dumps(team_memory)
            team.save()
            bot.send_message(message.chat.id, f'''Готово! Ваша новая обманка:\n {current_word['text']}: {fake}''')
            return GameAcceptingAnswers.round_welcome(message.chat.id)


    @bot.message_handler(func=AND(is_known_user(), game_state_is('round_accepting_answers')))
    @staticmethod
    def unknown_during_accepting_answers(message):
        bot.send_message(message.chat.id, 'Я не знаю, что делать с этим сообщением. Попробуйте начать заново с помощью /start.')
        return GameAcceptingAnswers.round_welcome(message.chat.id)
