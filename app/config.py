from os import environ
class Config:
    api_id = environ["API_ID"]
    api_hash = environ["API_HASH"]
    token = environ["TOKEN"]