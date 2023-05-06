import peewee
import config

db = peewee.SqliteDatabase(config.DBPATH)

class Chatlog(peewee.Model):
    chat_id = peewee.IntegerField()
    message_id = peewee.IntegerField()
    user_id = peewee.IntegerField()
    name  = peewee.TextField()
    timestamp = peewee.IntegerField()
    text = peewee.TextField()
    reply_to_message_id = peewee.IntegerField(null=True)

    class Meta:
        database = db
        table_name = 'chatlogs'
        primary_key = False

class Reminders(peewee.Model):
    reply_id = peewee.TextField()
    user_id = peewee.TextField()
    chat_id = peewee.TextField()
    date_now = peewee.TextField()
    date_to_remind = peewee.TextField()
    message = peewee.TextField()

    class Meta:
        database = db
        table_name = 'reminders'
        primary_key = False

class TensorMessage(peewee.Model):
    tensor_text = peewee.TextField()
    tensor_id = peewee.AutoField()

    class Meta:
        database = db
        table_name = 'tensor'

class Quote(peewee.Model):
    quote_text = peewee.TextField()
    quote_id = peewee.AutoField()

    class Meta:
        database = db
        table_name = 'quotes'

class Compleanni(peewee.Model):
    user_id = peewee.TextField()
    chat_id = peewee.TextField()
    birthdate = peewee.TextField()

    class Meta:
        database = db
        table_name = 'compleanni'
        primary_key = False
