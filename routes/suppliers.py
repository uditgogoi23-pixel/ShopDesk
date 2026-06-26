from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Supplier, StockEntry

suppliers_bp = Blueprint("suppliers", __name__)


# ─── LIST ALL SUPPLIERS ───────────────────────────────────────────────────────
@suppliers_bp.route("/")
def suppliers():
    all_suppliers = Supplier.query.order_by(Supplier.supplier_name).all()

    # Compute stats from stock entries
    entries = StockEntry.query.all()

    purchase_value = sum(float(e.invoice_total or 0) for e in entries)
    total_quantity = sum(float(e.quantity_added) for e in entries)
    total_gst      = sum(float(e.gst_amount or 0) for e in entries)
    pending_gst    = sum(float(e.gst_amount or 0) for e in entries if not e.gst_claimed)
    claimed_gst    = sum(float(e.gst_amount or 0) for e in entries if e.gst_claimed)
    supplier_count = len(all_suppliers)

    return render_template(
        "suppliers.html",
        suppliers=all_suppliers,
        purchase_value=purchase_value,
        total_quantity=total_quantity,
        supplier_count=supplier_count,
        total_gst=total_gst,
        pending_gst=pending_gst,
        claimed_gst=claimed_gst,
    )


# ─── ADD SUPPLIER ─────────────────────────────────────────────────────────────
@suppliers_bp.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name    = request.form.get("supplier_name", "").strip()
        phone   = request.form.get("phone", "").strip()
        email   = request.form.get("email", "").strip()
        gst_no  = request.form.get("gst_number", "").strip()
        address = request.form.get("address", "").strip()

        if not name:
            flash("Supplier name is required.", "danger")
            return render_template("suppliers/add.html")

        existing = Supplier.query.filter(
            db.func.lower(Supplier.supplier_name) == name.lower()
        ).first()

        if existing:
            flash("A supplier with this name already exists.", "danger")
            return render_template("suppliers/add.html")

        supplier = Supplier(
            supplier_name=name,
            phone=phone,
            email=email,
            gst_number=gst_no,
            address=address,
        )
        db.session.add(supplier)
        db.session.commit()
        flash(f'✓ Supplier "{name}" added successfully.', "success")
        return redirect(url_for("suppliers.suppliers"))

    return render_template("suppliers/add.html")


# ─── EDIT SUPPLIER ────────────────────────────────────────────────────────────
@suppliers_bp.route("/edit/<int:supplier_id>", methods=["GET", "POST"])
def edit(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)

    if request.method == "POST":
        supplier.supplier_name = request.form.get("supplier_name", supplier.supplier_name).strip()
        supplier.phone         = request.form.get("phone", supplier.phone).strip()
        supplier.email         = request.form.get("email", supplier.email).strip()
        supplier.gst_number    = request.form.get("gst_number", supplier.gst_number).strip()
        supplier.address       = request.form.get("address", supplier.address).strip()

        db.session.commit()
        flash(f'✓ Supplier "{supplier.supplier_name}" updated.', "success")
        return redirect(url_for("suppliers.suppliers"))

    return render_template("suppliers/edit.html", supplier=supplier)


# ─── DELETE SUPPLIER ──────────────────────────────────────────────────────────
@suppliers_bp.route("/delete/<int:supplier_id>", methods=["POST"])
def delete(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    name     = supplier.supplier_name
    db.session.delete(supplier)
    db.session.commit()
    flash(f'Supplier "{name}" deleted.', "warning")
    return redirect(url_for("suppliers.suppliers"))