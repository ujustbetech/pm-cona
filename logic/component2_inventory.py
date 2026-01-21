import pandas as pd
import numpy as np
from datetime import datetime


def run_component2(df: pd.DataFrame):
    """
    Component 2 — Inventory Dormancy Analysis
    Serverless-safe (Vercel compatible)
    Logic preserved exactly from original version
    """

    # ----------------------------
    # COPY & CLEAN COLUMN NAMES
    # ----------------------------
    df = df.copy()
    df.columns = df.columns.str.strip()

    # ----------------------------
    # REQUIRED COLUMNS
    # ----------------------------
    required_cols = [
        "Item No.",
        "Location Code",
        "Posting Date",
        "Quantity",
        "Remaining Quantity",
        "Cost Amount (Actual)",
        "Description",
        "Item Category Code",
        "Item Subcategory Code"
    ]

    df = df[required_cols]

    # ----------------------------
    # TYPE CLEANING (ADD ROBUST DATE PARSING LIKE BACKUP)
    # ----------------------------
    def to_date(val):
        if pd.isna(val):
            return pd.NaT
        if isinstance(val, (int, float)):
            try:
                return pd.to_datetime(val, unit='D', origin='1899-12-30')
            except:
                return pd.NaT
        return pd.to_datetime(val, errors='coerce', dayfirst=True)

    df["Posting Date"] = df["Posting Date"].apply(to_date)

    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Remaining Quantity"] = pd.to_numeric(
        df["Remaining Quantity"], errors="coerce"
    ).fillna(0)

    df["Cost Amount (Actual)"] = pd.to_numeric(
        df["Cost Amount (Actual)"], errors="coerce"
    ).fillna(0)

    df["Location Code"] = (
        df["Location Code"]
        .astype(str)
        .str.strip()
        .replace("nan", "UNKNOWN")
    )

    today = pd.Timestamp(datetime.now().date())

    # ----------------------------
    # LAST OUTWARD DATE
    # ----------------------------
    last_outward = (
        df[df["Quantity"] < 0]
        .groupby(["Item No.", "Location Code"])["Posting Date"]
        .max()
        .reset_index()
        .rename(columns={"Posting Date": "Last Outward Date"})
    )

    # ----------------------------
    # CURRENT STOCK ONLY
    # ----------------------------
    current_stock = (
        df[df["Remaining Quantity"] > 0]
        .groupby(["Item No.", "Location Code"])
        .agg(
            Description=("Description", "first"),
            Category=("Item Category Code", "first"),
            Subcategory=("Item Subcategory Code", "first"),
            On_Hand=("Remaining Quantity", "sum"),
            Stock_Value=("Cost Amount (Actual)", "sum"),
        )
        .reset_index()
    )

    # ----------------------------
    # MERGE & DORMANCY
    # ----------------------------
    result = current_stock.merge(
        last_outward,
        on=["Item No.", "Location Code"],
        how="left"
    )

    result["Days Dormant"] = np.where(
        result["Last Outward Date"].notna(),
        (today - pd.to_datetime(result["Last Outward Date"])).dt.days,
        np.nan
    )

    # ----------------------------
    # STATUS CLASSIFICATION (UNCHANGED)
    # ----------------------------
    result["Status"] = "Active"

    result.loc[result["Days Dormant"] > 60, "Status"] = "Slow-Moving"
    result.loc[result["Days Dormant"] > 365, "Status"] = "Dead"

    result.loc[
        result["Last Outward Date"].isna() & (result["On_Hand"] > 0),
        "Status"
    ] = "Dead"

    result["Days Dormant Display"] = result["Days Dormant"].fillna("Never Moved")

    # ----------------------------
    # KPI SUMMARY (PRE-AGGREGATE VALUE % FOR CHART)
    # ----------------------------
    status_value = result.groupby('Status')['Stock_Value'].sum()
    total_value = status_value.sum()

    summary = {
        "Total Items": len(result),
        "Active Items": int((result["Status"] == "Active").sum()),
        "Slow-Moving Items": int((result["Status"] == "Slow-Moving").sum()),
        "Dead Items": int((result["Status"] == "Dead").sum()),
        "Total Value": total_value,
        "Active Value": status_value.get("Active", 0),
        "Slow-Moving Value": status_value.get("Slow-Moving", 0),
        "Dead Value": status_value.get("Dead", 0),
        "Active %": round(status_value.get("Active", 0) / total_value * 100, 1) if total_value else 0,
        "Slow-Moving %": round(status_value.get("Slow-Moving", 0) / total_value * 100, 1) if total_value else 0,
        "Dead %": round(status_value.get("Dead", 0) / total_value * 100, 1) if total_value else 0,
    }

    # # NEW: Pre-aggregated DataFrame for value-based donut (alternative to engine support)
    # # Create one row per status, with 'weight' = % value (engine will "count" these for proportions)
    # agg_data = {
    #     'Status': ['Active', 'Slow-Moving', 'Dead'],
    #     'Weight': [summary["Active %"], summary["Slow-Moving %"], summary["Dead %"]]  # Proportions as "counts"
    # }
    # agg_df = pd.DataFrame(agg_data)
    # # Append to result (engine will use this for donut on 'Status', summing/counting Weight implicitly via row proportions)
    # result = pd.concat([result, agg_df], ignore_index=True)
    

    result["On_Hand"] = result["On_Hand"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "")
    # -------------------- DATE FORMATTING FOR DASHBOARD --------------------
    date_col = "Last Outward Date"

    # Convert to datetime safely
    result[date_col] = pd.to_datetime(result[date_col], errors="coerce")

    # Format to dd-mm-yyyy, NaT stays NaT temporarily
    result[date_col] = result[date_col].dt.strftime("%d-%m-%Y")

    # Replace all missing patterns
    result[date_col] = result[date_col].replace(["NaT", "nan", "NaN", "", None, np.nan], "Never Moved")



    return summary, result