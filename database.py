import peewee as pw
import yaml
import json
import random
import string
db = pw.SqliteDatabase('database.db')

class MyModel(pw.Model):
    class Meta:
        database = db

def create_table(cls):
    db.create_tables([cls])
    return cls

def get_words():
    with open('words.yaml') as o:
        return yaml.safe_load(o)

class JSONField(pw.Field):
    db_field = 'text'

    def db_value(self, value):
        return json.dumps(value,)

    def python_value(self, value):
        return json.loads(value)

def get_game_state():
    try:
        return GameState.get()
    except GameState.DoesNotExist:
        return GameState.create()

@create_table
class GameState(MyModel):
    current_round = pw.CharField(null=True)
    current_word_index = pw.IntegerField(null=True)
    phase = pw.CharField(default='waiting')

@create_table
class Team(MyModel):
    name = pw.CharField(unique=True)
    join_key = pw.CharField(default=lambda: ''.join([random.choice(string.ascii_uppercase) for _ in range(8)]))
    memory = JSONField(default={})