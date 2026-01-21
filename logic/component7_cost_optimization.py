import pandas as pd
import inspect

def run_component7(
    df_item: pd.DataFrame,
    df_ledger: pd.DataFrame,
    product_group_filter="PM"   # Default fallback
):
    """
    Component 7 — Stock Health (PM or ALL based on filter)
    Uses KPI_REGISTRY['filter'] automatically without any app.py changes.
    """

    # =====================================================
    # ⭐ AUTO-DETECT FILTER BASED ON KPI METADATA
    # =====================================================
    caller_frame = inspect.stack()[1]
    kpi_context = caller_frame.frame.f_locals.get("kpi", {})

    if isinstance(kpi_context, dict) and "filter" in kpi_context:
        product_group_filter = kpi_context["filter"]

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
    # CHANGE 1 — NORMALIZE DESCRIPTION
    # =====================================================
    df_ledger["Description"] = (
        df_ledger["Description"]
        .fillna("No Description")
        .astype(str)
        .str.strip()
    )

    # =====================================================
    # CHANGE 2 — PRESERVE FULL LEDGER FOR DETAIL TABLE
    # =====================================================
    full_ledger = df_ledger.copy()

    # =====================================================
    # ⭐ CONDITIONAL FILTERING LOGIC (PM or ALL)
    # =====================================================
    if product_group_filter:    # PM mode
        selected_items = df_item[
            df_item["Product_Group"] == product_group_filter
        ]["Item_No"].unique()

        # Apply filter to main ledger
        df_ledger = df_ledger[df_ledger["Item_No"].isin(selected_items)]

        # ⭐ ALSO FILTER FULL LEDGER FOR DETAIL TABLE
        full_ledger = full_ledger[full_ledger["Item_No"].isin(selected_items)]

    # Else: ALL stock KPI → do nothing

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

    # ---------- STATUS BUCKET ----------
    def stock_bucket(qty):
        if qty <= 50000:
            return "< 50,000"
        elif qty <= 200000:
            return "50,000 - 200,000"
        else:
            return "> 200,000"

    stock["Stock_Status"] = stock["Remaining_Qty"].apply(stock_bucket)

    # ---------- PIE DATA ----------
    pie_df = (
        stock
        .groupby("Stock_Status")
        .size()
        .reindex(["< 50,000", "50,000 - 200,000", "> 200,000"], fill_value=0)
        .reset_index(name="Count")
    )

    total = pie_df["Count"].sum()
    pie_df["Percentage"] = (pie_df["Count"] / total * 100).round(1)
    pie_df["row_type"] = "SUMMARY"

    # =====================================================
    # DETAIL TABLE (NOW FILTERED CORRECTLY)
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
            return "< 50,000"
        elif qty <= 200000:
            return "50,000 - 200,000"
        else:
            return "> 200,000"

    detail_df["Status"] = detail_df["Stock_Qty"].apply(stock_bucket_verbose)
    detail_df["row_type"] = "DETAIL"

    # ---------- FORMAT Stock_Qty ----------
    detail_df["Stock_Qty"] = detail_df["Stock_Qty"].apply(
        lambda x: f"{int(x):,}" if pd.notna(x) else ""
    )

    # ---------- COMBINED OUTPUT ----------
    final_df = pd.concat(
        [pie_df, detail_df],
        ignore_index=True,
        sort=False
    )

    # ---------- SUMMARY ----------
    summary = {
        "Total_PM_Stock_Lines": int(total),
        "< 50,000": int(pie_df.loc[pie_df["Stock_Status"] == "< 50,000", "Count"].sum()),
        "50,000 - 200,000": int(pie_df.loc[pie_df["Stock_Status"] == "50,000 - 200,000", "Count"].sum()),
        "> 200,000": int(pie_df.loc[pie_df["Stock_Status"] == "> 200,000", "Count"].sum()),
    }

    return summary, final_df
