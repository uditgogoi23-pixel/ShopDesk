"""
Harry Retail - Analytics Routes
Business insights: top sellers, dead stock, revenue by category,
order value trends, inventory turnover, low stock alerts
"""

from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models import Order, OrderItem, Payment, Product
from sqlalchemy import func, desc, asc, text, not_, exists
from datetime import date, timedelta

analytics_bp = Blueprint('analytics', __name__)


def _top_selling(limit=10, days=30):
    since = date.today() - timedelta(days=days)
    return (
        db.session.query(
            Product.product_id,
            Product.product_name,
            Product.category,
            Product.price,
            Product.stock,
            func.sum(OrderItem.quantity).label('units_sold'),
            func.sum(OrderItem.quantity * Product.price).label('revenue'),
        )
        .join(OrderItem, Product.product_id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .filter(Order.order_date >= since)
        .group_by(Product.product_id)
        .order_by(desc('units_sold'))
        .limit(limit)
        .all()
    )


def _dead_stock(days=30):
    since = date.today() - timedelta(days=days)

    # Products with NO order items in the period
    sold_ids = (
        db.session.query(OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .filter(Order.order_date >= since)
        .subquery()
    )
    return (
        Product.query
        .filter(~Product.product_id.in_(sold_ids))
        .filter(Product.stock > 0)
        .order_by(Product.category, Product.product_name)
        .all()
    )


def _revenue_by_category(days=30):
    since = date.today() - timedelta(days=days)
    return (
        db.session.query(
            Product.category,
            func.sum(OrderItem.quantity * Product.price).label('revenue'),
            func.sum(OrderItem.quantity).label('units_sold'),
            func.count(func.distinct(Order.order_id)).label('orders'),
        )
        .join(OrderItem, Product.product_id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.order_id)
        .filter(Order.order_date >= since)
        .group_by(Product.category)
        .order_by(desc('revenue'))
        .all()
    )


def _avg_order_value(days=30):
    since = date.today() - timedelta(days=days)
    result = (
        db.session.query(
            func.count(func.distinct(Payment.order_id)).label('orders'),
            func.sum(Payment.amount).label('total'),
            func.avg(Payment.amount).label('avg'),
        )
        .join(Order, Payment.order_id == Order.order_id)
        .filter(Order.order_date >= since)
        .first()
    )
    return result


def _monthly_growth():
    rows = (
        db.session.query(
            func.date_format(Payment.payment_date, '%Y-%m').label('month'),
            func.sum(Payment.amount).label('revenue'),
            func.count(func.distinct(Payment.order_id)).label('orders'),
        )
        .filter(Payment.payment_date >= date.today() - timedelta(days=365))
        .group_by('month')
        .order_by('month')
        .all()
    )
    # Compute month-on-month growth %
    result = []
    for i, row in enumerate(rows):
        growth = 0
        if i > 0 and float(rows[i - 1].revenue) > 0:
            growth = round(
                ((float(row.revenue) - float(rows[i - 1].revenue)) / float(rows[i - 1].revenue)) * 100, 1
            )
        result.append({
            'month':   row.month,
            'revenue': float(row.revenue),
            'orders':  row.orders,
            'growth':  growth,
        })
    return result


def _low_stock_alerts():
    return (Product.query
            .filter(Product.stock <= Product.reorder_level)
            .order_by(asc(Product.stock))
            .all())


def _inventory_turnover(days=30):
    """Units sold / avg stock over period — higher = faster moving."""
    since = date.today() - timedelta(days=days)
    rows = (
        db.session.query(
            Product.product_id,
            Product.product_name,
            Product.category,
            Product.stock,
            Product.price,
            func.coalesce(func.sum(OrderItem.quantity), 0).label('units_sold'),
        )
        .outerjoin(OrderItem, Product.product_id == OrderItem.product_id)
        .outerjoin(Order, (OrderItem.order_id == Order.order_id) & (Order.order_date >= since))
        .group_by(Product.product_id)
        .order_by(desc('units_sold'))
        .all()
    )
    result = []
    for r in rows:
        avg_stock = r.stock + (r.units_sold / 2)
        turnover  = round(r.units_sold / avg_stock, 2) if avg_stock > 0 else 0
        result.append({
            'product_id':   r.product_id,
            'product_name': r.product_name,
            'category':     r.category,
            'stock':        r.stock,
            'price':        float(r.price),
            'units_sold':   r.units_sold,
            'turnover':     turnover,
        })
    result.sort(key=lambda x: x['turnover'], reverse=True)
    return result[:20]


# ─── MAIN ANALYTICS PAGE ─────────────────────────────────────────────────────
@analytics_bp.route('/')
def index():
    days = int(request.args.get('days', 30))

    top_selling     = _top_selling(limit=10, days=days)
    dead_stock      = _dead_stock(days=days)
    rev_by_cat = [
        {
            'category': r.category or 'Other',
            'revenue': float(r.revenue),
            'orders': r.orders
        }
        for r in _revenue_by_category(days=days)
    ]
    avg_ov          = _avg_order_value(days=days)
    monthly_growth  = _monthly_growth()
    low_stock       = _low_stock_alerts()
    inventory_tv    = _inventory_turnover(days=days)

    total_revenue = (
        db.session.query(
            func.coalesce(
                func.sum(OrderItem.quantity * OrderItem.selling_price),
                0
            )
        ).scalar()
    )

    total_profit = (
        db.session.query(
            func.coalesce(
                func.sum(
                    OrderItem.quantity *
                    (OrderItem.selling_price - OrderItem.cost_price)
                ),
                0
            )
        ).scalar()
    )

    margin_percent = 0

    if float(total_revenue) > 0:
        margin_percent = round(
            (float(total_profit) / float(total_revenue)) * 100,
            1
        )

    most_profitable = (
        db.session.query(
            Product.product_name,
            func.sum(
                OrderItem.quantity *
                (OrderItem.selling_price - OrderItem.cost_price)
            ).label('profit')
        )
        .join(Product, Product.product_id == OrderItem.product_id)
        .group_by(Product.product_id)
        .order_by(desc('profit'))
        .limit(10)
        .all()
    )

    least_profitable = (
        db.session.query(
            Product.product_name,
            func.sum(
                OrderItem.quantity *
                (OrderItem.selling_price - OrderItem.cost_price)
            ).label('profit')
        )
        .join(Product, Product.product_id == OrderItem.product_id)
        .group_by(Product.product_id)
        .order_by(asc('profit'))
        .limit(10)
        .all()
    )

    return render_template(
        'analytics/index.html',
        days=days,
        top_selling=top_selling,
        dead_stock=dead_stock,
        rev_by_cat=rev_by_cat,
        avg_ov=avg_ov,
        monthly_growth=monthly_growth,
        low_stock=low_stock,
        inventory_tv=inventory_tv,
        total_revenue=total_revenue,
        total_profit=total_profit,
        margin_percent=margin_percent,
        most_profitable=most_profitable,
        least_profitable=least_profitable
    )

# ─── API endpoints for charts ─────────────────────────────────────────────────
@analytics_bp.route('/api/category-revenue')
def api_cat_rev():
    days = int(request.args.get('days', 30))
    data = _revenue_by_category(days=days)
    return jsonify([
        {'category': r.category or 'Uncategorised',
         'revenue': float(r.revenue),
         'units': r.units_sold}
        for r in data
    ])


@analytics_bp.route('/api/monthly-growth')
def api_monthly():
    return jsonify(_monthly_growth())
