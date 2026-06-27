from flask import Blueprint, render_template

purchase_import_bp = Blueprint(
    "purchase_import",
    __name__,
    url_prefix="/purchase-import"
)


@purchase_import_bp.route("/", methods=["GET", "POST"])
def import_purchases():
    return render_template("import_purchases.html")