import pandas as pd
import numpy as np


def run_component4(df_so_raw: pd.DataFrame, df_inv_raw: pd.DataFrame):
    """
    Component 4 — Sales Order → Invoice (O2C Cycle)
    ✔ Original notebook logic
    ✔ Only SLA bar chart
    ✔ Correct table output
    ✔ No app.py changes
    """

    # ---------------- COPY & CLEAN ----------------
    df_so = df_so_raw.copy()
    df_inv = df_inv_raw.copy()

    df_so.columns = df_so.columns.str.strip()
    df_inv.columns = df_inv.columns.str.strip()

    # ---------------- SALES ORDERS ----------------
    if "No." in df_so.columns:
        so_col = "No."
    elif "No" in df_so.columns:
        so_col = "No"
    elif "Document No." in df_so.columns:
        so_col = "Document No."
    else:
        raise KeyError(f"SO number column not found: {df_so.columns.tolist()}")

    df_so = df_so[[so_col, "Document Date", "Completely Shipped"]].copy()
    df_so.columns = ["SO_No", "SO_Date", "Completely_Shipped"]

    df_so["SO_No"] = df_so["SO_No"].astype(str).str.strip().str.upper()
    df_so["SO_Date"] = pd.to_datetime(df_so["SO_Date"], errors="coerce")
    df_so["Completely_Shipped"] = df_so["Completely_Shipped"].fillna(0).astype(int)

    df_so = df_so.dropna(subset=["SO_Date"])

    total_sos = len(df_so)
    shipped_sos = int(df_so["Completely_Shipped"].sum())
    shipment_pct = round((shipped_sos / total_sos) * 100, 2) if total_sos else 0

    # ---------------- INVOICES ----------------
    if "Order No." in df_inv.columns:
        inv_so_col = "Order No."
    elif "Order No" in df_inv.columns:
        inv_so_col = "Order No"
    else:
        raise KeyError(f"Invoice Order No column not found: {df_inv.columns.tolist()}")

    df_inv = df_inv[[inv_so_col, "Posting Date"]].copy()
    df_inv.columns = ["SO_No", "Invoice_Date"]

    df_inv["SO_No"] = df_inv["SO_No"].astype(str).str.strip().str.upper()
    df_inv["Invoice_Date"] = pd.to_datetime(df_inv["Invoice_Date"], errors="coerce")
    df_inv = df_inv.dropna(subset=["Invoice_Date"])

    # ---------------- O2C CALCULATION ----------------
    latest_invoice = (
        df_inv.groupby("SO_No")["Invoice_Date"]
        .max()
        .reset_index()
    )

    df_main = df_so.merge(latest_invoice, on="SO_No", how="inner")

    df_main["O2C Cycle Days"] = (
        df_main["Invoice_Date"] - df_main["SO_Date"]
    ).dt.days

    df_valid = df_main[
        (df_main["O2C Cycle Days"] >= 0) &
        (df_main["O2C Cycle Days"] <= 365)
    ].copy()

    # ---------------- METRICS (USED BY BAR CHART) ----------------
    metrics = {
        "total_sos": int(total_sos),
        "shipment_pct": shipment_pct,
        "avg_cycle": round(df_valid["O2C Cycle Days"].mean(), 2),
        "median_cycle": round(df_valid["O2C Cycle Days"].median(), 2),
        "pct_7": round((df_valid["O2C Cycle Days"] <= 7).mean() * 100, 2),
        "pct_14": round((df_valid["O2C Cycle Days"] <= 14).mean() * 100, 2),
        "pct_30": round((df_valid["O2C Cycle Days"] <= 30).mean() * 100, 2),
        "pct_60": round((df_valid["O2C Cycle Days"] <= 60).mean() * 100, 2),
        "p95_cycle": round(np.percentile(df_valid["O2C Cycle Days"], 95), 2)
    }
        # ---------------- SLA BAR DATA ----------------
    sla_df = pd.DataFrame({
        "Sales Order No": ["SLA", "SLA", "SLA", "SLA"],
        "Sales Order Date": [pd.NaT]*4,
        "Final Invoice Date": [pd.NaT]*4,
        "O2C Cycle Days": [np.nan]*4,
        "SLA Bucket": ["≤7 Days", "≤14 Days", "≤30 Days", "≤60 Days"],
        "SLA %": [
            metrics["pct_7"],
            metrics["pct_14"],
            metrics["pct_30"],
            metrics["pct_60"]
        ]
    })


    df_table = df_valid.rename(columns={
        "SO_No": "Sales Order No",
        "SO_Date": "Sales Order Date",
        "Invoice_Date": "Final Invoice Date"
    })
    df_table["SLA Bucket"] = ""
    df_table["SLA %"] = ""


    df_final = pd.concat([df_table, sla_df], ignore_index=True)

    # ---- Excel-safe formatting ----
    safe_df = df_final.copy()

    # Convert datetime columns to string
    for col in ["Sales Order Date", "Final Invoice Date"]:
        if col in safe_df.columns:
            safe_df[col] = safe_df[col].dt.strftime("%d-%m-%Y")

    # Replace NaN/NaT with empty strings
    safe_df = safe_df.replace({np.nan: "", pd.NaT: ""})

    # Ensure numeric column is string-safe
    # Ensure numeric column stays integer-safe
    if "O2C Cycle Days" in safe_df.columns:
        safe_df["O2C Cycle Days"] = pd.to_numeric(safe_df["O2C Cycle Days"], errors="coerce").astype("Int64")

        safe_df["O2C Cycle Days"] = safe_df["O2C Cycle Days"].replace("", "").astype(str)

    # Final return with Excel-safe dataframe
    return metrics, safe_df


