import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_ROOT = os.path.join(BASE_DIR, "..", "saved_kpis")


def save_kpi_result(kpi_id, summary, df, charts):
    kpi_dir = os.path.join(SAVE_ROOT, kpi_id)
    os.makedirs(kpi_dir, exist_ok=True)

    # Save summary
    with open(os.path.join(kpi_dir, "summary.json"), "w") as f:
        json.dump(summary, f)

    # Save charts
    with open(os.path.join(kpi_dir, "charts.json"), "w") as f:
        json.dump(charts, f)

    # Save table as CSV
    df.to_csv(os.path.join(kpi_dir, "table.csv"), index=False)

    # ⭐ Save table as Excel (for download)
    df.to_excel(os.path.join(kpi_dir, "table.xlsx"), index=False)


def load_kpi_result(kpi_id):
    kpi_dir = os.path.join(SAVE_ROOT, kpi_id)

    if not os.path.exists(kpi_dir):
        return None, None, None

    with open(os.path.join(kpi_dir, "summary.json")) as f:
        summary = json.load(f)

    with open(os.path.join(kpi_dir, "charts.json")) as f:
        charts = json.load(f)

    df = pd.read_csv(os.path.join(kpi_dir, "table.csv"))

    return summary, df, charts
