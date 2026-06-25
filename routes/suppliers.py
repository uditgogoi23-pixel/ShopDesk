from flask import Blueprint, render_template

suppliers_bp = Blueprint("suppliers", __name__)

@suppliers_bp.route("/")
def suppliers():
    return render_template("suppliers.html")