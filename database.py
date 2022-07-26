from re import T
import peewee as pw
db = pw.SqliteDatabase('database.db')

class MyModel(pw.Model):
    class Meta:
        database = db

def create_table(cls):
    db.create_tables([cls])
    return cls

@create_table
class Admin(MyModel):
    state = pw.CharField(null=True)
    state_arg = pw.CharField(null=True)

@create_table
class Team(MyModel):
    telegram_id = pw.IntegerField()
    name = pw.CharField(null=True)
    state = pw.CharField(null=True)
    memory = pw.TextField(null=True)