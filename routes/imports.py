from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
import pandas as pd
from sqlalchemy import func

from extensions import db
from models import Product

imports_bp = Blueprint("imports", __name__)


@imports_bp.route("/", methods=["GET", "POST"])
def import_products():

    if request.method == "POST":

        file = request.files.get("excel_file")

        if not file:
            flash("Please select an Excel file.", "danger")
            return render_template("import_products.html")

        try:
            df = pd.read_excel(file)
            print("Columns:", df.columns.tolist())

            required_columns = [
                "Product Name",
                "Category",
                "Selling Price",
                "Opening Stock",
                "Purchase Price",
                "Unit",
                "Reorder Level"
            ]

            missing = [
                col for col in required_columns
                if col not in df.columns
            ]

            if missing:
                flash(
                    f"Missing required column(s): {', '.join(missing)}",
                    "danger"
                )
                return render_template("import_products.html")

            imported = 0
            skipped = 0

            for _, row in df.iterrows():

                product_name = str(row["Product Name"]).strip()

                existing = Product.query.filter(
                    func.lower(Product.product_name) == product_name.lower()
                ).first()

                if existing:
                    skipped += 1
                    continue

                product = Product(
                    product_name=product_name,
                    category=row["Category"],
                    price=float(row["Selling Price"]),
                    stock=float(row["Opening Stock"]),
                    unit_type=row["Unit"],
                    cost_price=float(row["Purchase Price"]),
                    reorder_level=float(row["Reorder Level"]),
                    image="default_product.png"
                )

                db.session.add(product)
                imported += 1

            db.session.commit()

            flash(
                f"Import completed! Imported: {imported} | Skipped: {skipped}",
                "success"
            )

            return redirect(url_for("products.index"))

        except Exception as e:
            flash(f"Error reading Excel file: {e}", "danger")

    return render_template("import_products.html")


@imports_bp.route("/download-template")
def download_template():

    data = {
        "Product Name": ["Example Product"],
        "Category": ["Groceries"],
        "Selling Price": [100],
        "Opening Stock": [50],
        "Purchase Price": [80],
        "Unit": ["Units"],
        "Reorder Level": [10]
    }

    df = pd.DataFrame(data)

    file_path = "product_import_template.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(
        file_path,
        as_attachment=True,
        download_name="product_import_template.xlsx"
    )