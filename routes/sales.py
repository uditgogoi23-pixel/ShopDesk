"""
ShopDesk — Sales Routes
POS interface: browse products, manage cart, complete sale.

CHANGES (Migration 001):
  - complete_sale now accepts decimal quantity (for weight items)
  - complete_sale saves unit_type per OrderItem
  - Stock deduction uses float arithmetic (supports 0.250 kg)
"""

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify, session)
from extensions import db
from models import Product, Order, OrderItem, Payment, Customer
from datetime import date

sales_bp = Blueprint('sales', __name__)

PAYMENT_MODES = ['Cash', 'UPI', 'Card', 'Net Banking', 'Cheque']


# ─── POS SCREEN ───────────────────────────────────────────────────────────────
@sales_bp.route('/')
def index():
    categories = db.session.query(Product.category).distinct().order_by(Product.category).all()
    categories = [c[0] for c in categories if c[0]]
    products   = (Product.query
                  .filter(Product.stock > 0)
                  .order_by(Product.category, Product.product_name)
                  .all())
    return render_template(
        'sales/index.html',
        products=products,
        categories=categories,
        payment_modes=PAYMENT_MODES,
    )


# ─── CUSTOMER LOOKUP (AJAX) ───────────────────────────────────────────────────
@sales_bp.route('/customer/<phone>')
def get_customer(phone):
    customer = Customer.query.filter_by(phone=phone).first()
    if customer:
        return jsonify({
            'exists':      True,
            'customer_id': customer.customer_id,
            'name':        customer.name,
        })
    return jsonify({'exists': False})


# ─── COMPLETE SALE (AJAX) ─────────────────────────────────────────────────────
@sales_bp.route('/complete', methods=['POST'])
def complete_sale():
    data             = request.get_json()
    discount_percent = float(data.get('discount', 0))
    phone            = data.get('customer_phone', '').strip()
    customer_name    = data.get('customer_name', '').strip()
    cart             = data.get('cart', [])   # [{product_id, quantity, unit_type}, ...]
    payment_mode     = data.get('payment_mode', 'Cash')

    # ── Resolve customer ──────────────────────────────────────────────────────
    customer_id = None   # default walk-in
    if phone:
        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            customer = Customer(
                name=customer_name or f"Customer-{phone[-4:]}",
                phone=phone,
            )
            db.session.add(customer)
            db.session.flush()
        customer_id = customer.customer_id

    if not cart:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400

    # ── Validate stock & compute total ────────────────────────────────────────
    total      = 0.0
    cart_items = []

    for item in cart:
        product = Product.query.get(item['product_id'])
        if not product:
            return jsonify({
                'success': False,
                'message': f"Product ID {item['product_id']} not found"
            }), 404

        # Accept decimal quantity from the modal (e.g. 0.250 kg)
        qty       = float(item['quantity'])
        unit_type = item.get('unit_type', product.unit_type)

        if float(product.stock) < qty:
            return jsonify({
                'success': False,
                'message': (f"Insufficient stock for {product.product_name}. "
                            f"Available: {float(product.stock)} {product.unit_type}"),
            }), 400

        total += float(product.price) * qty
        cart_items.append({'product': product, 'quantity': qty, 'unit_type': unit_type})

    discount      = round(total * (discount_percent / 100), 2)
    taxable_amount = total - discount
    gst_amount    = round(taxable_amount * 0.18, 2)
    grand_total   = taxable_amount + gst_amount

    try:
        # ── 1. Create Order ───────────────────────────────────────────────────
        order = Order(
            customer_id  = customer_id,
            invoice_no   = "TEMP",
            order_date   = date.today(),
            total_amount = total,
            discount     = discount,
            gst_amount   = gst_amount,
            grand_total  = grand_total,
            payment_mode = payment_mode,
            order_status = 'Completed',
        )
        db.session.add(order)
        db.session.flush()   # get order_id
        order.invoice_no = f"INV-{order.order_id:05d}"

        # ── 2. Create Order Items + Deduct Stock ──────────────────────────────
        for entry in cart_items:
            prod      = entry['product']
            qty       = entry['quantity']
            unit_type = entry['unit_type']

            order_item = OrderItem(
            order_id=order.order_id,
            product_id=prod.product_id,
            quantity=qty,
            unit_type=unit_type,

            unit_price=prod.price,
            subtotal=float(qty) * float(prod.price),

            selling_price=prod.price,
            cost_price=prod.cost_price
        )
            
            db.session.add(order_item)
            prod.stock = float(prod.stock) - qty   # float arithmetic for decimals

        # ── 3. Record Payment ─────────────────────────────────────────────────
        payment = Payment(
            order_id     = order.order_id,
            payment_mode = payment_mode,
            amount       = grand_total,
            payment_date = date.today(),
        )
        db.session.add(payment)
        db.session.commit()

        return jsonify({
            'success':  True,
            'order_id': order.order_id,
            'total':    grand_total,
            'message':  f'Sale completed! Invoice {order.invoice_no}',
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ─── ORDER RECEIPT ────────────────────────────────────────────────────────────
@sales_bp.route('/receipt/<int:order_id>')
def receipt(order_id):
    order   = Order.query.get_or_404(order_id)
    payment = Payment.query.filter_by(order_id=order_id).first()
    items   = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template('sales/receipt.html',
                           order=order, payment=payment, items=items)
