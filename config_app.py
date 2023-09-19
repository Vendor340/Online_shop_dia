from os import environ


class Config:
    def __init__(self):
        self.STRIPE_SECRET_KEY = environ["STRIPE_SECRET_KEY"]
        self.STRIPE_PUBLIC_KEY = environ["STRIPE_PUBLIC_KEY"]
        self.ADMIN_USERNAME = environ["ADMIN_USERNAME"]
        self.ADMIN_PASSWORD = environ["ADMIN_PASSWORD"]


config = Config()
