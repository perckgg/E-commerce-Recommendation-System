import os, json,requests,uuid
from flask import Flask, request, render_template,redirect, url_for, flash, request,jsonify
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from flask_dance.contrib.google import make_google_blueprint, google
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from .form import LoginForm, RegisterForm,RequestResetForm,ResetPasswordForm
from .db_model import  db,User, Item,Comment,Category
from .funcs import mail, send_confirmation_email, fulfill_order
from dotenv import load_dotenv
from .admin.route import admin
from itsdangerous import URLSafeTimedSerializer,SignatureExpired, BadSignature
from datetime import datetime
import re
from sqlalchemy.sql import text
from sqlalchemy import func, desc
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
MODEL_SERVER_URL = "http://192.168.1.117:7000/recommend"


os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
load_dotenv()
app = Flask(__name__)

app.register_blueprint(admin)
google_bp = make_google_blueprint(
	client_id=os.environ.get('GOOGLE_CLIENT_ID'),
	client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
 	redirect_url="callback",
   	 scope=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]
)
app.register_blueprint(google_bp, url_prefix="/login")
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_USERNAME'] = os.environ["EMAIL"]
app.config['MAIL_PASSWORD'] = os.environ["PASSWORD"]
app.config['MAIL_SERVER'] = "smtp.googlemail.com"
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_PORT'] = 587
app.config['SECURITY_PASSWORD_SALT'] = os.getenv("SECURITY_PASSWORD_SALT")

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
    # Danh mục chính
    cats = (
        Category.query.with_entities(Category.main_category)
        .distinct()
        .order_by(Category.main_category.asc())
        .all()
    )

    # Danh sách sản phẩm gốc
    items = Item.query.limit(15)

    # Danh sách sản phẩm theo giá tăng dần
    items_by_price = Item.query.order_by(Item.price.asc()).limit(15)

    # Danh sách sản phẩm theo tên (alphabet)
    items_by_name = Item.query.order_by(Item.name.asc()).limit(15)

    return render_template(
        "home.html", 
        items=items, 
        items_by_price=items_by_price, 
        items_by_name=items_by_name, 
        cats=cats
    )


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
@app.route("/login/google/callback")
def google_login():
    # Kiểm tra xem người dùng có được xác thực trên Google không
    if not google.authorized:
        return redirect(url_for("google.login"))

    # Lấy thông tin người dùng từ Google
    resp = google.get("/oauth2/v2/userinfo")
    if resp.ok:
        user_info = resp.json()
        email = user_info["email"]

        # Kiểm tra xem người dùng đã tồn tại trong CSDL hay chưa
        user = User.query.filter_by(email=email).first()
        if not user:
            new_id = gen_user_id()
            user = User(id=new_id,
                name=user_info["name"],
                email=email,
                email_confirmed=True  # Đánh dấu là đã xác thực email
            )
            db.session.add(user)
            db.session.commit()

        # Đăng nhập người dùng với Flask-Login
        login_user(user)
        flash("Đăng nhập thành công bằng Google!", "success")
        return redirect(url_for("home"))
    else:
        flash("Đã xảy ra lỗi khi đăng nhập với Google.", "error")
        return redirect(url_for("login"))
