from database import *
from helpers import *
import telebot
from telebot import types
import game_accepting_answers
import game_paused
from globals import bot

class AcceptingAnswersState:
    name = 'round_accepting_answers'
    def enter(round_name):
        print("Entering AcceptingAnswersState")
        admin = get_admin()
        admin.game_state = 'round_accepting_answers'
        admin.game_state_arg = round_name
        admin.save()
        game_accepting_answers.GameAcceptingAnswers.bot = bot
        for team in Team.select():
            print(team)
            telebot.util.antiflood(game_accepting_answers.GameAcceptingAnswers().round_welcome, team.telegram_id)

class PauseState:
    name = 'game_paused'
    def enter(round_name):
        print("Entering PauseState")
        admin = get_admin()
        admin.game_state = 'game_paused'
        admin.save()
        for team in Team.select():
            telebot.util.antiflood(game_paused.GamePaused().announce_pause, team.telegram_id)


GAME_STATES = [AcceptingAnswersState, PauseState]