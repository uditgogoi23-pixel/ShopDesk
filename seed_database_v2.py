import random
from decimal import Decimal
from datetime import datetime, timedelta

from faker import Faker

from app import create_app
from extensions import db

from models import (
    Product,
    Supplier,
    Customer,
    Order,
    OrderItem,
    Payment,
    StockEntry,
)

app = create_app()

fake = Faker("en_IN")
fake.unique.clear()


# ==============================
# CONFIGURATION
# ==============================

PRODUCT_COUNT = 500
SUPPLIER_COUNT = 80
CUSTOMER_COUNT = 2000
ORDER_COUNT = 12000

START_DATE = datetime.now() - timedelta(days=365)

PAYMENT_MODES = [
    "Cash",
    "UPI",
    "Card",
]

ORDER_STATUS = [
    "Completed",
    "Completed",
    "Completed",
    "Completed",
    "Completed",
    "Completed",
    "Completed",
    "Completed",
    "Cancelled",
]

GST_OPTIONS = [0, 5, 12, 18]

CATEGORIES = [
    "Dairy",
    "Snacks",
    "Beverages",
    "Bakery",
    "Rice & Grains",
    "Pulses",
    "Flour",
    "Cooking Oil",
    "Personal Care",
    "Cleaning",
    "Stationery",
    "Frozen Food",
    "Biscuits",
    "Chocolates",
    "Baby Care",
    "Vegetables",
    "Fruits",
    "Spices",
    "Tea & Coffee",
    "Soft Drinks",
]

UNITS = [
    "Units",
    "kg",
    "litre",
    "pack",
    "piece",
    "dozen"
]

PRODUCT_NAMES = [
    "Milk","Bread","Butter","Paneer","Curd","Cheese","Rice",
    "Atta","Sugar","Salt","Tea","Coffee","Maggi","Pasta",
    "Soap","Shampoo","Toothpaste","Biscuits","Chips","Chocolate",
    "Soft Drink","Juice","Cooking Oil","Dal","Detergent",
    "Hand Wash","Notebook","Pen","Pencil","Eggs","Corn Flakes",
    "Ketchup","Pickle","Jam","Honey","Toilet Cleaner",
    "Floor Cleaner","Tissue Paper","Face Wash","Body Lotion",
    "Tooth Brush","Green Tea","Coffee Powder","Mineral Water",
    "Ice Cream","Frozen Peas","Onion","Potato","Tomato",
    "Apple","Orange","Banana","Cabbage","Carrot","Spinach","Coriander"
]
# ==============================
# HELPER FUNCTIONS
# ==============================

def random_order_date():
    return START_DATE + timedelta(
        days=random.randint(0, 365),
        hours=random.randint(8, 21),
        minutes=random.randint(0, 59)
    )


def invoice_number(order_id):
    return f"INV-{2026}{order_id:06d}"


def weighted_customer(customers):
    """
    60% of orders come from regular customers.
    """
    if random.random() < 0.60:
        return random.choice(customers[:300])
    return random.choice(customers)


def weighted_product(products):
    """
    Fast-moving products are sold more often.
    """
    if random.random() < 0.60:
        return random.choice(products[:80])
    return random.choice(products)


def refill_product(product):

    qty = random.randint(100, 400)

    previous_stock = float(product.stock)

    purchase_price = float(product.cost_price)

    gst_percent = random.choice([5, 12, 18])

    gst_amount = round(
        qty * purchase_price * gst_percent / 100,
        2
    )

    invoice_total = round(
        qty * purchase_price + gst_amount,
        2
    )

    entry = StockEntry(

        product_id=product.product_id,

        quantity_added=qty,

        previous_stock=previous_stock,

        new_stock=previous_stock + qty,

        purchase_price=purchase_price,

        gst_percent=gst_percent,

        gst_amount=gst_amount,

        invoice_total=invoice_total,

        supplier_name=f"Supplier {random.randint(1,80)}",

        invoice_no=f"PO-{random.randint(10000,99999)}",

        remarks="Automatic Stock Refill",

        gst_claimed=True,

        entry_date=random_order_date()

    )

    product.stock = previous_stock + qty

    db.session.add(entry)
    
