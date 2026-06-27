from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from models import (
    Product,
    StockEntry,
    Supplier,
)
from datetime import datetime

stock_bp = Blueprint('stock', __name__)


@stock_bp.route('/')
def index():
    entries = (
        db.session.query(StockEntry)
        .order_by(StockEntry.entry_date.desc())
        .all()
    )
    return render_template('stock/index.html', entries=entries)


@stock_bp.route('/add', methods=['GET', 'POST'])
def add():
    products = Product.query.order_by(Product.product_name).all()
    suppliers = Supplier.query.order_by(Supplier.supplier_name).all()

    if request.method == 'POST':
        product_id     = request.form.get('product_id', type=int)
        quantity_added = request.form.get('quantity_added', type=float)
        purchase_price = request.form.get('purchase_price', type=float)
        gst_percent    = request.form.get('gst_percent', type=float, default=0)
        supplier_name  = request.form.get('supplier_name', '').strip()
        invoice_no     = request.form.get('invoice_no', '').strip()
        remarks        = request.form.get('remarks', '').strip()
        gst_claimed    = request.form.get('gst_claimed') == 'on'

        product = Product.query.get_or_404(product_id)

        gst_amount    = round((purchase_price * quantity_added) * (gst_percent / 100), 2)
        invoice_total = round((purchase_price * quantity_added) + gst_amount, 2)
        prev_stock    = float(product.stock)
        new_stock     = prev_stock + quantity_added

        entry = StockEntry(
            product_id     = product_id,
            quantity_added = quantity_added,
            previous_stock = prev_stock,
            new_stock      = new_stock,
            purchase_price = purchase_price,
            gst_percent    = gst_percent,
            gst_amount     = gst_amount,
            invoice_total  = invoice_total,
            supplier_name  = supplier_name,
            invoice_no     = invoice_no,
            remarks        = remarks,
            gst_claimed    = gst_claimed,
            entry_date     = datetime.now(),
        )

        product.stock      = new_stock
        product.cost_price = purchase_price   # update latest cost price

        db.session.add(entry)
        db.session.commit()

        flash(f'Stock added! {product.product_name} → {new_stock} {product.unit_type}', 'success')
        return redirect(url_for('stock.index'))

    preselect_id = request.args.get('product_id', type=int)
    return render_template('stock/add.html', products=products, suppliers=suppliers, preselect_id=preselect_id)


@stock_bp.route('/api/product/<int:product_id>')
def product_info(product_id):
    p = Product.query.get_or_404(product_id)
    return jsonify({
        'current_stock': float(p.stock),
        'unit_type':     p.unit_type,
        'cost_price':    float(p.cost_price),
        'reorder_level': p.reorder_level,
    })
