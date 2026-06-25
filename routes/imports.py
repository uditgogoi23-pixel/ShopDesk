from flask import Blueprint, render_template, request, flash
import pandas as pd
from flask import redirect, url_for
from extensions import db
from models import Product
from sqlalchemy import func
from flask import send_file

imports_bp = Blueprint("imports", __name__)


@imports_bp.route("/", methods=["GET", "POST"])
def import_products():
    print("METHOD:", request.method)

    if request.method == "POST":
        print("POST RECEIVED")
        print(request.files)

        file = request.files.get("excel_file")

        if not file:
            flash("Please select an Excel file.", "danger")
            return render_template("import_products.html")

        try:
            df = pd.read_excel(file)

            required_columns = [
                "Product Name",
                "Category",
                "Price",
                "Stock",
                "Reorder Level"
            ]

            missing_columns = [
                col for col in required_columns
                if col not in df.columns
            ]

            if missing_columns:
                flash(
                    f"Missing required column(s): {', '.join(missing_columns)}",
                    "danger"
                )
                return render_template("import_products.html")

            imported = 0
            skipped = 0

            for _, row in df.iterrows():

                product_name = str(row["Product Name"]).strip()
                category = str(row["Category"]).strip()

                existing = Product.query.filter(
                    func.lower(Product.product_name) == product_name.lower()
                ).first()

                if existing:
                    skipped += 1
                    continue

                product = Product(
                    product_name=product_name,
                    category=category,
                    price=row["Price"],
                    stock=row["Stock"],
                    unit_type="Units",
                    cost_price=0,
                    reorder_level=row["Reorder Level"]
                )

                db.session.add(product)
                imported += 1

            db.session.commit()

            flash(
                f"Import completed! Imported: {imported} | Skipped (duplicates): {skipped}",
                "success"
            )

            return redirect(url_for("products.index"))

        except Exception as e:
            flash(f"Error reading Excel file: {e}", "danger")
            return render_template("import_products.html")

    return render_template("import_products.html")
@imports_bp.route("/download-template")
def download_template():

    data = {
        "Product Name": ["Example Product"],
        "Category": ["Groceries"],
        "Price": [100],
        "Stock": [50],
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
    