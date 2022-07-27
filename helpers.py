from database import *

GET_ADMIN_ID = lambda: int(open('admin.txt', 'r').read().strip())

X = '❌'
TICK = '✅'

def AND(*funcs):
    def func(message):
        for f in funcs:
            if not f(message):
                return False
        return True
    return func

def OR(*funcs):
    def func(message):
        for f in funcs:
            if f(message):
                return True
        return False
    return func

def is_admin():
    return lambda message: message.from_user.id == GET_ADMIN_ID()

def is_unknown_user():
    return lambda message: Team.select().where(Team.telegram_id == message.from_user.id).count() == 0

def is_known_user():
    return lambda message: Team.select().where(Team.telegram_id == message.from_user.id).count() > 0

def game_state_is(state):
    return lambda message: get_admin().game_state == state

def user_state_is(state):
    return lambda message: get_user_state(message).state == state