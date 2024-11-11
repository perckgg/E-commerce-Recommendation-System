import os, stripe, json
from flask import Flask, request, render_template,redirect, url_for, flash, request, abort
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from .form import LoginForm, RegisterForm
from .db_model import  db,User, Item
from .funcs import mail, send_confirmation_email, fulfill_order
from dotenv import load_dotenv
from .admin.route import admin
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func

import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import uuid

# load files===========================================================================================================
trending_products = pd.read_csv("app/models/trending_products.csv")
train_data = pd.read_csv("app/models/clean_data.csv")

# database configuration---------------------------------------

load_dotenv()
app = Flask(__name__)

app.register_blueprint(admin)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_USERNAME'] = os.environ["EMAIL"]
app.config['MAIL_PASSWORD'] = os.environ["PASSWORD"]
app.config['MAIL_SERVER'] = "smtp.googlemail.com"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_PORT'] = 587
stripe.api_key = os.environ["STRIPE_PRIVATE"]
# db = SQLAlchemy(app)
Bootstrap(app)
db.init_app(app)
mail.init_app(app)
login_manager = LoginManager(app)
login_manager.init_app(app)

with app.app_context():
	db.create_all()

def gen_user_id():
    max_id = db.session.query(func.max(User.id)).scalar()
    if max_id is None:
        return 1  # Trường hợp chưa có người dùng nào, id sẽ bắt đầu từ 1
    return max_id + 1
@app.context_processor
def inject_now():
    return{'now':datetime.now()}
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route("/")
def home():
	items = Item.query.all()
	return render_template("home.html", items=items)

