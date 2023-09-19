from flask import Flask, render_template, request, redirect, url_for, abort
import modules
import stripe
from hash_data import hash_data, compare_hash
from config_app import config
from initialize_db import client
from json import loads


web_app = Flask(__name__)

web_app.config[
    "PUBLIC_KEY"] = config.STRIPE_PUBLIC_KEY
web_app.config[
    "SECRET_KEY"] = config.STRIPE_SECRET_KEY
db = client.first_database
user = None
users = db.user
products = db.product
stripe.api_key = web_app.config["SECRET_KEY"]


@web_app.route("/", methods=["GET", "POST"])
@web_app.route("/home", methods=["GET", "POST"])
def get_start():
    global cart
    stripe.api_key = web_app.config["SECRET_KEY"]

    username = request.cookies.get("username") if request.cookies.get("username") else None
    password = request.cookies.get("password") if request.cookies.get("password") else None
    cart = []
    total_cost = 0
    web_app.logger.debug(modules.User.objects())
    if username and password:
        cart = [i.cart for i in modules.User.objects(name=username, password=password)][0]

        total_cost = sum([int(i.get("cost")) * int(i.get("count")) for i in cart]) if len(cart) else 0
        if request.method == "POST":
            if request.values.get("Delete"):
                product = request.form.get("Delete")
                user_cart = [user for user in modules.User.objects(name=username, password=password)][0]
                for i in user_cart.cart:
                    if str(i.get('_id')) == product:
                        user_cart.cart.remove(i)
                        user_cart.save()

            if request.form.get("Buy"):
                payment_intent = stripe.PaymentIntent.create(
                    amount=total_cost * 100,
                    currency="usd",
                    payment_method="pm_card_visa"
                )

                return redirect(url_for("card_payment", client_secret=payment_intent.client_secret,
                                        public_key=web_app.config["PUBLIC_KEY"]))

    return render_template("index.html", username=username, cart=cart, total_cost=total_cost,
                           public_key=web_app.config["PUBLIC_KEY"], cookies=request.cookies)


@web_app.route("/payment-gateway", methods=["GET", "POST"])
def card_payment():
    return render_template("payment_gateway.html")


@web_app.route("/success", methods=["GET", "POST"])
def success():

    if request.method == "POST":
        if request.values.get('telegram') == 'True':
            modules.disconnect(alias='default')
            modules.connect(host="mongodb://mongo/telegram_database")
            from app.initialize_db import cart as redis
            from app.models import Customer
            chat_id = request.values.get('chat_id')
            User = Customer.objects(chat_id=int(chat_id))[0]
            for product in redis.lrange(chat_id, 0, -1):
                product = loads(product)
                web_app.logger.debug(product)
                product['_id'] = product['_id']["$oid"]
                User.history += [product]
            User.save()
            redis.delete(chat_id)
            modules.disconnect("default")
            modules.connect(host="mongodb://mongo/first_database")
            return redirect(url_for('get_start'))
        user_data = {"name": request.cookies.get("username"), "password": request.cookies.get("password")}
        for i in users.find_one(user_data).get('cart'):
            product = products.find_one({'_id': i.get('_id')})

            if product:
                product["count"] -= i.get('count')
                products.update_one({'_id': i.get('_id')}, {"$set": {"count": product["count"]}})
            users.update_one(user_data, {"$push": {"history": i}})

        users.update_one(user_data, {'$set': {"cart": []}})
        return redirect(url_for('get_start'))
    return render_template("success.html")


@web_app.route("/login", methods=["GET", "POST"])
def login_page():

    global admin

    respon = web_app.make_response(render_template("login.html"))
    if request.method == "POST":
        name = request.values.get("username") if request.values.get("username") != '' else abort(406)
        password = hash_data(request.values.get("password")) if request.values.get("password") != '' else abort(406)
        if compare_hash(hash_data(name), modules.Admin.name.default) and compare_hash(password,
                                                                                      modules.Admin.password.default):
            admin = modules.Admin(name=name, password=password)
            return redirect(url_for('admin_panel'))
        print([i for i in users.find()])
        for user_in in users.find():
            print(user_in.get("name"), name)

            if user_in.get("name") == name and compare_hash(user_in.get('password'), password):
                respon.set_cookie("username", name)
                respon.set_cookie("password", password)
                return respon

        return redirect("register")
    return respon


@web_app.route("/log_out", methods=["POST"])
def log_out():
    respon = web_app.make_response(redirect(url_for('get_start')))
    respon.set_cookie("username")
    respon.set_cookie("password")
    return respon


