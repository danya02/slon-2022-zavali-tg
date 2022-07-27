import peewee as pw
import yaml
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

@create_table
class Admin(MyModel):
    state = pw.CharField(null=True)
    state_arg = pw.CharField(null=True)
    game_state = pw.CharField(null=True)
    game_state_arg = pw.CharField(null=True)

@create_table
class Team(MyModel):
    name = pw.CharField(null=True)
    join_key = pw.CharField(default=lambda: ''.join([random.choice(string.ascii_uppercase) for _ in range(8)]))
    memory = pw.TextField(default='{}')