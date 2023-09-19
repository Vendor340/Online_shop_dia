from mongoengine import *

connect(host="mongodb://mongo/telegram_database")


class Customer(Document):
    username = StringField(db_field="username")
    chat_id = IntField(db_field="chat_id", unique=True)
    card = ListField(field=StringField())
    history = ListField(field=DictField())
    language = StringField(db_field="language", default="en")
    meta = {
        "indexes": [{
            'fields': ['chat_id']
        }
        ]
    }


class Product(Document):
    name = StringField(db_field="name")
    count = IntField(db_field="count")
    cost = IntField(db_field="cost")
    tag = StringField(db_field="tag")
    meta = {
        "indexes": [{
            'fields': ['tag', 'name']}
        ]
    }
