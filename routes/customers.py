from flask import Blueprint, render_template
from models import Customer
from models import Customer, Order

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/')
def index():
    customers = Customer.query.all()
    return render_template(
        'customers/index.html',
        customers=customers
    )
@customers_bp.route("/<int:customer_id>/history")
def history(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    orders = (
        Order.query
        .filter_by(customer_id=customer_id)
        .order_by(Order.order_date.desc())
        .all()
    )

    total_orders = len(orders)

    total_spent = sum(
        order.total_amount or 0
        for order in orders
    )
    avg_order = round(total_spent / total_orders, 2) if total_orders else 0

    return render_template(
    "customers/history.html",
    customer=customer,
    orders=orders,
    total_orders=total_orders,
    total_spent=total_spent,
    avg_order=avg_order
)