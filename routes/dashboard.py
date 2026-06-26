"""
Harry Retail - Dashboard Routes
KPI cards: today's revenue, orders, stock alerts, top sellers, monthly trend
"""

from flask import Blueprint, render_template, jsonify
from extensions import db
from models import Order, OrderItem, Payment, Product, StockEntry
from sqlalchemy import func, desc, text
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


def _get_kpis():
    today        = date.today()
    month_start  = today.replace(day=1)
    last_month_s = (month_start - timedelta(days=1)).replace(day=1)
    last_month_e = month_start - timedelta(days=1)

 # ── Today's Revenue ─────────────────────────────────────────────

    today_rev = (
    db.session.query(
        func.coalesce(
            func.sum(OrderItem.selling_price * OrderItem.quantity),
            0
        )
    )
    .join(Order, Order.order_id == OrderItem.order_id)
    .filter(Order.order_date == today)
    .scalar()
)

    # ── Today's Profit ──────────────────────────────────────────────

    today_profit = (
        db.session.query(
            func.coalesce(
                func.sum(
                    OrderItem.quantity *
                    (OrderItem.selling_price - OrderItem.cost_price)
                ),
                0
            )
        )
        .join(Order, Order.order_id == OrderItem.order_id)
        .filter(Order.order_date == today)
        .scalar()
    )

    # ── Today's Orders ──────────────────────────────────────────────

    today_orders = (
        Order.query
        .filter(Order.order_date == today)
        .count()
    )

    # ── This Month Revenue ──────────────────────────────────────────

    month_rev = (
    db.session.query(
        func.coalesce(
            func.sum(OrderItem.selling_price * OrderItem.quantity),
            0
        )
    )
    .join(Order, Order.order_id == OrderItem.order_id)
    .filter(Order.order_date >= month_start)
    .scalar()
)

    # ── This Month Profit ───────────────────────────────────────────

    month_profit = (
        db.session.query(
            func.coalesce(
                func.sum(
                    OrderItem.quantity *
                    (OrderItem.selling_price - OrderItem.cost_price)
                ),
                0
            )
        )
        .join(Order, Order.order_id == OrderItem.order_id)
        .filter(Order.order_date >= month_start)
        .scalar()
    )

    # ── Last Month Revenue ──────────────────────────────────────────

    last_rev = (
    db.session.query(
        func.coalesce(
            func.sum(OrderItem.selling_price * OrderItem.quantity),
            0
        )
    )
    .join(Order, Order.order_id == OrderItem.order_id)
    .filter(Order.order_date.between(last_month_s, last_month_e))
    .scalar()
)
    margin_percent = 0 
    revenue_growth = 0

    if float(month_rev) > 0:
        margin_percent = round(
            (float(month_profit) / float(month_rev)) * 100,
            1
        )

    if float(last_rev) > 0:
        revenue_growth = round(((float(month_rev) - float(last_rev)) / float(last_rev)) * 100, 1)

    # ── Total Products ───────────────────────────────────────────────────────
    total_products = Product.query.count()

    # ── Low Stock Products ────────────────────────────────────────────────────
    low_stock = sorted(
                [p for p in Product.query.all() if p.is_low_stock],
                key=lambda p: float(p.stock)
            )

    # ── Inventory Value ───────────────────────────────────────────────────────
    inv_value = (db.session.query(
                     func.coalesce(func.sum(Product.price * Product.stock), 0))
                 .scalar())
    purchase_value = (
    db.session.query(
        func.coalesce(
            func.sum(
                StockEntry.quantity_added * StockEntry.purchase_price
            ),
            0
        )
    ).scalar()
)
    # ── Top Selling Products (last 30 days) ───────────────────────────────────
    thirty_ago = today - timedelta(days=30)
    top_products = (
        db.session.query(
            Product.product_name,
            Product.category,
            func.sum(OrderItem.quantity).label('units_sold'),
            func.sum(OrderItem.quantity * OrderItem.selling_price).label('revenue'),
        )
        .join(OrderItem, Product.product_id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .filter(Order.order_date >= thirty_ago)
        .group_by(Product.product_id)
        .order_by(desc('units_sold'))
        .limit(5)
        .all()
    )

    # ── Monthly Revenue Trend (last 6 months) ─────────────────────────────────
    # REPLACE the monthly_trend query with this:
    monthly_trend = [
        {
            'month': r.month,
            'revenue': float(r.revenue)
        }
        for r in (
            db.session.query(
                func.date_format(Payment.payment_date, '%Y-%m').label('month'),
                func.sum(Payment.amount).label('revenue'),
            )
            .filter(Payment.payment_date >= today - timedelta(days=180))
            .group_by(func.date_format(Payment.payment_date, '%Y-%m'))
            .order_by(func.date_format(Payment.payment_date, '%Y-%m'))
            .all()
        )
    ]
    # ── Recent Orders ─────────────────────────────────────────────────────────
    recent_orders = (Order.query
                     .order_by(desc(Order.order_id))
                     .limit(8)
                     .all())

    recent_orders = (
        Order.query
        .order_by(desc(Order.order_id))
        .limit(8)
        .all()
    )
    print("Today:", today)
    print("Month Start:", month_start)
    print("Today's Revenue:", today_rev)
    print("Monthly Revenue:", month_rev)
    return {
        'today_rev': float(today_rev),
        'today_profit': float(today_profit),
        'today_orders': today_orders,
        'month_rev': float(month_rev),
        'month_profit': float(month_profit),
        'margin_percent': margin_percent,
        'revenue_growth': revenue_growth,
        'total_products': total_products,
        'low_stock': low_stock,
        'inv_value': float(inv_value),
        'purchase_value': float(purchase_value),
        'top_products': top_products,
        'monthly_trend': monthly_trend,
        'recent_orders': recent_orders,
    }


@dashboard_bp.route('/')
def index():
    kpis = _get_kpis()
    return render_template('dashboard/index.html', **kpis)


# ─── API: chart data ─────────────────────────────────────────────────────────
@dashboard_bp.route('/api/trend')
def api_trend():
    kpis = _get_kpis()
    trend = kpis['monthly_trend']
    return jsonify(trend)
