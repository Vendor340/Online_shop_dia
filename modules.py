from mongoengine import *
from hash_data import hash_data
from bson import ObjectId
from config_app import config
connect(host="mongodb://mongo/first_database")


class Product(Document):
    name = StringField(db_field="name")
    cost = FloatField(db_field="cost")
    count = IntField(db_field="count", default=1)
    _id = ObjectIdField(required=True, primary_key=True, default=ObjectId)
    content_type=StringField(db_field="content_type")
    meta = {'indexes':[{
        "fields":['$name', "content_type"]
        }]
    }



class User(Document):


    name = StringField(db_field="name",required=True)
    password = StringField(db_field="password", required=True)
    cart = ListField(DictField())
    history = ListField(DictField())
    meta = {"allow_inheritance":True}

    def add_product(self, product):
        self.cart.add_product(product)

    def delete_product(self, product):
        self.cart.delete_product(product)




class Admin(User):
    name = StringField(db_field="name", default=hash_data(config.ADMIN_USERNAME))
    password = StringField(db_field="password", default=hash_data(config.ADMIN_PASSWORD))