@app.route("/login", methods=['POST', 'GET'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		email = form.email.data
		user = User.query.filter_by(email=email).first()
		if user == None:
			flash(f'User with email {email} doesn\'t exist!<br> <a href={url_for("register")}>Register now!</a>', 'error')
			return redirect(url_for('login'))
		elif check_password_hash(user.password, form.password.data):
			login_user(user)
			return redirect(url_for('home'))
		else:
			flash("Email and password incorrect!!", "error")
			return redirect(url_for('login'))
	return render_template("login.html", form=form)
@app.route('/search')
def search():
	query = request.args['query']
	search = "%{}%".format(query)
	items = Item.query.filter(Item.name.like(search)).all()
	return render_template('home.html', items=items, search=True, query=query)

@app.route("/register", methods=['POST', 'GET'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegisterForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			flash(f"User with email {user.email} already exists!!<br> <a href={url_for('login')}>Login now!</a>", "error")
			return redirect(url_for('register'))
		new_id = gen_user_id()
		new_user = User(id=new_id,name=form.name.data,
						email=form.email.data,
						password=generate_password_hash(
									form.password.data,
									method='pbkdf2:sha256',
									salt_length=8),
						phone=form.phone.data)
		db.session.add(new_user)
		db.session.commit()
		# send_confirmation_email(new_user.email)
		flash('Thanks for registering! You may login now.', 'success')
		return redirect(url_for('login'))
	return render_template("register.html", form=form)

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route("/resend")
@login_required
def resend():
	send_confirmation_email(current_user.email)
	logout_user()
	flash('Confirmation email sent successfully.', 'success')
	return redirect(url_for('login'))

@app.route("/add/<id>", methods=['POST'])
def add_to_cart(id):
	if not current_user.is_authenticated:
		flash(f'You must login first!<br> <a href={url_for("login")}>Login now!</a>', 'error')
		return redirect(url_for('login'))

	item = Item.query.get(id)
	if request.method == "POST":
		quantity = request.form["quantity"]
		current_user.add_to_cart(id, quantity)
		flash(f'''{item.name} successfully added to the <a href=cart>cart</a>.<br> <a href={url_for("cart")}>view cart!</a>''','success')
		return redirect(url_for('home'))

@app.route("/cart")
@login_required
def cart():
	price = 0
	price_ids = []
	items = []
	quantity = []
	for cart in current_user.cart:
		items.append(cart.item)
		quantity.append(cart.quantity)
		price_id_dict = {
			"price": cart.item.price_id,
			"quantity": cart.quantity,
			}
		price_ids.append(price_id_dict)
		price += cart.item.price*cart.quantity
	return render_template('cart.html', items=items, price=price, price_ids=price_ids, quantity=quantity)

@app.route('/orders')
@login_required
def orders():
	return render_template('orders.html', orders=current_user.orders)


@app.route("/remove/<id>/<quantity>")
@login_required
def remove(id, quantity):
	current_user.remove_from_cart(id, quantity)
	return redirect(url_for('cart'))

@app.route('/item/<int:id>')
def item(id):
	item = Item.query.get(id)
	return render_template('item.html', item=item)

# stripe stuffs
@app.route('/payment_success')
def payment_success():
	return render_template('success.html')

@app.route('/payment_failure')
def payment_failure():
	return render_template('failure.html')

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
	data = json.loads(request.form['price_ids'].replace("'", '"'))
	try:
		checkout_session = stripe.checkout.Session.create(
			client_reference_id=current_user.id,
			line_items=data,
			payment_method_types=[
			  'card',
			],
			mode='payment',
			success_url=url_for('payment_success', _external=True),
			cancel_url=url_for('payment_failure', _external=True),
		)
	except Exception as e:
		return str(e)
	return redirect(checkout_session.url, code=303)

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():

	if request.content_length > 1024*1024:
		print("Request too big!")
		abort(400)

	payload = request.get_data()
	sig_header = request.environ.get('HTTP_STRIPE_SIGNATURE')
	ENDPOINT_SECRET = os.environ.get('ENDPOINT_SECRET')
	event = None

	try:
		event = stripe.Webhook.construct_event(
		payload, sig_header, ENDPOINT_SECRET
		)
	except ValueError as e:
		# Invalid payload
		return {}, 400
	except stripe.error.SignatureVerificationError as e:
		# Invalid signature
		return {}, 400

	if event['type'] == 'checkout.session.completed':
		session = event['data']['object']

		# Fulfill the purchase...
		fulfill_order(session)

	# Passed signature verification
	return {}, 200

# Define your model class for the 'signup' table
# class Signup(db.Model):
#     id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     username = db.Column(db.String(100), nullable=False)
#     email = db.Column(db.String(100), nullable=False)
#     password = db.Column(db.String(100), nullable=False)

# # Define your model class for the 'signup' table
# class Signin(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(100), nullable=False)
#     password = db.Column(db.String(100), nullable=False)


# Recommendations functions============================================================================================
# Function to truncate product name
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text


# def content_based_recommendations(train_data, item_name, top_n=10):
#     # Check if the item name exists in the training data
#     if item_name not in train_data['Name'].values:
#         print(f"Item '{item_name}' not found in the training data.")
#         return pd.DataFrame()

#     # Create a TF-IDF vectorizer for item descriptions
#     tfidf_vectorizer = TfidfVectorizer(stop_words='english')

#     # Apply TF-IDF vectorization to item descriptions
#     tfidf_matrix_content = tfidf_vectorizer.fit_transform(train_data['Tags'])

#     # Calculate cosine similarity between items based on descriptions
#     cosine_similarities_content = cosine_similarity(tfidf_matrix_content, tfidf_matrix_content)

#     # Find the index of the item
#     item_index = train_data[train_data['Name'] == item_name].index[0]

#     # Get the cosine similarity scores for the item
#     similar_items = list(enumerate(cosine_similarities_content[item_index]))

#     # Sort similar items by similarity score in descending order
#     similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)

#     # Get the top N most similar items (excluding the item itself)
#     top_similar_items = similar_items[1:top_n+1]

#     # Get the indices of the top similar items
#     recommended_item_indices = [x[0] for x in top_similar_items]

#     # Get the details of the top similar items
#     recommended_items_details = train_data.iloc[recommended_item_indices][['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']]

#     return recommended_items_details
# # routes===============================================================================
# # List of predefined image URLs
# random_image_urls = [
#     "static/img/img_1.png",
#     "static/img/img_2.png",
#     "static/img/img_3.png",
#     "static/img/img_4.png",
#     "static/img/img_5.png",
#     "static/img/img_6.png",
#     "static/img/img_7.png",
#     "static/img/img_8.png",
# ]


# @app.route("/")
# def index():
#     # Create a list of random image URLs for each product
#     random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
#     price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
#     return render_template('index.html',trending_products=trending_products.head(8),truncate = truncate,
#                            random_product_image_urls=random_product_image_urls,
#                            random_price = random.choice(price))

# @app.route("/main")
# def main():
#     return render_template('main.html')

# routes
# @app.route("/index")
# def indexredirect():
#     # Create a list of random image URLs for each product
#     random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
#     price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
#     return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
#                            random_product_image_urls=random_product_image_urls,
#                            random_price=random.choice(price))

# @app.route("/signup", methods=['POST','GET'])
# def signup():
#     if request.method=='POST':
#         username = request.form['username']
#         email = request.form['email']
#         password = request.form['password']
        
#         # Tạo ID ngẫu nhiên và kiểm tra trùng lặp
#         while True:
#             random_id = random.randint(1000, 9999)  # Tạo số ngẫu nhiên với 4 chữ số
#             existing_user = Signup.query.filter_by(id=random_id).first()
#             if not existing_user:  # Nếu không có user nào với ID này, thoát khỏi vòng lặp
#                 break
        
#         new_signup = Signup(id=random_id, username=username, email=email, password=password)
#         db.session.add(new_signup)
#         db.session.commit()

#         # Create a list of random image URLs for each product
#         random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
#         price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
#         return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
#                                random_product_image_urls=random_product_image_urls, random_price=random.choice(price),
#                                signup_message='User signed up successfully!'
#                                )

# # Route for signup page
# @app.route('/signin', methods=['POST', 'GET'])
# def signin():
#     if request.method == 'POST':
#         username = request.form['signinUsername']
#         password = request.form['signinPassword']
#         new_signup = Signin(username=username,password=password)
#         db.session.add(new_signup)
#         db.session.commit()

#         # Create a list of random image URLs for each product
#         random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
#         price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
#         return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
#                                random_product_image_urls=random_product_image_urls, random_price=random.choice(price),
#                                signup_message='User signed in successfully!'
#                                )
# @app.route("/recommendations", methods=['POST', 'GET'])
# def recommendations():
#     if request.method == 'POST':
#         prod = request.form.get('prod')
#         nbr = int(request.form.get('nbr'))
#         content_based_rec = content_based_recommendations(train_data, prod, top_n=nbr)

#         if content_based_rec.empty:
#             message = "No recommendations available for this product."
#             return render_template('main.html', message=message)
#         else:
#             # Create a list of random image URLs for each recommended product
#             random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
#             print(content_based_rec)
#             print(random_product_image_urls)

#             price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
#             return render_template('main.html', content_based_rec=content_based_rec, truncate=truncate,
#                                    random_product_image_urls=random_product_image_urls,
#                                    random_price=random.choice(price))


# if __name__=='__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)