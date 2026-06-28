"""
Harry Retail - Analytics Routes
Business insights: top sellers, dead stock, revenue by category,
order value trends, inventory turnover, low stock alerts
"""

from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models import Order, OrderItem, Payment, Product, StockEntry, Customer
from sqlalchemy import func, desc, asc
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
            func.sum(OrderItem.quantity * OrderItem.selling_price).label('revenue'),
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
            func.sum(OrderItem.quantity * OrderItem.selling_price).label('revenue'),
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
    return (
        Product.query
        .filter(Product.stock <= Product.reorder_level)
        .order_by(asc(Product.stock))
        .all()
    )


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


def _daily_revenue(days=30):
    """Daily revenue for trend chart."""
    since = date.today() - timedelta(days=days)
    rows = (
        db.session.query(
            Order.order_date.label('day'),
            func.coalesce(
                func.sum(OrderItem.quantity * OrderItem.selling_price), 0
            ).label('revenue'),
            func.coalesce(
                func.sum(
                    OrderItem.quantity * (OrderItem.selling_price - OrderItem.cost_price)
                ), 0
            ).label('profit'),
            func.count(func.distinct(Order.order_id)).label('orders'),
        )
        .join(OrderItem, Order.order_id == OrderItem.order_id)
        .filter(Order.order_date >= since)
        .group_by(Order.order_date)
        .order_by(Order.order_date)
        .all()
    )
    return [
        {
            'day':     str(r.day),
            'revenue': float(r.revenue),
            'profit':  float(r.profit),
            'orders':  r.orders,
        }
        for r in rows
    ]


def _forecast_revenue(daily_data, days_ahead=7):
    """Simple 7-day moving average forecast."""
    if len(daily_data) < 7:
        return []
    revenues = [d['revenue'] for d in daily_data]
    avg = sum(revenues[-7:]) / 7
    today = date.today()
    return [
        {
            'day':      str(today + timedelta(days=i + 1)),
            'revenue':  round(avg, 2),
            'forecast': True,
        }
        for i in range(days_ahead)
    ]


def _stock_depletion():
    """Predict how many days until each product runs out."""
    since = date.today() - timedelta(days=30)
    rows = (
        db.session.query(
            Product.product_id,
            Product.product_name,
            Product.category,
            Product.stock,
            Product.reorder_level,
            func.coalesce(
                func.sum(OrderItem.quantity), 0
            ).label('sold_30d'),
        )
        .outerjoin(OrderItem, Product.product_id == OrderItem.product_id)
        .outerjoin(
            Order,
            (OrderItem.order_id == Order.order_id) &
            (Order.order_date >= since)
        )
        .filter(Product.stock > 0)
        .group_by(Product.product_id)
        .all()
    )
    result = []
    for r in rows:
        daily_rate = float(r.sold_30d) / 30
        if daily_rate > 0:
            days_left = round(float(r.stock) / daily_rate)
        else:
            days_left = 999
        result.append({
            'product_name': r.product_name,
            'category':     r.category,
            'stock':        float(r.stock),
            'sold_30d':     float(r.sold_30d),
            'daily_rate':   round(daily_rate, 2),
            'days_left':    days_left,
        })
    result.sort(key=lambda x: x['days_left'])
    return [r for r in result if r['days_left'] < 30]


