from flask import (
    Flask, render_template, request,
    redirect, url_for, session, send_file
)
import importlib
import pandas as pd
import io
import os
import sys
import uuid
from flask import flash
from registry.hierarchy import DEPARTMENTS
from registry.kpis import KPI_REGISTRY
from services.excel_loader import load_excel
from services.chart_engine import generate_charts
from services.formatters import format_number
from services.kpi_storage import save_kpi_result, load_kpi_result



# -------------------------------------------------
# APP INIT
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Safe temp directory
TMP_DIR = os.path.join(BASE_DIR, "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "pm-cona-secret"


# -------------------------------------------------
# LOGIN
# -------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # TEMP STATIC AUTH
        if username == "admin" and password == "admin123":
            session["user"] = username
            session["role"] = "admin"
            return redirect(url_for("departments"))

        elif username == "user" and password == "user123":
            session["user"] = username
            session["role"] = "user"
            return redirect(url_for("departments"))

        flash("Invalid credentials", "error")
        return redirect(url_for("login"))

    return render_template("login.html")



# -------------------------------------------------
# DEPARTMENTS
# -------------------------------------------------
@app.route("/departments")
def departments():
    return render_template("departments.html", departments=DEPARTMENTS)


# -------------------------------------------------
# KRAs
# -------------------------------------------------
@app.route("/kras/<dept_id>")
def kras(dept_id):
    dept = DEPARTMENTS.get(dept_id)
    if not dept:
        return "Invalid department", 404

    if dept.get("has_subdepartments"):
        return render_template(
            "subdepartments.html",
            dept_id=dept_id,
            subdepartments=dept["subdepartments"]
        )

    return render_template(
        "kras.html",
        dept_id=dept_id,
        kras=dept["kras"],
        has_subdept=False
    )


@app.route("/kras/<dept_id>/<sub_id>")
def kras_with_subdept(dept_id, sub_id):
    dept = DEPARTMENTS.get(dept_id)
    if not dept or sub_id not in dept.get("subdepartments", {}):
        return "Invalid sub-department", 404

    kras = dept["subdepartments"][sub_id]["kras"]

    return render_template(
        "kras.html",
        dept_id=dept_id,
        sub_id=sub_id,
        kras=kras,
        has_subdept=True
    )


# -------------------------------------------------
# KPIs
# -------------------------------------------------
@app.route("/kpis/<dept_id>/<kra_id>")
def kpis_no_subdept(dept_id, kra_id):
    dept = DEPARTMENTS.get(dept_id)
    if not dept:
        return "Invalid department", 404

    if dept.get("has_subdepartments"):
        return "Sub-department required", 400

    kras = dept.get("kras", {})
    if kra_id not in kras:
        return "Invalid KRA", 404

    kpi_ids = kras[kra_id]["kpis"]

    return render_template(
        "kpis.html",
        dept_id=dept_id,
        kpis={k: KPI_REGISTRY[k] for k in kpi_ids}
    )


@app.route("/kpis/<dept_id>/<sub_id>/<kra_id>")
def kpis_with_subdept(dept_id, sub_id, kra_id):
    dept = DEPARTMENTS.get(dept_id)
    if not dept:
        return "Invalid department", 404

    try:
        kpi_ids = (
            dept["subdepartments"][sub_id]
            ["kras"][kra_id]
            ["kpis"]
        )
    except KeyError:
        return "Invalid KRA", 404

    return render_template(
        "kpis.html",
        dept_id=dept_id,
        sub_id=sub_id,
        kpis={k: KPI_REGISTRY[k] for k in kpi_ids}
    )


# -------------------------------------------------
# UPLOAD + RUN KPI (ADMIN ONLY)
# -------------------------------------------------
@app.route("/upload/<kpi_id>", methods=["GET", "POST"])
def upload(kpi_id):

    # Admin-only lock
    if session.get("role") != "admin":
        return render_template("access_denied.html"), 403

    if kpi_id not in KPI_REGISTRY:
        return "Invalid KPI", 404

    kpi = KPI_REGISTRY[kpi_id]

    # GET → upload page
    if request.method == "GET":
        return render_template("upload.html", kpi=kpi)

    # POST → run KPI
    dfs = []
    for f in kpi["files"]:
        file = request.files.get(f)
        if not file:
            return f"Missing file: {f}", 400
        dfs.append(load_excel(file))

    # Run logic
    module = importlib.import_module(f"logic.{kpi['module']}")
    func = getattr(module, kpi["function"])
    result = func(*dfs)

    summary, df = {}, None

    if isinstance(result, tuple) and len(result) == 2:
        summary, df = result
    elif isinstance(result, pd.DataFrame):
        df = result
    elif isinstance(result, dict):
        summary = result
    else:
        summary = {"Result": str(result)}

    if df is None:
        return "No tabular data produced", 400

    # Table column filter
    selected_columns = request.form.getlist("table_columns")
    df_table = df

    if selected_columns:
        valid_columns = [c for c in selected_columns if c in df.columns]
        if valid_columns:
            df_table = df[valid_columns]

    # Table HTML
    table_html = df_table.to_html(
        classes="table",
        index=False,
        border=0
    )

    # Charts
    charts = generate_charts(df, kpi.get("charts", []))

    # Format summary
    formatted_summary = {}
    for key, value in summary.items():
        key_lower = key.lower()
        if "%" in key_lower or "percent" in key_lower:
            formatted_summary[key] = format_number(value, "percent")
        elif "value" in key_lower or "amount" in key_lower:
            formatted_summary[key] = format_number(value, "currency")
        elif "item" in key_lower or "count" in key_lower or "total" in key_lower:
            formatted_summary[key] = format_number(value, "count")
        else:
            formatted_summary[key] = format_number(value)

    # SAVE KPI OUTPUT (CSV + XLSX + JSON)
    save_kpi_result(
        kpi_id=kpi_id,
        summary=formatted_summary,
        df=df_table,
        charts=charts
    )

    template_name = kpi.get("template", "dashboard.html")

    # ⭐ FIX #1 — Add kpi_id to template
    return render_template(
        template_name,
        kpi_id=kpi_id,
        label=kpi["label"],
        summary=formatted_summary,
        table_html=table_html,
        charts=charts
    )


# -------------------------------------------------
# VIEW KPI (USER)
# -------------------------------------------------
@app.route("/view/<kpi_id>")
def view_kpi(kpi_id):

    if kpi_id not in KPI_REGISTRY:
        return "Invalid KPI", 404

    summary, df, charts = load_kpi_result(kpi_id)

    if df is None:
        return "KPI not yet run by admin", 404

    kpi = KPI_REGISTRY[kpi_id]

    # ⭐ FIX #2 — Add kpi_id to template
    return render_template(
        kpi.get("template", "dashboard.html"),
        kpi_id=kpi_id,
        label=kpi["label"],
        summary=summary,
        table_html=df.to_html(classes="table", index=False),
        charts=charts
    )


# -------------------------------------------------
# DOWNLOAD EXCEL
# -------------------------------------------------
@app.route("/download/<kpi_id>")
def download_kpi_excel(kpi_id):

    from services.kpi_storage import SAVE_ROOT  # ensure import

    kpi_dir = os.path.join(SAVE_ROOT, kpi_id)
    excel_path = os.path.join(kpi_dir, "table.xlsx")

    if not os.path.exists(excel_path):
        return "Excel report not available", 404

    return send_file(
        excel_path,
        as_attachment=True,
        download_name=KPI_REGISTRY[kpi_id]["label"].replace(" ", "_") + ".xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
