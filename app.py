from flask import (
    Flask, render_template, request,
    redirect, url_for, session, send_file
)
import importlib
import pandas as pd
import io
import os
import sys

from registry.hierarchy import DEPARTMENTS
from registry.kpis import KPI_REGISTRY
from services.excel_loader import load_excel
from services.chart_engine import generate_charts


# -------------------------------------------------
# APP INIT
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

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


# -------------------------------------------------
# UPLOAD + RUN KPI
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

    # ---------------- NORMALIZE OUTPUT ----------------
    summary = {}
    df = None
    table_html = None
    charts = {}

    # Case 1: (summary, df)
    if isinstance(result, tuple) and len(result) == 2:
        raw_summary, df = result

    # Case 2: only DataFrame
    elif isinstance(result, pd.DataFrame):
        df = result
        raw_summary = {}

    # Case 3: only dict
    elif isinstance(result, dict):
        raw_summary = result
        df = None

    # Case 4: fallback
    else:
        raw_summary = {"Result": result}
        df = None

    # Ensure summary is dict
    if isinstance(raw_summary, dict):
        summary = raw_summary
    elif isinstance(raw_summary, (list, tuple)):
        summary = {f"Metric {i+1}": v for i, v in enumerate(raw_summary)}
    else:
        summary = {"Value": raw_summary}

    # Table + charts
    if df is not None:
        session["last_df"] = df.to_json()

        table_html = df.to_html(
            classes="table",
            index=False,
            border=0
        )

        charts = generate_charts(df)

    return render_template(
        "dashboard.html",
        label=kpi["label"],
        summary=summary,
        table_html=table_html,
        charts=charts
    )


# -------------------------------------------------
# DOWNLOAD REPORT
# -------------------------------------------------
@app.route("/download-report")
def download_report():
    if "last_df" not in session:
        return "No report available", 400

    df = pd.read_json(session["last_df"])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")

    output.seek(0)

    return send_file(
        output,
        download_name="pm_cona_kpi_report.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
