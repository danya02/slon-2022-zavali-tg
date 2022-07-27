import peewee as pw
import yaml
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
    telegram_id = pw.IntegerField(unique=True)
    name = pw.CharField(null=True)
    state = pw.CharField(null=True)
    memory = pw.TextField(null=True)

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
