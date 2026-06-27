from flask import Blueprint, send_file, render_template
import pandas as pd
from io import BytesIO
from datetime import datetime

from models import Product, Order, OrderItem, StockEntry, Payment
from extensions import db

export_bp = Blueprint("export", __name__)


# ── Export Landing Page ───────────────────────────────────────────────────────
@export_bp.route("/")
def index():
    return render_template("export/index.html")


# ── 1. Products ───────────────────────────────────────────────────────────────
@export_bp.route("/products")
def export_products():
    products = Product.query.all()
    data = []
    for p in products:
        data.append({
            "Product Name": p.product_name,
            "Category":     p.category,
            "Selling Price": float(p.price),
            "Cost Price":   float(p.cost_price),
            "Stock":        float(p.stock),
            "Unit Type":    p.unit_type,
            "Reorder Level": p.reorder_level,
            "Low Stock":    "Yes" if p.is_low_stock else "No",
            "Margin %":     p.margin_percent,
        })
    return _send_excel(data, "products")


# ── 2. Sales / Orders ─────────────────────────────────────────────────────────
@export_bp.route("/sales")
def export_sales():
    orders = Order.query.order_by(Order.order_date.desc()).all()
    data = []
    for o in orders:
        for item in o.order_items:
            data.append({
                "Order ID":       o.order_id,
                "Invoice No":     o.invoice_no or "—",
                "Date":           str(o.order_date),
                "Customer":       o.customer.name if o.customer else "Walk-in",
                "Product":        item.product.product_name if item.product else "—",
                "Qty":            float(item.quantity),
                "Unit":           item.unit_type,
                "Selling Price":  float(item.selling_price),
                "Subtotal":       float(item.quantity) * float(item.selling_price),
                "Payment Mode":   o.payment_mode or "—",
                "Status":         o.order_status,
            })
    return _send_excel(data, "sales")


# ── 3. Stock-In History ───────────────────────────────────────────────────────
@export_bp.route("/stock")
def export_stock():
    entries = StockEntry.query.order_by(StockEntry.entry_date.desc()).all()
    data = []
    for e in entries:
        data.append({
            "Entry ID":       e.entry_id,
            "Date":           str(e.entry_date),
            "Product":        e.product.product_name if e.product else "—",
            "Qty Added":      float(e.quantity_added),
            "Previous Stock": float(e.previous_stock),
            "New Stock":      float(e.new_stock),
            "Purchase Price": float(e.purchase_price),
            "GST %":          float(e.gst_percent),
            "GST Amount":     float(e.gst_amount),
            "Invoice Total":  float(e.invoice_total),
            "GST Claimed":    "Yes" if e.gst_claimed else "No",
            "Supplier":       e.supplier_name or "—",
            "Invoice No":     e.invoice_no or "—",
            "Remarks":        e.remarks or "—",
        })
    return _send_excel(data, "stock_in_history")


# ── 4. GST Summary ────────────────────────────────────────────────────────────
@export_bp.route("/gst")
def export_gst():
    # Output tax — from sales (if GST was charged)
    orders = Order.query.all()
    sales_data = []
    for o in orders:
        for item in o.order_items:
            sales_data.append({
                "Type":        "OUTPUT (Sale)",
                "Date":        str(o.order_date),
                "Reference":   o.invoice_no or f"Order #{o.order_id}",
                "Product":     item.product.product_name if item.product else "—",
                "Amount":      float(item.quantity) * float(item.selling_price),
                "GST %":       0,
                "GST Amount":  float(o.gst_amount) if o.gst_amount else 0,
            })

    # Input tax — from stock purchases
    entries = StockEntry.query.all()
    purchase_data = []
    for e in entries:
        purchase_data.append({
            "Type":        "INPUT (Purchase)",
            "Date":        str(e.entry_date),
            "Reference":   e.invoice_no or f"Entry #{e.entry_id}",
            "Product":     e.product.product_name if e.product else "—",
            "Amount":      float(e.invoice_total),
            "GST %":       float(e.gst_percent),
            "GST Amount":  float(e.gst_amount),
        })

    data = sales_data + purchase_data

    # Summary rows at the bottom
    total_output = sum(r["GST Amount"] for r in sales_data)
    total_input  = sum(r["GST Amount"] for r in purchase_data)
    net_payable  = total_output - total_input

    data.append({})  # blank row
    data.append({"Type": "TOTAL OUTPUT GST (collected from customers)", "GST Amount": total_output})
    data.append({"Type": "TOTAL INPUT GST (paid to suppliers)",         "GST Amount": total_input})
    data.append({"Type": "NET GST PAYABLE TO GOVERNMENT",               "GST Amount": net_payable})

    return _send_excel(data, "gst_summary")


# ── Helper ────────────────────────────────────────────────────────────────────
def _send_excel(data, filename):
    df     = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=filename[:31])
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    return send_file(
        output,
        as_attachment=True,
        download_name=f"{filename}_{timestamp}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )