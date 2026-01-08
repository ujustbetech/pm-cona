import pandas as pd


def run_component7(df_item: pd.DataFrame, df_ledger: pd.DataFrame):
    """
    Component 7 — PM Stock Health
    Logic matches backup EXACTLY
    """

    # ---------- CLEAN ----------
    df_item = df_item.copy()
    df_ledger = df_ledger.copy()

    df_item.columns = df_item.columns.str.strip()
    df_ledger.columns = df_ledger.columns.str.strip()

    # ---------- RENAME ----------
    df_item = df_item.rename(columns={
        "No.": "Item_No",
        "Gen. Prod. Posting Group": "Product_Group"
    })

    df_ledger = df_ledger.rename(columns={
        "Item No.": "Item_No",
        "Remaining Quantity": "Remaining_Qty"
    })

    # =====================================================
    # CHANGE 1️⃣ — NORMALIZE DESCRIPTION (backup parity)
    # =====================================================
    df_ledger["Description"] = (
        df_ledger["Description"]
        .fillna("No Description")
        .astype(str)
        .str.strip()
    )

    # =====================================================
    # CHANGE 2️⃣ — PRESERVE FULL LEDGER (ALL ITEMS)
    # =====================================================
    full_ledger = df_ledger.copy()

    # ---------- PM ITEMS ONLY (CRITICAL) ----------
    pm_items = df_item[df_item["Product_Group"] == "PM"]["Item_No"].unique()
    df_ledger = df_ledger[df_ledger["Item_No"].isin(pm_items)]

    # ---------- AGGREGATE ITEM + LOCATION ----------
    df_ledger["Remaining_Qty"] = pd.to_numeric(
        df_ledger["Remaining_Qty"],
        errors="coerce"
    ).fillna(0)

    stock = (
        df_ledger
        .groupby(["Item_No", "Location Code"], as_index=False)
        .agg(Remaining_Qty=("Remaining_Qty", "sum"))
    )

    stock = stock[stock["Remaining_Qty"] > 0].copy()

    # ---------- STATUS BUCKET (UNCHANGED) ----------
    def stock_bucket(qty):
        if qty <= 50000:
            return "CRITICAL"
        elif qty <= 200000:
            return "MODERATE"
        else:
            return "HEALTHY"

    stock["Stock_Status"] = stock["Remaining_Qty"].apply(stock_bucket)

    # ---------- PIE DATA (SUMMARY ROWS) ----------
    pie_df = (
        stock
        .groupby("Stock_Status")
        .size()
        .reindex(["CRITICAL", "MODERATE", "HEALTHY"], fill_value=0)
        .reset_index(name="Count")
    )

    total = pie_df["Count"].sum()
    pie_df["Percentage"] = (pie_df["Count"] / total * 100).round(1)
    pie_df["row_type"] = "SUMMARY"

    # =====================================================
    # CHANGE 3️⃣ — DETAIL TABLE FROM *ALL ITEMS*
    # =====================================================
    detail_df = (
        full_ledger
        .groupby(
            ["Item_No", "Description", "Location Code"],
            as_index=False
        )
        .agg(Stock_Qty=("Remaining_Qty", "sum"))
    )

    detail_df = detail_df[detail_df["Stock_Qty"] > 0].copy()

    def stock_bucket_verbose(qty):
        if qty <= 50000:
            return "CRITICAL (Critical)"
        elif qty <= 200000:
            return "MODERATE (Moderate)"
        else:
            return "HEALTHY (Healthy)"

    detail_df["Status"] = detail_df["Stock_Qty"].apply(stock_bucket_verbose)
    detail_df["row_type"] = "DETAIL"

    # ---------- COMBINED OUTPUT ----------
    final_df = pd.concat(
        [pie_df, detail_df],
        ignore_index=True,
        sort=False
    )

    # ---------- SUMMARY ----------
    summary = {
        "Total_PM_Stock_Lines": int(total),
        "CRITICAL": int(pie_df.loc[pie_df["Stock_Status"] == "CRITICAL", "Count"].sum()),
        "MODERATE": int(pie_df.loc[pie_df["Stock_Status"] == "MODERATE", "Count"].sum()),
        "HEALTHY": int(pie_df.loc[pie_df["Stock_Status"] == "HEALTHY", "Count"].sum()),
    }

    return summary, final_df