def _business_insights(daily_data, top_selling, dead_stock,
                        low_stock, total_revenue, total_profit,
                        margin_percent, monthly_growth):
    """Auto-generate human-readable business insights."""
    insights = []

    if len(daily_data) >= 14:
        first_half  = sum(d['revenue'] for d in daily_data[:len(daily_data) // 2])
        second_half = sum(d['revenue'] for d in daily_data[len(daily_data) // 2:])
        if first_half > 0:
            trend = round(((second_half - first_half) / first_half) * 100, 1)
            if trend > 0:
                insights.append({
                    'type':  'success',
                    'icon':  '📈',
                    'title': 'Revenue Growing',
                    'text':  f'Revenue up {trend}% in the second half of this period vs first half. Keep it up!'
                })
            elif trend < -10:
                insights.append({
                    'type':  'danger',
                    'icon':  '📉',
                    'title': 'Revenue Declining',
                    'text':  f'Revenue down {abs(trend)}% recently. Consider promotions or checking inventory.'
                })

    if margin_percent > 30:
        insights.append({
            'type':  'success',
            'icon':  '💰',
            'title': 'Healthy Margin',
            'text':  f'Gross margin is {margin_percent}% — good profitability. Industry average for retail is 20-30%.'
        })
    elif 0 < margin_percent < 15:
        insights.append({
            'type':  'warning',
            'icon':  '⚠️',
            'title': 'Low Margin Warning',
            'text':  f'Gross margin is only {margin_percent}%. Review your purchase prices or selling prices.'
        })

    if top_selling:
        best = top_selling[0]
        insights.append({
            'type':  'info',
            'icon':  '🏆',
            'title': 'Best Seller',
            'text':  f'{best.product_name} is your top product with {int(best.units_sold)} units sold and ₹{int(best.revenue)} revenue.'
        })

    if len(dead_stock) > 0:
        insights.append({
            'type':  'warning',
            'icon':  '💀',
            'title': 'Dead Stock Alert',
            'text':  f'{len(dead_stock)} products have zero sales this period. Consider discounting: {", ".join([p.product_name for p in dead_stock[:3]])}.'
        })

    critical = [p for p in low_stock if float(p.stock) == 0]
    if critical:
        insights.append({
            'type':  'danger',
            'icon':  '🚨',
            'title': 'Out of Stock!',
            'text':  f'{len(critical)} products are completely out of stock: {", ".join([p.product_name for p in critical[:3]])}. Reorder immediately!'
        })

    if len(monthly_growth) >= 2:
        last = monthly_growth[-1]
        if last['growth'] > 10:
            insights.append({
                'type':  'success',
                'icon':  '🚀',
                'title': 'Strong Monthly Growth',
                'text':  f"Revenue increased by {last['growth']}% compared to last month."
            })
    return insights


# ─── MAIN ANALYTICS PAGE ─────────────────────────────────────────────────────
@analytics_bp.route('/')
def index():
    days = int(request.args.get('days', 30))

    top_selling    = _top_selling(limit=10, days=days)
    dead_stock     = _dead_stock(days=days)
    rev_by_cat     = [
        {
            'category': r.category or 'Other',
            'revenue':  float(r.revenue),
            'orders':   r.orders
        }
        for r in _revenue_by_category(days=days)
    ]
    avg_ov         = _avg_order_value(days=days)
    monthly_growth = _monthly_growth()
    low_stock      = _low_stock_alerts()
    inventory_tv   = _inventory_turnover(days=days)

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

    daily_data = _daily_revenue(days)
    forecast   = _forecast_revenue(daily_data)
    depletion  = _stock_depletion()
    insights   = _business_insights(
        daily_data, top_selling, dead_stock, low_stock,
        total_revenue, total_profit, margin_percent, monthly_growth
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
        least_profitable=least_profitable,
        daily_data=daily_data,
        forecast=forecast,
        depletion=depletion,
        insights=insights
    )

@analytics_bp.route('/kpis')
def kpis():
    # Read date range from query params (default: last 30 days)
    end_str   = request.args.get('end',   str(date.today()))
    start_str = request.args.get('start', str(date.today() - timedelta(days=30)))

    end_date   = date.fromisoformat(end_str)
    start_date = date.fromisoformat(start_str)

    # --- Revenue in selected range ---
    revenue = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        func.date(Payment.payment_date) >= start_date,
        func.date(Payment.payment_date) <= end_date
    ).scalar()

    # --- Average order value ---
    avg_order = db.session.query(
        func.coalesce(func.avg(Payment.amount), 0)
    ).filter(
        func.date(Payment.payment_date) >= start_date,
        func.date(Payment.payment_date) <= end_date
    ).scalar()

    # --- Total orders in range ---
    total_orders = db.session.query(func.count(Order.order_id)).filter(
        func.date(Order.order_date) >= start_date,
        func.date(Order.order_date) <= end_date
    ).scalar()

    # --- Low stock count (products with stock < 10) ---
    low_stock_count = Product.query.filter(Product.stock < 10).count()

    # --- Yesterday's revenue (for trend arrow) ---
    yesterday = date.today() - timedelta(days=1)
    revenue_yesterday = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        func.date(Payment.payment_date) == yesterday
    ).scalar()

    # --- Today's revenue ---
    revenue_today = db.session.query(
        func.coalesce(func.sum(Payment.amount), 0)
    ).filter(
        func.date(Payment.payment_date) == date.today()
    ).scalar()

    # Trend: positive = up, negative = down
    trend = float(revenue_today) - float(revenue_yesterday)

    return jsonify({
        "revenue":          round(float(revenue), 2),
        "avg_order_value":  round(float(avg_order), 2),
        "total_orders":     int(total_orders),
        "low_stock_count":  int(low_stock_count),
        "revenue_today":    round(float(revenue_today), 2),
        "revenue_yesterday":round(float(revenue_yesterday), 2),
        "trend":            round(trend, 2),   # positive = up today vs yesterday
    })
# ─────────────────────────────────────────────
# NEW ROUTE 2: Daily Revenue Trend
# GET /analytics/revenue-trend?start=2024-01-01&end=2024-01-31
# Returns daily totals for the line chart
# ─────────────────────────────────────────────
@analytics_bp.route('/revenue-trend')
def revenue_trend():
    end_str   = request.args.get('end',   str(date.today()))
    start_str = request.args.get('start', str(date.today() - timedelta(days=30)))

    end_date   = date.fromisoformat(end_str)
    start_date = date.fromisoformat(start_str)

    # Current period: daily revenue
    rows = db.session.query(
        func.date(Payment.payment_date).label('day'),
        func.sum(Payment.amount).label('total')
    ).filter(
        func.date(Payment.payment_date) >= start_date,
        func.date(Payment.payment_date) <= end_date
    ).group_by('day').order_by('day').all()

    # Previous period (same length, shifted back)
    delta = (end_date - start_date).days
    prev_end   = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=delta)

    prev_rows = db.session.query(
        func.date(Payment.payment_date).label('day'),
        func.sum(Payment.amount).label('total')
    ).filter(
        func.date(Payment.payment_date) >= prev_start,
        func.date(Payment.payment_date) <= prev_end
    ).group_by('day').order_by('day').all()

    return jsonify({
        "current": [{"date": str(r.day), "amount": float(r.total)} for r in rows],
        "previous": [{"date": str(r.day), "amount": float(r.total)} for r in prev_rows],
    })
# ─── API endpoints for charts ─────────────────────────────────────────────────
@analytics_bp.route('/api/category-revenue')
def api_cat_rev():
    days = int(request.args.get('days', 30))
    data = _revenue_by_category(days=days)
    return jsonify([
        {'category': r.category or 'Uncategorised',
         'revenue':  float(r.revenue),
         'units':    r.units_sold}
        for r in data
    ])
