from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
import pandas as pd
from extensions import db
from models import Supplier

supplier_import_bp = Blueprint(
    "supplier_import",
    __name__,
)


@supplier_import_bp.route("/import", methods=["GET", "POST"])
def import_suppliers():

    if request.method == "POST":

        file = request.files.get("excel_file")

        if not file:
            flash("Please select an Excel file.", "danger")
            return redirect(request.url)

        try:
            df = pd.read_excel(file)

            required = [
                "Supplier Name",
                "Phone",
                "Email",
                "GST Number",
                "Address"
            ]

            missing = [
                c for c in required
                if c not in df.columns
            ]

            if missing:
                flash(
                    f"Missing columns: {', '.join(missing)}",
                    "danger"
                )
                return redirect(request.url)

            imported = 0
            skipped = 0

            for _, row in df.iterrows():

                name = str(row["Supplier Name"]).strip()

                exists = Supplier.query.filter_by(
                    supplier_name=name
                ).first()

                if exists:
                    skipped += 1
                    continue

                supplier = Supplier(
                    supplier_name=name,
                    phone=str(row.get("Phone", "")),
                    email=str(row.get("Email", "")),
                    gst_number=str(row.get("GST Number", "")),
                    address=str(row.get("Address", ""))
                )

                db.session.add(supplier)
                imported += 1

            db.session.commit()

            flash(
                f"{imported} suppliers imported. {skipped} skipped.",
                "success"
            )

            return redirect(url_for("suppliers.suppliers"))

        except Exception as e:

            flash(str(e), "danger")

    return render_template("import_suppliers.html")

@supplier_import_bp.route("/download-template")
def download_template():

    data = {
        "Supplier Name": ["ABC Distributors"],
        "Phone": ["9876543210"],
        "Email": ["abc@email.com"],
        "GST Number": ["18ABCDE1234F1Z5"],
        "Address": ["Guwahati, Assam"]
    }

    df = pd.DataFrame(data)

    file_path = "supplier_import_template.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(
        file_path,
        as_attachment=True,
        download_name="supplier_import_template.xlsx"
    )