@web_app.route("/register", methods=["GET", "POST"])
def register():
    global user
    respon = web_app.make_response(render_template("register.html"))
    if request.cookies.get("username"):
        return redirect("home")
    if request.method == "POST":
        username = request.values.get("username") if request.values.get("username") else abort(406)
        if request.values.get("password") == request.values.get("retry_password"):

            password = hash_data(request.values.get("password")) if request.values.get(
                "password") else abort(406)
            if compare_hash(password, hash_data(modules.Admin.password.default)) and compare_hash(username, hash_data(
                    modules.Admin.name.default)):
                abort(406)

            user = modules.User(name=username, password=password)
            for user_in in users.find():
                if user_in.get("name") == username and compare_hash(user_in.get("password"), password):
                    return redirect(url_for('login_page'))
            user.save()
            respon.set_cookie("username", username)
            respon.set_cookie("password", password)
            return respon
        else:
            abort(403)

    return respon


@web_app.route("/market", methods=["GET", "POST"])
def get_to_market():
    if request.method == "POST":
        if request.values.get("Filter"):
            filter_text = request.values.get("Filter")
            result = [product for product in products.find()]
            if filter_text != "all":
                result = modules.Product.objects(content_type__icontains=filter_text)
                result = [i for i in result.as_pymongo()]
            return render_template("market.html", market=result)
        if request.form.get("Search"):
            text = request.form.get("Search")
            search_product = [i.name for i in modules.Product.objects(name__icontains=text)]
            return render_template("market.html", market=search_product)
        if request.form.get("Buy"):
            try:
                name = request.cookies.get("username")
                password = request.cookies.get("password")
                id = request.form.get("Buy")
                for i in products.find():

                    if str(i.get("_id")) == id:

                        user_cart = \
                            [user for user in modules.User.objects(name=name, password=password)][0]
                        user_cart.cart.append(i)
                        user_cart.cart[-1]['count'] = int(request.values.get("count"))
                        if i["count"] - int(request.values.get("count")) == 0:
                            products.delete_one(i)
                        i["count"] -= int(request.values.get("count"))
                        user_cart.save()
            except AttributeError:
                abort(406, description="You aren't authenticated. Log in or register on this site.")
    market = [i for i in products.find()]
    return render_template("market.html", market=market, filters=set([i.get('content_type') for i in market]))


@web_app.route("/user")
def get_info_user_about():
    user = users.find_one({'name': request.cookies.get('username'), 'password': request.cookies.get('password')})
    print(user)
    history = user["history"] if len(user["history"]) else None
    return render_template("user.html", username=request.cookies.get('username'), history=history)


@web_app.route("/admin")
def admin_panel():
    try:
        if admin or request.form.get("data"):
            return render_template("admin.html")
    except NameError:
        abort(401)


@web_app.route("/admin/users", methods=["GET", "POST"])
def show_users():
    users = db.user
    try:
        if request.method == "POST":
            if request.values.get("add"):
                name = request.values.get("username")
                password = hash_data(request.values.get("password"))
                if name and password:
                    user = modules.User(name=name, password=password)
                    if users.find_one({name: name, password: password}):
                        abort(405)
                    else:
                        user.save()
                else:
                    pass
            elif request.values.get("del"):
                try:
                    name = request.values.get("username")
                    password = hash_data(request.values.get("password"))
                    for user in users.find():
                        if compare_hash(user.get('password'), password) and compare_hash(user.get('name'), name):
                            query = {"name": name, "password": password}
                            users.delete_one(query)

                except TypeError:
                    abort(406)
        users_in = [user for user in users.find()]
        return render_template("users.html", users=users_in)
    except NameError:
        abort(401)


@web_app.route("/admin/products", methods=["GET", "POST"])

def show_products():
    products = db.product
    stripe.api_key = web_app.config["SECRET_KEY"]

    try:
        if request.method == "POST":
            name = request.form.get("Product_name") if request.form.get("Product_name") else abort(406,
                                                                                                   description="Name of product must be written")
            cost = float(request.form.get("Product_cost")) if float(request.form.get("Product_cost")) > 0 else abort(
                406,
                description="Cost of product must be bigger than 0")
            count = int(request.form.get("Product_count")) if int(request.form.get("Product_count")) > 0 else abort(406,
                                                                                                                    description="Product count must be bigger than 0")
            content_type = request.form.get("Product_type") if request.form.get("Product_type") else abort(406,
                                                                                                           description="Product have to have a type!")
            if request.form.get("Add"):
                product = modules.Product(name=name, cost=cost, count=count, content_type=content_type)
                product.save()
            if request.form.get("Del"):
                for item in products.find():
                    print(item.get('name'), item.get('cost'))
                    if item.get('name') == name and item.get('cost') == cost:
                        if item.get('count') - count <= 0:
                            products.delete_one(item)
                        elif item.get('count') - count > 0:

                            new_count = item["count"] - count
                            products.update_one({"name": name, "cost": cost, "count": item.get("count")},
                                                {"$set": {"name": name, "cost": cost, "count": new_count}})

        products_show = [i for i in products.find()]

        return render_template("products.html", admin=admin, products=products_show)
    except NameError:
        abort(401)


if __name__ == "__main__":
    web_app.run(host='0.0.0.0', port=5000, debug=True)
