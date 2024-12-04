from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
import datetime
db = SQLAlchemy()
class User(UserMixin,db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True,autoincrement = True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    password = db.Column(db.String(250), nullable=True)
    admin = db.Column(db.Boolean, nullable=True, default=False)
    email_confirmed = db.Column(db.Boolean, nullable=True, default=False)
    cart = db.relationship('Cart', backref='buyer')
    orders = db.relationship("Order", backref='customer')
    
    def add_to_cart(self, itemid, quantity):
        max_id = db.session.query(db.func.max(Cart.id)).scalar()
        new_id = max_id + 1 if max_id is not None else 1
        item_to_add = Cart(id=new_id,itemid=itemid, uid=self.id, quantity=quantity)
        db.session.add(item_to_add)
        db.session.commit()

    def remove_from_cart(self, itemid, quantity):
        item_to_remove = Cart.query.filter_by(itemid=itemid, uid=self.id, quantity=quantity).first()
        db.session.delete(item_to_remove)
        db.session.commit()
    def get_id(self):
         return super().get_id()

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(250), nullable=True)
    details = db.Column(db.String(250), nullable=True)
    rating = db.Column(db.Float,nullable = True)
    rating_count = db.Column(db.Integer,nullable = True)
    comment_count = db.Column(db.Integer,nullable = True)
    discount = db.Column(db.Float,nullable = True)
    comments = relationship('Comment', back_populates='item')
    price_id = db.Column(db.String(250), nullable=True)
    orders = db.relationship("Ordered_item", backref="item")
    in_cart = db.relationship("Cart", backref="item")
    
    def ins_comment_count():
        pass
    def ins_rating_count():
        pass
    
 

class Cart(db.Model):
	__tablename__ = "cart"
	id = db.Column(db.Integer, primary_key=True,autoincrement=True)
	uid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	itemid = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
	quantity = db.Column(db.Integer, nullable=False, default=1)

class Order(db.Model):
	__tablename__ = "orders"
	id = db.Column(db.Integer, primary_key=True,autoincrement = True)
	uid = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
	date = db.Column(db.DateTime, nullable=False)
	status = db.Column(db.String(50), nullable=False)
	items = db.relationship("Ordered_item", backref="order")

class Ordered_item(db.Model):
	__tablename__ = "ordered_items"
	id = db.Column(db.Integer, primary_key=True,autoincrement= True)
	oid = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
	itemid = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
	quantity = db.Column(db.Integer, db.ForeignKey('cart.quantity'), nullable=False)
  
class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer,primary_key = True,autoincrement=True)
    content = db.Column(db.Text, nullable = True)
    created_at = db.Column(db.DateTime,default = datetime.datetime.now(),nullable=True)
    rating = db.Column(db.Integer,default = 0, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    item = relationship('Item', back_populates='comments')
    def __repr__(self):
        return f"<Comment {self.content[:20]} by User {self.user_id}>"
    
