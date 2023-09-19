from telethon import events, TelegramClient, errors
from telethon.tl.custom import Button
from messages import *
from initialize_db import cart
from models import Customer, Product
from json import dumps, loads
import logging
from payments import get_payment_intent, public_key
from mongoengine.errors import NotUniqueError
from config import Config
config = Config()
logging.basicConfig(level=logging.DEBUG)
bot = TelegramClient(api_hash=config.api_hash, api_id=config.api_id, session="Shop_dia")


@bot.on(events.NewMessage(incoming=True, pattern="/admin"))
async def admin(event):
    chat = await event.get_chat()
    user_id = event.sender_id
    keyboard = [[Button.text(i)] for i in ["show_products", "show_users", "add_product", "delete_product"]]
    if user_id == 1184514582:
        await bot.send_message(chat, "Welcome to the admin panel of telegram bot!", buttons=keyboard)


@bot.on(events.NewMessage(incoming=True, pattern="add_product"))
async def add_product(event):
    logging.debug("Creating product is starting!")
    chat = await event.get_chat()
    async with bot.conversation(chat) as con:
        await con.send_message("Enter name of product:")
        name = await con.get_response()
        await con.send_message("Enter cost of product:")
        cost = await con.get_response()
        await con.send_message("Enter count of product:")
        product_count = await con.get_response()
        await con.send_message("Enter type of product:")
        type_product = await con.get_response()
        product = Product(name=name.text, cost=float(cost.text), count=int(product_count.text), tag=type_product.text)

        product.save()
    logging.info("Product is created successfully!")


@bot.on(events.NewMessage(incoming=True, pattern="show_products"))
async def show_products(event):
    chat = await event.get_chat()
    for index, product in enumerate(Product.objects):
        await bot.send_message(chat, f"{index + 1}) {product.name}: cost={product.cost}, count="
                                     f"{product.count}, id={product.id}, type={product.tag}")
    logging.info("Products have been shown!")


@bot.on(events.NewMessage(incoming=True, pattern="show_users"))
async def show_users(event):
    chat = await event.get_chat()
    print(Customer.objects)
    for index, user in enumerate(Customer.objects):
        user = user.to_mongo()
        await bot.send_message(chat,
                               f"{index + 1}) name: {user.get('username')}\nchat_id: {user.get('chat_id')}\ncart: "
                               f"{user.get('cart')}\n"
                               f"language: {user.get('language')}")


@bot.on(events.NewMessage(incoming=True, pattern="delete_product"))
async def delete_product(event):
    chat = await event.get_chat()
    async with bot.conversation(chat) as conv:
        await conv.send_message("Enter the ID of product:")
        id_product = await conv.get_response()
        id_product = id_product.text
    for product in Product.objects(id=id_product):
        product.delete()
        product.save()


@bot.on(events.NewMessage(incoming=True, pattern="/start"))
async def start(event):
    global User
    chat = await event.get_chat()
    chat_id = event.chat_id
    sender = await event.get_sender()
    username = sender.first_name + " " + sender.last_name

    try:
        User = Customer(username=username, chat_id=chat_id)
        User.save()
    except NotUniqueError:
        logging.warning("User already exists!")
        User = Customer.objects(chat_id=chat_id).first()
    keyboard = [[Button.text(i)] for i in ["/cart", "/marketplace", "/profile", "/settings"]]
    if User.language == "en":
        await bot.send_message(chat, "Welcome to the Telegram shop bot!", buttons=keyboard)
        await bot.send_message(chat, "My website!", buttons=[[
            Button.url(text='my website!',
                       url='http://127.0.0.1:5000/')]])
    else:
        print(User.language)
        await bot.send_message(chat, translate_languages[User.language].get("Welcome to the Telegram shop bot!"),
                               buttons=keyboard)
        await bot.send_message(chat, translate_languages[User.language]["my website"],
                               buttons=[[
                                   Button.url(text='my website!',
                                              url='http://127.0.0.1:5000/')]]
                               )
    logging.debug(f"User initialize with this data:\nName:{User.username}\nchat_id:{User.chat_id}")


@bot.on(events.NewMessage(incoming=True, pattern="/settings"))
async def settings(event):
    chat = await event.get_chat()
    settings = [[Button.inline(text=option, data=option)] for option in ["set_language"]]
    if User.language == "en":
        await bot.send_message(chat, "What do you want to do in settings?", buttons=settings)
    else:
        await bot.send_message(chat, translate_languages[User.language].get("What do you want to do in settings?"),
                               buttons=settings)


