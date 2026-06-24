"""
Harry Retail - Database Models
SQLAlchemy ORM models matching the retail schema
"""

from extensions import db
from datetime import date, datetime


class Customer(db.Model):
    __tablename__ = 'customers'

    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    email       = db.Column(db.String(150), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)

    def to_dict(self):
        return {
            'customer_id': self.customer_id,
            'name':        self.name,
            'phone': self.phone,
            'email':       self.email,
            'created_at': str(self.created_at),
        }


class Product(db.Model):
    __tablename__ = 'products'

    product_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)
    category     = db.Column(db.String(50),  nullable=True)
    price        = db.Column(db.Numeric(10, 2), nullable=False)
    stock        = db.Column(db.Integer, default=0)

    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def to_dict(self):
        return {
            'product_id':   self.product_id,
            'product_name': self.product_name,
            'category':     self.category,
            'price':        float(self.price),
            'stock':        self.stock,
        }


class Order(db.Model):
    __tablename__ = 'orders'

    order_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_no = db.Column(db.String(20), unique=True)
    customer_id  = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=True)
    order_date   = db.Column(db.Date, default=date.today)
    total_amount = db.Column(db.Numeric(10, 2), nullable=True)
    discount = db.Column(db.Numeric(10,2), default=0)
    gst_amount = db.Column(db.Numeric(10,2), default=0)
    grand_total = db.Column(db.Numeric(10,2), default=0)
    payment_mode = db.Column(db.String(30), nullable=True)
    order_status = db.Column(db.String(30), default='Completed')

    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    payments    = db.relationship('Payment', backref='order', lazy=True)

    @property
    def calculated_total(self):
        return sum(
             float(item.product.price) * item.quantity
             for item in self.order_items
             if item.product
    )

    def to_dict(self):
        return {
            'order_id':     self.order_id,
            'customer_id':  self.customer_id,
            'order_date':   str(self.order_date),
            'order_status': self.order_status,
            'total_amount': self.calculated_total,
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id      = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_id    = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity      = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self):
        return {
            'order_item_id': self.order_item_id,
            'order_id':      self.order_id,
            'product_id':    self.product_id,
            'quantity':      self.quantity,
        }


class Payment(db.Model):
    __tablename__ = 'payments'

    payment_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id     = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    payment_mode = db.Column(db.String(30), default='Cash')
    amount       = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.Date, default=date.today)

    def to_dict(self):
        return {
            'payment_id':   self.payment_id,
            'order_id':     self.order_id,
            'payment_mode': self.payment_mode,
            'amount':       float(self.amount),
            'payment_date': str(self.payment_date),
        }
class StockEntry(db.Model):
    __tablename__ = 'stock_entries'

    entry_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)

    quantity_added = db.Column(db.Integer, nullable=False)
    previous_stock = db.Column(db.Integer, nullable=False)
    new_stock = db.Column(db.Integer, nullable=False)

    remarks = db.Column(db.String(255), nullable=True)

    entry_date = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'entry_id': self.entry_id,
            'product_id': self.product_id,
            'quantity_added': self.quantity_added,
            'previous_stock': self.previous_stock,
            'new_stock': self.new_stock,
            'remarks': self.remarks,
            'entry_date': str(self.entry_date)
        }