@app.route('/search')
def search():
    query = request.args.get('query', '').strip()  # Lấy từ khóa và loại bỏ khoảng trắng thừa
    page = request.args.get('page', 1, type=int)  # Trang hiện tại, mặc định là 1
    per_page = 16  # Số lượng sản phẩm mỗi trang
    max_pages = 50
    if not query:  # Nếu không có từ khóa, trả về thông báo
        flash("Please enter a keyword to search.", "info")
        return redirect(url_for('home'))

    # Tìm kiếm sản phẩm theo từ khóa
    search = f"%{query}%"
    items_query = (
        db.session.query(Item)
        .join(Category, Item.category == Category.id)  # Thực hiện join với bảng Category
        .filter(
            db.or_(
                Item.name.ilike(search),
                Category.main_category.ilike(search),  
            )
        )
        .order_by(Item.rating.desc(), Item.rating_count.desc())
    )

    # Tổng số sản phẩm và số trang
    total_items = items_query.count()
    total_pages = min((total_items + per_page - 1) // per_page, max_pages)
    start_page = max(1, page - 1)
    end_page = min(total_pages, page + 2)
    # Lấy sản phẩm cho trang hiện tại
    items = (
        items_query
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Hiển thị kết quả tìm kiếm
    return render_template(
        "search_result.html",
        items=items,
        query=query,
        current_page=page,
        total_pages=total_pages,
        max_pages=max_pages,
        start_page=start_page,
        end_page=end_page
    )


@app.route('/category')
def search_by_category():
    cats = Category.query.all()
    category = request.args.get('name','').strip()
    limit = request.args.get('limit',10,type=int)
    if not category:  # Nếu không có từ khóa, trả về tất cả sản phẩm
        flash("Please enter a keyword to search.", "info")
        return redirect(url_for('home'))
    cat = f"%{category}%"
    items = (
        Item.query.filter(Item.category.ilike(cat))  # Filter by category
        .order_by(Item.rating_count.desc())  # Sort by rating_count descending
        .limit(limit)  # Limit the number of results
        .all()  # Fetch the results
    )
    if not items:
        items = Item.query.order_by(Item.rating.desc(), Item.rating_count.desc()).limit(10).all()

    return render_template('home.html', items=items, category=True,name=category,cats=cats)

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify([])

    # Tìm sản phẩm bắt đầu với từ khóa
    search = f"{query}%"
    items = Item.query.filter(Item.name.ilike(search)).limit(5).all()
    main_categories = (
        Category.query.with_entities(Category.main_category)
        .filter(Category.main_category.ilike(search))
        .distinct()
        .limit(5)
        .all()
    )
    sub_categories = (
        Category.query.with_entities(Category.sub_category)
        .filter(Category.sub_category.ilike(search))
        .distinct()
        .limit(5)
        .all()
    )

    # Chuyển đổi kết quả sang JSON
    results = []
    results.extend([{'type': 'item', 'id': item.id, 'name': item.name, 'image_url': item.image} for item in items])
    results.extend([{'type': 'category', 'name': category.main_category, 'id': None, 'image_url': None} for category in main_categories])
    results.extend([{'type': 'category', 'name': category.sub_category, 'id': None, 'image_url': None} for category in sub_categories])
    return jsonify(results)

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
		quantity = request.args.get('quantity', None)
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
			"price": cart.item.price,
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
    comment = Comment.query.filter_by(item_id = id).order_by(Comment.created_at.desc()).all()
    items_by_price = Item.query.order_by(Item.price.asc()).limit(15)
    items_by_name = Item.query.order_by(Item.name.asc()).limit(15)
    return render_template(
    'item.html', item=item,
    comment=comment,
    items_by_name=items_by_name,
    items_by_price=items_by_price,
    )
def get_recommendations(item_name):
    try:
        # Gửi yêu cầu POST đến model server
        response = requests.post(MODEL_SERVER_URL, json={"query": item_name, "top_item": 10})
        response.raise_for_status()
        return response.json().get("recommendations", [])
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error contacting model server: {e}")
        return []
def get_similar_items(query, limit=15):
    query = normalize_name(query)
    sql = text("""
        SELECT *
        FROM items
        WHERE similarity(name, :query) > 0.3
        ORDER BY similarity(name, :query) DESC
        LIMIT :limit
    """)
    result = db.engine.execute(sql, query=query, limit=limit)
    return [row for row in result]
def normalize_name(name):
    name = name.lower()  # Chuyển về chữ thường
    name = re.sub(r'[^\w\s]', '', name)  # Loại bỏ ký tự đặc biệt
    name = re.sub(r'\s+', ' ', name).strip()  # Xóa khoảng trắng thừa
    return name
@app.route('/payment_success')
def payment_success():
	return render_template('success.html')

@app.route('/payment_failure')
def payment_failure():
	return render_template('failure.html')

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    # Lấy dữ liệu giỏ hàng từ form
    data = json.loads(request.form['price_ids'].replace("'", '"'))

    try:
        # Giả lập thanh toán thành công
        # (Ở đây bạn có thể tích hợp bất kỳ cổng thanh toán nào hoặc mô phỏng quy trình)
        payment_id = str(uuid.uuid4())  # Giả lập Payment ID
        print(f"Payment successful! Payment ID: {payment_id}, User ID: {current_user.id}, Items: {data}")

        # Tạo session giả lập và gọi fulfill_order
        session = {'client_reference_id': current_user.id}
        fulfill_order(session)

        # Chuyển hướng đến trang xác nhận thanh toán thành công
        return redirect(url_for('payment_success'))

    except Exception as e:
        print(f"Payment failed: {e}")
        # Xử lý lỗi khi thanh toán không thành công
        return redirect(url_for('payment_failure'))
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_reset_token(user)
            send_reset_email(user, token)
            flash('An email with instructions to reset your password has been sent.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email not found.', 'danger')
    return render_template('request_password_reset.html', form=form)
def generate_reset_token(user, expires_sec=1800):
    """Tạo một token để xác thực người dùng khi đặt lại mật khẩu"""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(user.email, salt=app.config['SECURITY_PASSWORD_SALT'])

def send_reset_email(user, token):
    """Gửi email với liên kết đặt lại mật khẩu"""
    reset_link = url_for('reset_password', token=token, _external=True)
    msg = Message('Password Reset Request', sender='hoangkhanghcmut@gmail.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{reset_link}

If you did not request this, please ignore this email.
'''
    mail.send(msg)
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = verify_reset_token(token)
    except (SignatureExpired, BadSignature):
        flash('The token is expired or invalid', 'danger')
        return redirect(url_for('reset_password_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(form.password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

def verify_reset_token(token):
    """Xác thực token và lấy lại email người dùng từ token"""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=1800)
    except (SignatureExpired, BadSignature):
        raise Exception('Token expired or invalid')
    return email

@app.route('/item/<int:item_id>/review', methods=['POST'])
@login_required
def submit_review(item_id):
    # Lấy dữ liệu từ form
    rating = request.form.get('rating')  # Có thể là None
    comment = request.form.get('content', '').strip()  # Mặc định là chuỗi rỗng nếu không có
    
    # Tìm Item liên quan
    item = Item.query.get_or_404(item_id)
    category = Category.query.get_or_404(item.category)  # Lấy category liên quan đến item
    
    # Kiểm tra đầu vào
    if not rating and not comment:  # Nếu cả rating và comment đều trống
        flash("Please provide a rating or a comment to submit a review.", "warning")
        return redirect(url_for('item', id=item_id))  # Quay lại trang sản phẩm
    
    # Tạo review
    review = Comment(
        item_id=item_id,
        user_id=current_user.id,
        rating=float(rating) if rating else None,
        content=comment if comment else ''
    )
    
    # Cập nhật rating_count và comment_count của Item
    if rating:
        item.rating_count = (item.rating_count or 0) + 1  # Tăng rating_count
        
        # Lấy tổng các rating hiện tại và thêm rating mới
        total_rating_sum = db.session.query(db.func.sum(Comment.rating)).filter(Comment.item_id == item_id).scalar() or 0
        total_rating_sum += float(rating)

        # Tính trung bình cộng rating cho Item
        item.rating = total_rating_sum / item.rating_count

    item.comment_count = item.comment_count + 1 if item.comment_count else 1  # Tăng comment_count
    
    # Cập nhật rating_count và rating_avg của Category
    if rating:
        # Tính tổng số lượng đánh giá và tổng điểm rating cho category
        total_category_rating_count = db.session.query(db.func.sum(Item.rating_count)).filter(Item.category == category.id).scalar() or 0
        total_category_rating_sum = db.session.query(db.func.sum(Item.rating * Item.rating_count)).filter(Item.category == category.id).scalar() or 0

        # Cập nhật số lượng đánh giá và trung bình đánh giá cho Category
        category.rating_count = total_category_rating_count
        category.rating_avg = total_category_rating_sum / total_category_rating_count if total_category_rating_count > 0 else 0.0

    # Lưu review và cập nhật database
    db.session.add(review)
    db.session.commit()

    flash("Your review has been submitted!", "success")
    return redirect(url_for('item', id=item_id))



# Recommendations functions============================================================================================
# Function to truncate product name
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text

