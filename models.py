"""
ShopDesk — Database Models
SQLAlchemy ORM models matching the retail schema.

CHANGES in this version (Migration 001):
  Product   — added unit_type, cost_price, reorder_level
  OrderItem — quantity changed from Integer → Numeric(10,3) for weight support
              added unit_type (snapshot of unit at time of sale)
"""

from extensions import db
from datetime import date, datetime


class Customer(db.Model):
    __tablename__ = 'customers'

    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(100), nullable=False)
    phone       = db.Column(db.String(10), unique=True, nullable=False)
    email       = db.Column(db.String(150), unique=True, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)

    def to_dict(self):
        return {
            'customer_id': self.customer_id,
            'name':        self.name,
            'phone':       self.phone,
            'email':       self.email,
            'created_at':  str(self.created_at),
        }


# ── UNIT TYPES supported by the POS quantity modal ───────────────────────────
UNIT_TYPES = ['Units', 'kg', 'g', 'litre', 'ml', 'pack', 'dozen', 'piece']


class Product(db.Model):
    __tablename__ = 'products'

    product_id    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name  = db.Column(db.String(100), nullable=False)
    category      = db.Column(db.String(50),  nullable=True)
    price         = db.Column(db.Numeric(10, 2), nullable=False)
    stock         = db.Column(db.Numeric(10, 3), default=0)  # Decimal for weight stock

    # ── NEW columns (Migration 001) ───────────────────────────────────────────
    unit_type     = db.Column(db.String(20),   nullable=False, default='Units',
                              comment='Units | kg | g | litre | ml | pack')
    cost_price    = db.Column(db.Numeric(10, 2), nullable=False, default=0.00,
                              comment='Purchase price — used for profit calculation')
    discount_type = db.Column(db.String(10), default='none')
    discount_value = db.Column(db.Numeric(10, 2), default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10,
                          comment='Low-stock alert threshold')

    image = db.Column(db.String(255), default="default_product.png")
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.supplier_id"),
        nullable=True
    )
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    @property
    def is_low_stock(self):
        """True when stock is at or below the per-product reorder threshold."""
        return float(self.stock) <= self.reorder_level

    @property
    def margin_percent(self):
        """Gross margin % — requires cost_price to be set."""
        if not self.cost_price or float(self.cost_price) == 0:
            return None
        return round(
            (float(self.price) - float(self.cost_price)) / float(self.price) * 100, 1
        )
    @property
    def quantity_options(self):

        if self.unit_type == "kg":
            return ["250g", "500g", "1kg", "2kg", "5kg"]

        elif self.unit_type == "litre":
            return ["250ml", "500ml", "1L", "2L", "5L"]

        else:
            return ["1", "2", "5", "10"]
    def to_dict(self):
        return {
            'product_id':    self.product_id,
            'product_name':  self.product_name,
            'category':      self.category,
            'price':         float(self.price),
            'stock':         float(self.stock),
            'unit_type':     self.unit_type,
            'cost_price':    float(self.cost_price),
            'reorder_level': self.reorder_level,
            'is_low_stock':  self.is_low_stock,
        }


