"""
Harry Retail - Orders Routes
View order history, individual order details, filter by date/status
"""

from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models import Order, OrderItem, Payment, Product
from sqlalchemy import desc, func
from datetime import date, timedelta

orders_bp = Blueprint('orders', __name__)


# ─── ORDER HISTORY ────────────────────────────────────────────────────────────
@orders_bp.route('/')
def index():
    page   = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    period = request.args.get('period', 'all')

    query  = Order.query

    if status:
        query = query.filter(Order.order_status == status)

    if period == 'today':
        query = query.filter(Order.order_date == date.today())
    elif period == 'week':
        query = query.filter(Order.order_date >= date.today() - timedelta(days=7))
    elif period == 'month':
        query = query.filter(Order.order_date >= date.today() - timedelta(days=30))

    pagination = query.order_by(desc(Order.order_date), desc(Order.order_id)).paginate(
        page=page, per_page=20, error_out=False
    )
    orders = pagination.items

    # Attach totals (computed via relationship)
    return render_template(
        'orders/index.html',
        orders=orders,
        pagination=pagination,
        status=status,
        period=period,
    )


# ─── ORDER DETAIL ─────────────────────────────────────────────────────────────
@orders_bp.route('/<int:order_id>')
def detail(order_id):
    order   = Order.query.get_or_404(order_id)
    payment = Payment.query.filter_by(order_id=order_id).first()
    items   = (
        db.session.query(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.product_id)
        .filter(OrderItem.order_id == order_id)
        .all()
    )
    return render_template('orders/detail.html',
                           order=order, payment=payment, items=items)


# ─── API: RECENT ORDERS ───────────────────────────────────────────────────────
@orders_bp.route('/api/recent')
def api_recent():
    orders = (Order.query
              .order_by(desc(Order.order_id))
              .limit(10)
              .all())
    return jsonify([o.to_dict() for o in orders])