def create_products():

    print("Creating Products...")

    for i in range(PRODUCT_COUNT):

        product = Product(
            product_name=f"{random.choice(PRODUCT_NAMES)} {i+1}",
            category=random.choice(CATEGORIES),
            price=round(random.uniform(20, 700), 2),
            cost_price=round(random.uniform(10, 500), 2),
            stock=random.randint(30, 500),
            unit_type=random.choice(UNITS),
            reorder_level=random.randint(10, 50),
            image="default_product.png"
        )

        db.session.add(product)

    db.session.commit()

    print("✓ Products Created")
def create_suppliers():

    print("Creating Suppliers...")

    for i in range(SUPPLIER_COUNT):

        supplier = Supplier(
            supplier_name=fake.company(),
            phone=f"9{random.randint(100000000,999999999)}",
            email=fake.unique.company_email(),
            gst_number=f"18ABCDE{random.randint(1000,9999)}F1Z5",
            address=fake.address()
        )

        db.session.add(supplier)

    db.session.commit()

    print("✓ Suppliers Created")
def create_customers():

    print("Creating Customers...")

    for i in range(CUSTOMER_COUNT):

        customer = Customer(
            name=fake.name(),
            phone=f"9{random.randint(100000000,999999999)}",
            email=fake.unique.email(),
            city=fake.city()
        )

        db.session.add(customer)

    db.session.commit()

    print("✓ Customers Created")
# ==============================
# CREATE ORDERS
# ==============================

def create_orders():

    print("Creating Orders...")

    customers = Customer.query.all()
    products = Product.query.all()

    for order_no in range(1, ORDER_COUNT + 1):

        customer = weighted_customer(customers)

        order_date = random_order_date()

        payment_mode = random.choice(PAYMENT_MODES)

        status = random.choice(ORDER_STATUS)

        order = Order(

            invoice_no=invoice_number(order_no),

            customer_id=customer.customer_id,

            order_date=order_date.date(),

            payment_mode=payment_mode,

            order_status=status,

            total_amount=0,

            discount=0,

            gst_amount=0,

            grand_total=0

        )

        db.session.add(order)

        db.session.flush()

        subtotal = 0

        gst_total = 0

        item_count = random.randint(1, 6)

        selected_products = random.sample(products, item_count)

        for product in selected_products:

            if float(product.stock) <= float(product.reorder_level):

                refill_product(product)

            qty = random.randint(1, 5)

            if float(product.stock) < qty:

                continue

            selling_price = float(product.price)

            cost_price = float(product.cost_price)

            gst_percent = random.choice(GST_OPTIONS)

            line_total = selling_price * qty

            gst = line_total * gst_percent / 100

            item = OrderItem(

                order_id=order.order_id,

                product_id=product.product_id,

                quantity=qty,

                unit_type=product.unit_type,

                selling_price=selling_price,

                cost_price=cost_price,

                unit_price=selling_price,

                subtotal=line_total

            )

            db.session.add(item)

            product.stock = float(product.stock) - qty

            subtotal += line_total

            gst_total += gst

        discount = 0

        if subtotal > 5000:
            discount = round(subtotal * 0.05, 2)

        grand_total = subtotal + gst_total - discount

        order.total_amount = round(subtotal, 2)
        order.discount = round(discount, 2)
        order.gst_amount = round(gst_total, 2)
        order.grand_total = round(grand_total, 2)

        payment = Payment(
            order_id=order.order_id,
            payment_mode=payment_mode,
            amount=round(grand_total, 2),
            payment_date=order_date
        )

        db.session.add(payment)

        if order_no % 250 == 0:
            db.session.commit()
            print(f"{order_no} orders completed")

    db.session.commit()

    print("✓ Orders Created")

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    with app.app_context():

        print("=" * 60)
        print("SHOPDESK DATABASE GENERATOR")
        print("=" * 60)

        create_products()
        create_suppliers()
        create_customers()
        create_orders()

        db.session.commit()

        print()
        print("=" * 60)
        print("DATABASE GENERATED SUCCESSFULLY")
        print("=" * 60)