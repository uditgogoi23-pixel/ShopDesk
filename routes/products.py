"""
Harry Retail - Products Routes
Full CRUD: Add, View, Update, Delete products
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from models import Product, StockEntry

products_bp = Blueprint('products', __name__)

CATEGORIES = [
    'Groceries', 'Dairy & Eggs', 'Beverages', 'Snacks & Confectionery',
    'Personal Care', 'Household', 'Medicines & Healthcare',
    'Bakery', 'Fruits & Vegetables', 'Frozen Foods', 'Other'
]


# ─── LIST ALL PRODUCTS ───────────────────────────────────────────────────────
@products_bp.route('/')
def index():
    search   = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    sort     = request.args.get('sort', 'product_name')

    query = Product.query

    if search:
        query = query.filter(Product.product_name.ilike(f'%{search}%'))
    if category:
        query = query.filter(Product.category == category)

    sort_map = {
        'product_name': Product.product_name,
        'price_asc':    Product.price.asc(),
        'price_desc':   Product.price.desc(),
        'stock_asc':    Product.stock.asc(),
        'stock_desc':   Product.stock.desc(),
    }
    query = query.order_by(sort_map.get(sort, Product.product_name))

    products   = query.all()
    low_stock  = [p for p in products if p.stock <= 10]

    return render_template(
        'products/index.html',
        products=products,
        low_stock=low_stock,
        categories=CATEGORIES,
        search=search,
        selected_category=category,
        sort=sort,
    )


# ─── ADD PRODUCT ─────────────────────────────────────────────────────────────
@products_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name     = request.form.get('product_name', '').strip()
        category = request.form.get('category', '').strip()
        price    = request.form.get('price', 0)
        stock    = request.form.get('stock', 0)

        if not name or not price:
            flash('Product name and price are required.', 'danger')
            return render_template('products/add.html', categories=CATEGORIES)

        product = Product(
            product_name=name,
            category=category,
            price=float(price),
            stock=int(stock),
        )
        db.session.add(product)
        db.session.commit()
        flash(f'✓ Product "{name}" added successfully.', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/add.html', categories=CATEGORIES)


# ─── EDIT PRODUCT ─────────────────────────────────────────────────────────────
@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.product_name = request.form.get('product_name', product.product_name).strip()
        product.category     = request.form.get('category', product.category)
        product.price        = float(request.form.get('price', product.price))
        product.stock        = int(request.form.get('stock', product.stock))

        db.session.commit()
        flash(f'✓ Product "{product.product_name}" updated.', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/edit.html', product=product, categories=CATEGORIES)


# ─── DELETE PRODUCT ───────────────────────────────────────────────────────────
@products_bp.route('/delete/<int:product_id>', methods=['POST'])
def delete(product_id):
    product = Product.query.get_or_404(product_id)
    name    = product.product_name
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{name}" deleted.', 'warning')
    return redirect(url_for('products.index'))


# ─── STOCK UPDATE (AJAX) ──────────────────────────────────────────────────────
@products_bp.route('/update-stock/<int:product_id>', methods=['POST'])
def update_stock(product_id):
    product = Product.query.get_or_404(product_id)
    data    = request.get_json()
    product.stock = int(data.get('stock', product.stock))
    db.session.commit()
    return jsonify({'success': True, 'stock': product.stock})


# ─── API: ALL PRODUCTS JSON ───────────────────────────────────────────────────
@products_bp.route('/api/all')
def api_all():
    products = Product.query.filter(Product.stock > 0).order_by(Product.product_name).all()
    return jsonify([p.to_dict() for p in products])
@products_bp.route('/refill/<int:product_id>', methods=['GET', 'POST'])
def refill_stock(product_id):

    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':

        quantity = int(request.form.get('quantity', 0))
        remarks = request.form.get('remarks', '')

        previous_stock = product.stock
        new_stock = previous_stock + quantity

        product.stock = new_stock

        entry = StockEntry(
            product_id=product.product_id,
            quantity_added=quantity,
            previous_stock=previous_stock,
            new_stock=new_stock,
            remarks=remarks
        )

        db.session.add(entry)
        db.session.commit()

        flash('Stock updated successfully!', 'success')

        return redirect(url_for('products.index'))

    return render_template(
        'products/refill.html',
        product=product
    )
