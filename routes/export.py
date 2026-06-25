from flask import Blueprint, send_file
import pandas as pd
from io import BytesIO

from models import Product

export_bp = Blueprint("export", __name__)

@export_bp.route("/products")
def export_products():

    products = Product.query.all()

    data = []

    for product in products:
        data.append({
            "Product Name": product.product_name,
            "Category": product.category,
            "Price": float(product.price),
            "Stock": float(product.stock),
            "Unit Type": product.unit_type,
            "Cost Price": float(product.cost_price),
            "Reorder Level": product.reorder_level
        })

    df = pd.DataFrame(data)

    output = BytesIO()

    df.to_excel(output, index=False)

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="products.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )