"""
ShopDesk — Products Routes
Full CRUD: Add, View, Update, Delete, Refill stock.

CHANGES (Migration 001):
  - All forms now handle unit_type, cost_price, reorder_level
  - Low-stock check uses per-product reorder_level (not hardcoded 10)
  - api/all now returns unit_type so the POS modal can configure itself
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from models import Product, StockEntry, UNIT_TYPES
from sqlalchemy import func
import os
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image

products_bp = Blueprint('products', __name__)

CATEGORIES = [
    'Groceries', 'Dairy & Eggs', 'Beverages', 'Snacks & Confectionery',
    'Personal Care', 'Household', 'Medicines & Healthcare',
    'Bakery', 'Fruits & Vegetables', 'Frozen Foods', 'Other'
]


# ─── LIST ALL PRODUCTS ────────────────────────────────────────────────────────
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

    products  = query.all()
    # Use per-product reorder_level instead of hardcoded 10
    low_stock = [p for p in products if p.is_low_stock]
    inventory_value = sum(
    float(p.stock) * float(p.price or 0)
    for p in products
)
    
    categories = [
            c[0] for c in db.session.query(Product.category)
            .distinct()
            .order_by(Product.category)
            .all()
        ]

    return render_template(
            'products/index.html',
            products=products,
            low_stock=low_stock,
            categories=categories,
            inventory_value=inventory_value,
            search=search,
            selected_category=category,
            sort=sort,
            low_stock_count=len(low_stock),
        )

@products_bp.route("/low-stock")
def low_stock():

    products = Product.query.filter(
        Product.stock <= Product.reorder_level
    ).order_by(Product.stock.asc()).all()
    
    return render_template(
        "products/low_stock.html",
        products=products
    )
# ─── ADD PRODUCT ──────────────────────────────────────────────────────────────
@products_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name          = request.form.get('product_name', '').strip()
        category      = request.form.get('category', '').strip()
        price         = request.form.get('price', 0)
        stock         = request.form.get('stock', 0)
        unit_type     = request.form.get('unit_type', 'Units')
        cost_price    = request.form.get('cost_price', 0) or 0
        reorder_level = request.form.get('reorder_level', 10) or 10
        image = request.files.get("product_image")
        filename = "default_product.png"
        discount_type = request.form.get("discount_type", "none")
        discount_value = request.form.get("discount_value", 0) or 0
        
        
        
        if not name or not price:
            flash('Product name and price are required.', 'danger')
            return render_template('products/add.html',
                                   categories=CATEGORIES, unit_types=UNIT_TYPES)

        if image and image.filename:
            filename = secure_filename(image.filename)
            filepath = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                filename
    )

            img = Image.open(image)

            img.thumbnail((300, 300))

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.save(
                filepath,
                "JPEG",
                quality=85,
                optimize=True
            )
                    
        existing = Product.query.filter(
        func.lower(Product.product_name) == name.lower(),
        func.lower(Product.category) == category.lower()
        ).first()

        if existing:
            flash("A product with the same name and category already exists.", "danger")
            return render_template(
            "products/add.html",
            categories=CATEGORIES,
            unit_types=UNIT_TYPES
        )
        product = Product(
            product_name=name,
            category=category,
            price=float(price),
            stock=float(stock),
            unit_type=unit_type,
            cost_price=float(cost_price),
            discount_type=discount_type,
            discount_value=float(discount_value),
            reorder_level=int(reorder_level),
            image=filename,
        )
        db.session.add(product)
        db.session.commit()

        flash(f'✓ Product "{name}" added successfully.', 'success')
        return redirect(url_for('products.index'))

        
    return render_template('products/add.html',
                           categories=CATEGORIES, unit_types=UNIT_TYPES)


# ─── EDIT PRODUCT ─────────────────────────────────────────────────────────────
@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
def edit(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.product_name = request.form.get('product_name', product.product_name).strip()
        product.category = request.form.get('category', product.category).strip()
        product.price = float(request.form.get('price', product.price))
        product.stock = float(request.form.get('stock', product.stock))
        product.unit_type = request.form.get('unit_type', product.unit_type)
        product.cost_price = float(request.form.get('cost_price', 0) or 0)
        product.reorder_level = int(request.form.get('reorder_level', 10) or 10)
        product.discount_type = request.form.get("discount_type", "none")
        product.discount_value = float(request.form.get("discount_value", 0) or 0)

        existing = Product.query.filter(
            func.lower(Product.product_name) == product.product_name.lower(),
            func.lower(Product.category) == product.category.lower(),
            Product.product_id != product.product_id
        ).first()

        if existing:
            flash("A product with the same name and category already exists.", "danger")
            return render_template(
                "products/edit.html",
                product=product,
                categories=CATEGORIES,
                unit_types=UNIT_TYPES
            )

        db.session.commit()
        flash(f'✓ Product "{product.product_name}" updated.', "success")
        return redirect(url_for("products.index"))

    return render_template(
        "products/edit.html",
        product=product,
        categories=CATEGORIES,
        unit_types=UNIT_TYPES
    )

        
    


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
    product.stock = float(data.get('stock', product.stock))
    db.session.commit()
    return jsonify({'success': True, 'stock': float(product.stock)})


# ─── API: ALL PRODUCTS JSON (used by POS modal) ───────────────────────────────
@products_bp.route('/api/all')
def api_all():
    products = Product.query.filter(Product.stock > 0).order_by(Product.product_name).all()
    return jsonify([p.to_dict() for p in products])


# ─── REFILL STOCK ─────────────────────────────────────────────────────────────
@products_bp.route('/refill/<int:product_id>', methods=['GET', 'POST'])
def refill_stock(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        quantity       = float(request.form.get('quantity', 0))
        remarks        = request.form.get('remarks', '')
        supplier_name = request.form.get('supplier_name', '')
        invoice_no = request.form.get('invoice_no', '')
        purchase_price = float(request.form.get('purchase_price') or 0)
        gst_percent = float(request.form.get('gst_percent') or 0)
        previous_stock = float(product.stock)
        new_stock      = previous_stock + quantity
        subtotal = quantity * purchase_price
        gst_amount = subtotal * gst_percent / 100
        invoice_total = subtotal + gst_amount

        product.stock = new_stock

        entry = StockEntry(
            product_id     = product.product_id,
            quantity_added = quantity,
            previous_stock = previous_stock,
            new_stock      = new_stock,
            remarks        = remarks,
            supplier_name=supplier_name,
            invoice_no=invoice_no,
            purchase_price=purchase_price,
            gst_percent=gst_percent,
            gst_amount=gst_amount,
            invoice_total=invoice_total,
            gst_claimed=False,
        )
        db.session.add(entry)
        db.session.commit()
        flash(f'✓ Stock updated! {product.product_name} now has {new_stock} {product.unit_type}.', 'success')
        return redirect(url_for('products.index'))

    return render_template('products/refill.html', product=product)
# ==========================================
# PURCHASE HISTORY
# ==========================================

@products_bp.route('/purchase-history')
def purchase_history():
    print("PURCHASE HISTORY ROUTE RUNNING")
    entries = StockEntry.query.order_by(
        StockEntry.entry_date.desc()
    ).all()

    purchase_value = sum(
    float(e.invoice_total or 0)
    for e in entries
)

    total_gst = sum(
        float(e.gst_amount or 0)
        for e in entries
)

    pending_gst = sum(
        float(e.gst_amount or 0)
        for e in entries
        if not e.gst_claimed
)

    claimed_gst = sum(
        float(e.gst_amount or 0)
        for e in entries
        if e.gst_claimed
)

    total_quantity = sum(
        float(e.quantity_added)
        for e in entries
)

    supplier_count = len(
        set(
        e.supplier_name
        for e in entries
        if e.supplier_name
    )
)

    return render_template(
    "products/purchase_history.html",
    entries=entries,
    purchase_value=purchase_value,
    total_quantity=total_quantity,
    supplier_count=supplier_count,
    total_gst=total_gst,
    pending_gst=pending_gst,
    claimed_gst=claimed_gst
)