class Order(db.Model):
    __tablename__ = 'orders'

    order_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_no   = db.Column(db.String(20), unique=True)
    customer_id  = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=True)
    order_date   = db.Column(db.Date, default=date.today)
    total_amount = db.Column(db.Numeric(10, 2), nullable=True)
    discount     = db.Column(db.Numeric(10, 2), default=0)
    gst_amount   = db.Column(db.Numeric(10, 2), default=0)
    grand_total  = db.Column(db.Numeric(10, 2), default=0)
    payment_mode = db.Column(db.String(30), nullable=True)
    order_status = db.Column(db.String(30), default='Completed')

    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    payments    = db.relationship('Payment',   backref='order', lazy=True)

    @property
    def calculated_total(self):
        return sum(
            float(item.unit_price) * float(item.quantity)
            for item in self.order_items
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

    # ── CHANGED: Integer → Numeric(10,3) to support 0.250 kg, 1.500 litre ───
    quantity      = db.Column(db.Numeric(10, 3), nullable=False, default=1.000)

    # ── NEW: unit label snapshot at time of sale ──────────────────────────────
    unit_type     = db.Column(db.String(20), nullable=False, default='Units')
    selling_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    cost_price    = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    unit_price = db.Column(db.Numeric(10, 2))
    subtotal = db.Column(db.Numeric(10, 2))

    @property
    def quantity_display(self):
        """Human-readable quantity: '2' for integers, '0.250' for fractions."""
        qty = float(self.quantity)
        if qty == int(qty):
            return str(int(qty))
        return f"{qty:.3f}".rstrip('0')
    
    @property
    def revenue(self):
         return float(self.quantity) * float(self.selling_price)
    @property
    def cost(self):
        return float(self.quantity) * float(self.cost_price)

    

    @property
    def profit(self):
        return self.revenue - self.cost

    @property
    def margin_percent(self):
        if self.revenue == 0:
            return 0
        return round((self.profit / self.revenue) * 100, 1)

    def to_dict(self):
        return {
            'order_item_id': self.order_item_id,
            'order_id':      self.order_id,
            'product_id':    self.product_id,
            'quantity':      float(self.quantity),
            'unit_type':     self.unit_type,
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

    entry_id       = db.Column(db.Integer, primary_key=True, autoincrement=True)

    product_id     = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    product = db.relationship('Product')
    quantity_added = db.Column(db.Numeric(10, 3), nullable=False)   # Decimal for weight
    previous_stock = db.Column(db.Numeric(10, 3), nullable=False)
    new_stock      = db.Column(db.Numeric(10, 3), nullable=False)
    remarks        = db.Column(db.String(255), nullable=True)
    supplier_name = db.Column(db.String(100), nullable=True)

    invoice_no = db.Column(db.String(50), nullable=True)

    purchase_price = db.Column(
    db.Numeric(10, 2),
    nullable=False,
    default=0
    )
    gst_percent = db.Column(
    db.Numeric(5,2),
    nullable=False,
    default=0
    )

    gst_amount = db.Column(
    db.Numeric(10,2),
    nullable=False,
    default=0
    )

    invoice_total = db.Column(
    db.Numeric(10,2),
    nullable=False,
    default=0
    )

    gst_claimed = db.Column(
    db.Boolean,
    nullable=False,
    default=False
    )
    entry_date     = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'entry_id':       self.entry_id,
            'product_id':     self.product_id,
            'quantity_added': float(self.quantity_added),
            'previous_stock': float(self.previous_stock),
            'new_stock':      float(self.new_stock),
            'remarks':        self.remarks,
            'entry_date':     str(self.entry_date),
        }
class BusinessSettings(db.Model):
    __tablename__ = 'business_settings'

    id = db.Column(db.Integer, primary_key=True)

    # Business Info
    shop_name = db.Column(db.String(120), nullable=False, default="ShopDesk")
    owner_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)

    # Business Type
    business_type = db.Column(
        db.String(20),
        nullable=False,
        default="Retail"
    )

    # GST
    gst_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    gst_mode = db.Column(
        db.String(20),
        nullable=False,
        default="Inclusive"
    )

    gst_number = db.Column(db.String(30))
    default_gst_rate = db.Column(
    db.Numeric(5,2),
    nullable=False,
    default=18.00
    )
    gst_registration_type = db.Column(
    db.String(20),
    nullable=False,
    default="Regular"
    )
    currency = db.Column(
        db.String(10),
        nullable=False,
        default="INR"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.now
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )
    
    def __repr__(self):
        return "<BusinessSettings>"

class Supplier(db.Model):
    __tablename__ = "suppliers"

    supplier_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supplier_name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    gst_number = db.Column(db.String(30))
    address = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.now
    )

    products = db.relationship(
        "Product",
        backref="supplier",
        lazy=True
    )

    def __repr__(self):
        return f"<Supplier {self.supplier_name}>"
    
class PurchaseHistory(db.Model):
        __tablename__ = "purchase_history"

        purchase_id = db.Column(db.Integer, primary_key=True)

        purchase_date = db.Column(db.DateTime, nullable=False)

        supplier_id = db.Column(
            db.Integer,
            db.ForeignKey("suppliers.supplier_id"),
            nullable=True
        )

        product_id = db.Column(
            db.Integer,
            db.ForeignKey("products.product_id"),
            nullable=False
        )

        invoice_no = db.Column(db.String(50))

        quantity = db.Column(db.Numeric(10,2), nullable=False)

        purchase_price = db.Column(db.Numeric(10,2), nullable=False)

        gst_percent = db.Column(db.Numeric(5,2), default=0)

        gst_amount = db.Column(db.Numeric(10,2), default=0)

        total_amount = db.Column(db.Numeric(10,2), nullable=False)

        payment_status = db.Column(
            db.String(20),
            default="Paid"
        )

        payment_method = db.Column(
            db.String(30),
            default="Cash"
        )

        due_date = db.Column(db.Date)

        remarks = db.Column(db.Text)

        created_at = db.Column(
            db.DateTime,
            default=datetime.now
        )

        supplier = db.relationship(
            "Supplier",
            backref="purchases"
        )

        product = db.relationship("Product", backref="purchase_history")