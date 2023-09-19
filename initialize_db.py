from pymongo import MongoClient

client = MongoClient("mongodb://mongo/first_database")

db = client.first_database

