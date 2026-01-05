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

from registry.hierarchy import DEPARTMENTS
from registry.kpis import KPI_REGISTRY
from services.excel_loader import load_excel
from services.chart_engine import generate_charts
from services.formatters import format_number



# -------------------------------------------------
# APP INIT
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

    # ✅ SAFE TEMP DIRECTORY (WORKS ON WINDOWS, PYTHONANYWHERE, LINUX)
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
        session["user"] = request.form["username"]
        return redirect(url_for("departments"))
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


# UPLOAD + RUN KPI  (FIXED)
# -------------------------------------------------
@app.route("/upload/<kpi_id>", methods=["GET", "POST"])
def upload(kpi_id):
    if kpi_id not in KPI_REGISTRY:
        return "Invalid KPI", 404

    kpi = KPI_REGISTRY[kpi_id]

    # ---------- GET ----------
    if request.method == "GET":
        return render_template("upload.html", kpi=kpi)

    # ---------- POST ----------
    dfs = []
    for f in kpi["files"]:
        file = request.files.get(f)
        if not file:
            return f"Missing file: {f}", 400
        dfs.append(load_excel(file))

    # Run KPI logic
    module = importlib.import_module(f"logic.{kpi['module']}")
    func = getattr(module, kpi["function"])
    result = func(*dfs)

    summary = {}
    df = None
    table_html = None
    charts = {}

    # ---------- NORMALIZE RESULT ----------
    if isinstance(result, tuple) and len(result) == 2:
        summary, df = result
    elif isinstance(result, pd.DataFrame):
        df = result
    elif isinstance(result, dict):
        summary = result
    else:
        summary = {"Result": str(result)}

    # ---------- TABLE + CHARTS ----------
    if df is not None:
        table_html = df.to_html(
            classes="table",
            index=False,
            border=0
        )

        charts = generate_charts(df, kpi.get("charts", []))


        # 🔥 SAFE TEMP FILE STORAGE (NO SESSION BLOAT)
        report_id = str(uuid.uuid4())
        report_path = os.path.join(TMP_DIR, f"{report_id}.csv")
        df.to_csv(report_path, index=False)

        

        session["report_path"] = report_path

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


    return render_template(
        "dashboard.html",
        label=kpi["label"],
        summary=formatted_summary,
        table_html=table_html,
        charts=charts
    )



# -------------------------------------------------
# DOWNLOAD REPORT
# -------------------------------------------------
@app.route("/download-report")
def download_report():
    report_path = session.get("report_path")

    if not report_path or not os.path.exists(report_path):
        return "No report available", 400

    return send_file(
        report_path,
        as_attachment=True,
        download_name="pm_cona_kpi_report.csv",
        mimetype="text/csv"
    )


# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