@bot.on(events.CallbackQuery(pattern="set_"))
async def change_settings(event):
    chat = await event.get_chat()
    async with bot.conversation(chat) as conver:
        if event.data.decode("UTF-8") == "set_language":
            keyboard = [[Button.inline(lang, code)] for lang, code in
                        zip(["english", "russian", "ukrainian"], ["/language_en", "/language_ru", "/language_ua"])]
            if User.language == "en":
                await conver.send_message("Enter language which you prefer:", buttons=keyboard)
            else:
                await conver.send_message(translate_languages[User.language].get("Enter language which you prefer:"),
                                          buttons=keyboard)

@bot.on(events.CallbackQuery(pattern="/language"))
async def language(event):
    print("Setting language is starting!")
    chat = await event.get_chat()
    data = event.data.decode("UTF-8").split("_")[1]
    User.language = data
    User.save()
    if User.language == "en":
        await bot.send_message(chat, "Changing language is successful!")
    else:
        await bot.send_message(chat, translate_languages[User.language].get("Changing language is successful!"))
    logging.debug(f"Language has been set: {User.language}")
    logging.info("Setting language is finished")


@bot.on(events.NewMessage(incoming=True, pattern="/marketplace"))
async def marketplace(event):
    print("Shop's market place is showing!")
    chat = await event.get_chat()
    try:
        datas = [{'text':str(product.name), 'data':f"buy_{product.id}"} for product in Product.objects]
        print(datas)
        buttons = [Button.inline(**product) for product in datas]
        filters = list(map(Button.inline, set(['filter_' + filt.tag for filt in Product.objects]))) + [
            Button.inline(text="/search", data="/search")]
        if User.language != "en":
            await bot.send_message(chat, translate_languages[User.language]["marketplace"], buttons=buttons)
            await bot.send_message(chat, translate_languages[User.language]["Filters"], buttons=filters)
        else:
            await bot.send_message(chat, "marketplace", buttons=buttons)
            await bot.send_message(chat, "Filters", buttons=filters)
    except errors.ReplyMarkupInvalidError:
        logging.error("Products absent in the shop!")
    finally:
        logging.info("Showing marketplace is end!")


@bot.on(events.CallbackQuery(pattern="/search"))
async def search_product(event):
    chat = await event.get_chat()
    async with bot.conversation(chat) as conv:
        await conv.send_message("Enter product which you search?: ")
        search = await conv.get_response()
        search = search.text
    products = [Button.inline(text=product.name, data=f'buy_{product.id}') for product in
                Product.objects(name__icontains=search)]
    await bot.send_message(chat, "Search result:", buttons=products)


@bot.on(events.CallbackQuery(pattern="filter_"))
async def filtering_products(event):
    chat_id = event.chat_id
    data = event.data.decode("UTF-8")
    data = data.split("_")[1]
    products = [Button.inline(text=product.name, data="buy_" + str(product.id)) for product in
                Product.objects(tag=data)]
    await bot.send_message(chat_id, "filter result:", buttons=products)


@bot.on(events.CallbackQuery(pattern="buy_"))
async def add_product_to_cart(event):
    chat = await event.get_chat()
    data = event.data.decode("UTF-8")
    product_id = data.split("_")[1]
    product = Product.objects(id=product_id).first().to_mongo()
    cart.set('max_count', str(product['count']))
    cart.set('count', '0')
    add_and_minus = [Button.inline(symbol, command) for symbol, command in
                     zip(["+", "-", "submit"],
                         [f"/cart_add_{product_id}", f"/cart_substracte_{product_id}",
                          f"/cart_submit_{product_id}"])]
    if User.language != "en":
        await bot.send_message(chat, f"{translate_languages[User.language]['Max count of']} {product['name']}: "
                                     f"{product['count']}", buttons=add_and_minus)
    else:
        await bot.send_message(chat, f"Max count of {product['name']}: {product['count']}",
                               buttons=add_and_minus)


