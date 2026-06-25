from flask import Blueprint, render_template

suppliers_bp = Blueprint("suppliers", __name__)

@suppliers_bp.route("/")
def suppliers():
    return render_template(
        "suppliers.html",

        purchase_value=0.00,
        total_quantity=0,
        supplier_count=1,
        pending_gst=0.00,
        claimed_gst=0.00,
        total_gst=0.00,

        suppliers=[
            {
                "name": "Agro Fresh",
                "phone": "9876543210",
                "email": "agro@email.com",
                "gst": "18ABCDE1234F1Z5",
                "purchase": 52300,
                "due": 0
            }
        ]
    )