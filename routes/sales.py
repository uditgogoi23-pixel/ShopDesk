"""
Harry Retail - Sales Routes
POS interface: browse products, manage cart, complete sale
"""

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, session)
from extensions import db
from models import Product, Order, OrderItem, Payment, Customer
from datetime import date

sales_bp = Blueprint('sales', __name__)

PAYMENT_MODES = ['Cash', 'UPI', 'Card', 'Net Banking', 'Cheque']


# ─── POS SCREEN ──────────────────────────────────────────────────────────────
@sales_bp.route('/')
def index():
    categories = db.session.query(Product.category).distinct().order_by(Product.category).all()
    categories = [c[0] for c in categories if c[0]]
    products   = Product.query.filter(Product.stock > 0).order_by(Product.category, Product.product_name).all()
    return render_template(
        'sales/index.html',
        products=products,
        categories=categories,
        payment_modes=PAYMENT_MODES,
    )


# ─── COMPLETE SALE (AJAX) ─────────────────────────────────────────────────────
@sales_bp.route('/complete', methods=['POST'])
def complete_sale():
    data         = request.get_json()
    phone = data.get('customer_phone', '').strip()
    print("DEBUG DATA:", data)
    cart         = data.get('cart', [])           # [{product_id, quantity}, ...]
    payment_mode = data.get('payment_mode', 'Cash')
    customer = None

    if phone:
        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            customer = Customer(
                name=f"Customer-{phone[-4:]}",
                phone=phone
            )
            db.session.add(customer)
            db.session.flush()
        customer_id = customer.customer_id
    else:
        # Use default guest customer (assumed id=1) when no phone provided
        customer_id = 1

    if not cart:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400

    # ── Validate stock & compute total ──────────────────────────────────────
    total       = 0.0
    cart_items  = []

    for item in cart:
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({'success': False,
                            'message': f"Product ID {item['product_id']} not found"}), 404
        qty = int(item['quantity'])
        if product.stock < qty:
            return jsonify({'success': False,
                            'message': f"Insufficient stock for {product.product_name}. "
                                       f"Available: {product.stock}"}), 400
        total += float(product.price) * qty
        cart_items.append({'product': product, 'quantity': qty})

    try:
        # ── 1. Create Order ─────────────────────────────────────────────────
        order = Order(
            customer_id=customer_id,
            order_date=date.today(),
            total_amount=total,
            payment_mode=payment_mode,
            order_status='Completed',
        )
        db.session.add(order)
        db.session.flush()   # get order.order_id before committing

        # ── 2. Create Order Items + Deduct Stock ────────────────────────────
        for entry in cart_items:
            prod = entry['product']
            qty  = entry['quantity']

            order_item = OrderItem(
                order_id   = order.order_id,
                product_id = prod.product_id,
                quantity   = qty,
            )
            db.session.add(order_item)
            prod.stock -= qty           # deduct stock

        # ── 3. Record Payment ───────────────────────────────────────────────
        payment = Payment(
            order_id     = order.order_id,
            payment_mode = payment_mode,
            amount       = total,
            payment_date = date.today(),
        )
        db.session.add(payment)

        db.session.commit()

        return jsonify({
            'success':  True,
            'order_id': order.order_id,
            'total':    total,
            'message':  f'Sale completed! Order #{order.order_id}',
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── ORDER RECEIPT ────────────────────────────────────────────────────────────
@sales_bp.route('/receipt/<int:order_id>')
def receipt(order_id):
    order    = Order.query.get_or_404(order_id)
    payment  = Payment.query.filter_by(order_id=order_id).first()
    items    = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template('sales/receipt.html',
                           order=order, payment=payment, items=items)