@bot.on(events.CallbackQuery(pattern="/cart_"))
async def change_count(callback):
    chat = await callback.get_chat()
    chat_id = callback.chat_id
    command = callback.data.decode("UTF-8").split("_")[1]
    data = callback.data.decode("UTF-8").split("_")[-1]
    maxi = int(cart.get('max_count'))
    count = int(cart.get('count'))
    product = Product.objects(id=data).first()
    logging.debug(product)
    if command == "add" and count < int(maxi):
        count += 1
        cart.set('count', str(count))

    elif command == "substracte" and count > 0:
        count -= 1
        cart.set('count', str(count))

    elif command == "submit":
        product.count -= count
        product.save()
        logging.debug(f'Count of product: {product.count}')
        product_cart = loads(product.to_json())
        product_cart['count'] = count
        cart.lpush(str(chat_id), dumps(product_cart))
        if User.language != "en":
            await bot.send_message(chat, translate_languages[User.language]["Your product have been added to cart successfully!"])
        else:
            await bot.send_message(chat, "Your product have been added to cart successfully!")

        logging.info(f"{product} have been added to cart!")
        cart.delete('max-count')
        cart.delete('count')

    await bot.send_message(chat, f'{product.name}: {count}')


@bot.on(events.NewMessage(incoming=True, pattern="/cart"))
async def show_cart(event):
    chat = await event.get_chat()
    chat_id = event.chat_id
    try:
        show_cart = cart.lrange(str(chat_id), 0, -1)
        amount = 0
        for num, product in enumerate(show_cart):
            product = loads(product)
            logging.debug(product)
            keyboard = [Button.inline('/delete_product', f'/delete_{product["_id"]["$oid"]}'),
                         ]
            await bot.send_message(chat,
                                   f"{num + 1}) {product['name']}: cost={product['cost']}, count={product['count']}, "
                                   f"id={product['_id']['$oid']}", buttons=keyboard)

            amount += int(product['cost']) * int(product['count'])
        if amount > 0:
            if User.language != "en":
                await bot.send_message(chat, f"\n{translate_languages[User.language]['Amount']}: {amount}$",
                                       buttons=[Button.inline('/buy', f"/buy_{amount}")])
            else:
                await bot.send_message(chat, f"Amount:{amount}",  buttons=[Button.inline('/buy', f"/buy_{amount}")])
    except TypeError:
        await bot.send_message(chat, "Cart haven't products yet!")


@bot.on(events.CallbackQuery(pattern="/buy"))
async def buying_product(event):
    chat_id = event.chat_id
    amount = event.data.decode("UTF-8").split("_")[1]
    payment_intent = get_payment_intent(amount=int(amount), currency='usd')
    if User.language != "en":
        await bot.send_message(chat_id, translate_languages[User.language]["Payment gateway"], buttons=[[
            Button.url(text='payment',
                       url='http://127.0.0.1:5000/'
                           'payment-gateway?'
                           f'client_secret={payment_intent.client_secret}&public_key={public_key}&telegram=True&chat_id={chat_id}')]])
    else:
        await bot.send_message(chat_id, "Payment gateway", buttons=[[
            Button.url(text='payment',
                       url='http://127.0.0.1:5000/'
                           'payment-gateway?'
                           f'client_secret={payment_intent.client_secret}&public_key={public_key}&telegram=True&chat_id={chat_id}')]])


@bot.on(events.CallbackQuery(pattern="/delete_"))
async def delete_product(event):
    chat = await event.get_chat()
    chat_id = event.chat_id
    data = event.data.decode("UTF-8").split("_")[-1]
    print(chat_id)
    for product in cart.lrange(str(chat_id), 0, -1):
        product_r = loads(product)
        logging.debug(product_r.get('_id')['$oid']+"___"+data)
        logging.debug(product_r.get('_id')['$oid'] == data)
        if product_r.get('_id')['$oid'] == data:
            pos = cart.lpos(str(chat_id), product)
            cart.lrem(str(chat_id), pos, product)
            if User.language != "en":
                await bot.send_message(chat, translate_languages[User.language]['Product have been deleted successfully!'])
            else:
                await bot.send_message(chat, 'Product have been deleted successfully!')


@bot.on(events.NewMessage(incoming=True, pattern="/profile"))
async def show_profile(event):
    chat = await event.get_chat()
    data = User.to_mongo()
    if User.language != "en":
        await bot.send_message(chat,
                           f"{translate_languages[User.language]['Name']}: {data.get('username')}\n"
                           f"{translate_languages[User.language]['ID']}: {data.get('chat_id')}\n"
                           f"{translate_languages[User.language]['History']}: {data.get('history')}\n"
                           f"{translate_languages[User.language]['Language']}: {data.get('language')}")
    else:
        await bot.send_message(chat,
                               f"Name: {data.get('username')}\n"
                               f"ID: {data.get('chat_id')}\n"
                               f"History: {data.get('history')}\n"
                               f"Language: {data.get('language')}")


if __name__ == "__main__":
    bot.start(bot_token=config.token)
    bot.run_until_disconnected()
