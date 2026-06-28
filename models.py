"""
ShopDesk — Database Models
SQLAlchemy ORM models matching the retail schema.

CHANGES in this version (Migration 001):
  Product     — added unit_type, cost_price, reorder_level
  OrderItem   — quantity changed from Integer → Numeric(10,3) for weight support
                added unit_type (snapshot of unit at time of sale)

BUG FIXES:
  - unit_price is now non-nullable with default 0.00 (prevents TypeError in calculated_total)
  - Order.calculated_total safely handles None values
  - Order.to_dict() uses stored total_amount with calculated_total as fallback
  - All datetime defaults changed to utcnow for consistency
  - is_low_stock uses per-product reorder_level (correct single source of truth)
"""

from extensions import db
from datetime import date, datetime


# ── UNIT TYPES supported by the POS quantity modal ───────────────────────────
UNIT_TYPES = ['Units', 'kg', 'g', 'litre', 'ml', 'pack', 'dozen', 'piece']


class Customer(db.Model):
    __tablename__ = 'customers'

    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(100), nullable=False)
    phone       = db.Column(db.String(20), unique=True, nullable=True)
    email       = db.Column(db.String(150), unique=True, nullable=True)
    city        = db.Column(db.String(50), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)  # Fixed: utcnow

    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)

    def to_dict(self):
        return {
            'customer_id': self.customer_id,
            'name':        self.name,
            'phone':       self.phone,
            'email':       self.email,
            'city':        self.city,
            'created_at':  str(self.created_at),
        }


class Product(db.Model):
    __tablename__ = 'products'

    product_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(100), nullable=False)
    category     = db.Column(db.String(50), nullable=True)
    price        = db.Column(db.Numeric(10, 2), nullable=False)
    stock        = db.Column(db.Numeric(10, 3), default=0)  # Decimal for weight stock

    # ── NEW columns (Migration 001) ───────────────────────────────────────────
    unit_type      = db.Column(db.String(20), nullable=False, default='Units',
                               comment='Units | kg | g | litre | ml | pack')
    cost_price     = db.Column(db.Numeric(10, 2), nullable=False, default=0.00,
                               comment='Purchase price — used for profit calculation')
    discount_type  = db.Column(db.String(10), default='none')
    discount_value = db.Column(db.Numeric(10, 2), default=0)
    reorder_level  = db.Column(db.Integer, nullable=False, default=10,
                               comment='Low-stock alert threshold (per product)')
    image          = db.Column(db.String(255), default='default_product.png')

    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    @property
    def is_low_stock(self):
        """True when stock is at or below the per-product reorder threshold."""
        return float(self.stock) <= float(self.reorder_level)

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
        if self.unit_type == 'kg':
            return ['250g', '500g', '1kg', '2kg', '5kg']
        elif self.unit_type == 'litre':
            return ['250ml', '500ml', '1L', '2L', '5L']
        else:
            return ['1', '2', '5', '10']

    def to_dict(self):
        return {
            'product_id':   self.product_id,
            'product_name': self.product_name,
            'category':     self.category,
            'price':        float(self.price),
            'stock':        float(self.stock),
            'unit_type':    self.unit_type,
            'cost_price':   float(self.cost_price),
            'reorder_level': self.reorder_level,
            'is_low_stock': self.is_low_stock,
            'image':        self.image,
        }


class Order(db.Model):
    __tablename__ = 'orders'

    order_id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_no   = db.Column(db.String(20), unique=True, nullable=True)
    customer_id  = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=True)
    order_date   = db.Column(db.Date, default=date.today)
    total_amount = db.Column(db.Numeric(10, 2), nullable=True)
    discount_type = db.Column(db.String(20), default="none")
    discount_value = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    gst_amount   = db.Column(db.Numeric(10, 2), default=0)
    grand_total  = db.Column(db.Numeric(10, 2), default=0)
    payment_mode = db.Column(db.String(30), nullable=True)
    order_status = db.Column(db.String(30), default='Completed')

    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    payments    = db.relationship('Payment', backref='order', lazy=True)

    @property
    def calculated_total(self):
        """
        Recomputes total from order items.
        Fixed: safely skips items where unit_price is None.
        """
        return sum(
            float(item.unit_price or 0) * float(item.quantity or 0)
            for item in self.order_items
        )

    def to_dict(self):
        # Use stored total_amount if available; fall back to calculated
        stored = float(self.total_amount) if self.total_amount is not None else None
        return {
            'order_id':     self.order_id,
            'invoice_no':   self.invoice_no,
            'customer_id':  self.customer_id,
            'order_date':   str(self.order_date),
            'order_status': self.order_status,
            'total_amount': stored if stored is not None else self.calculated_total,
            'grand_total':  float(self.grand_total) if self.grand_total else 0,
            'payment_mode': self.payment_mode,
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id      = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    product_id    = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)

    # ── CHANGED: Integer → Numeric(10,3) to support 0.250 kg, 1.500 litre ───
    quantity  = db.Column(db.Numeric(10, 3), nullable=False, default=1.000)

    # ── NEW: unit label snapshot at time of sale ──────────────────────────────
    unit_type = db.Column(db.String(20), nullable=False, default='Units')

    selling_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    cost_price    = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # Fixed: non-nullable with default 0.00 — prevents TypeError in calculated_total
    unit_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    subtotal   = db.Column(db.Numeric(10, 2), nullable=True)

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
            'unit_price':    float(self.unit_price),
            'subtotal':      float(self.subtotal) if self.subtotal else 0,
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
    product        = db.relationship('Product')
    quantity_added = db.Column(db.Numeric(10, 3), nullable=False)
    previous_stock = db.Column(db.Numeric(10, 3), nullable=False)
    new_stock      = db.Column(db.Numeric(10, 3), nullable=False)
    remarks        = db.Column(db.String(255), nullable=True)
    supplier_name  = db.Column(db.String(100), nullable=True)
    invoice_no     = db.Column(db.String(50), nullable=True)
    purchase_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    gst_percent    = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    gst_amount     = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    invoice_total  = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    gst_claimed    = db.Column(db.Boolean, nullable=False, default=False)
    entry_date     = db.Column(db.DateTime, default=datetime.utcnow)  # Fixed: utcnow

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

    id            = db.Column(db.Integer, primary_key=True)
    shop_name     = db.Column(db.String(120), nullable=False, default='ShopDesk')
    owner_name    = db.Column(db.String(120))
    phone         = db.Column(db.String(20))
    email         = db.Column(db.String(120))
    address       = db.Column(db.Text)
    business_type = db.Column(db.String(20), nullable=False, default='Retail')

    # GST
    gst_enabled           = db.Column(db.Boolean, nullable=False, default=False)
    gst_mode              = db.Column(db.String(20), nullable=False, default='Inclusive')
    gst_number            = db.Column(db.String(30))
    default_gst_rate      = db.Column(db.Numeric(5, 2), nullable=False, default=18.00)
    gst_registration_type = db.Column(db.String(20), nullable=False, default='Regular')

    currency   = db.Column(db.String(10), nullable=False, default='INR')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)   # Fixed: utcnow
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,   # Fixed: utcnow
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return '<BusinessSettings>'


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    supplier_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supplier_name = db.Column(db.String(120), nullable=False)
    phone         = db.Column(db.String(20))
    email         = db.Column(db.String(120))
    gst_number    = db.Column(db.String(30))
    address       = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)  # Fixed: utcnow

    def __repr__(self):
        return f'<Supplier {self.supplier_name}>'