from flask import Blueprint, render_template
from models import Customer

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/')
def index():
    customers = Customer.query.all()
    return render_template(
        'customers/index.html',
        customers=customers
    )