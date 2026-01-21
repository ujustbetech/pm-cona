import pandas as pd

def run_component5a_rm(
    df_items: pd.DataFrame,
    df_po: pd.DataFrame,
    df_receipts: pd.DataFrame,
    df_lines: pd.DataFrame
):
    """
    Component 5A — RM Purchase Order SLA
    Matches backup code: same-quarter On-Time, completion on all lines
    """

    # COPY & CLEAN
    df_items = df_items.copy()
    df_po = df_po.copy()
    df_receipts = df_receipts.copy()
    df_lines = df_lines.copy()

    for df in [df_items, df_po, df_receipts, df_lines]:
        df.columns = df.columns.str.strip()

    # 1. GET TRUE RM ITEM CODES
    df_items = df_items.rename(columns={
        "No.": "Item_No",
        "Inventory Posting Group": "Posting_Group"
    })

    rm_items = (
        df_items[df_items["Posting_Group"] == "RM"]["Item_No"]
        .astype(str)
        .str.strip()
        .unique()
    )

    rm_items_set = set(rm_items)

    # 2. FIND POs THAT CONTAIN AT LEAST ONE RM ITEM
    df_lines = df_lines.rename(columns={
        "Document No.": "PO_No",
        "No.": "Item_No",
        "Outstanding Quantity": "Outstanding_Qty"
    })

    df_lines["PO_No"] = df_lines["PO_No"].astype(str).str.strip().str.upper()
    df_lines["Item_No"] = df_lines["Item_No"].astype(str).str.strip()
    df_lines["Outstanding_Qty"] = pd.to_numeric(
        df_lines["Outstanding_Qty"], errors="coerce"
    ).fillna(0)

    rm_po_list = (
        df_lines[df_lines["Item_No"].isin(rm_items_set)]["PO_No"]
        .unique()
        .tolist()
    )

    if not rm_po_list:
        metrics = {"Total_RM_POs": 0, "On_Time_POs": 0, "Late_POs": 0, "On_Time_Pct": 0.0}
        table_df = pd.DataFrame(columns=["PO_No", "Vendor", "Order_Date", "Last_Receipt_Date",
                                        "Days_To_Receive", "Order_Quarter", "On_Time"])
        return metrics, table_df

    # 3. PURCHASE ORDER MASTER (RM ONLY)
    df_po = df_po.rename(columns={
        "No.": "PO_No",
        "Buy-from Vendor Name": "Vendor",
        "Order Date": "Order_Date",
        "Last Receiving No.": "Last_Receiving_No"
    })

    df_po["PO_No"] = df_po["PO_No"].astype(str).str.strip().str.upper()
    df_po["Last_Receiving_No"] = df_po["Last_Receiving_No"].fillna('').astype(str).str.strip().str.upper()
    df_po["Vendor"] = df_po["Vendor"].fillna("Unknown")

    # Robust Excel date parsing (with dayfirst=True to match backup)
    def to_date(val):
        if pd.isna(val):
            return pd.NaT
        if isinstance(val, (int, float)):
            try:
                return pd.to_datetime(val, unit='D', origin='1899-12-30')
            except:
                return pd.NaT
        return pd.to_datetime(val, errors='coerce', dayfirst=True)

    df_po["Order_Date"] = df_po["Order_Date"].apply(to_date)
    df_po = df_po.dropna(subset=["Order_Date"])

    # Filter to POs containing RM items
    df_po = df_po[df_po["PO_No"].isin(rm_po_list)].copy()

    # 4. COMPLETION CHECK (ALL LINES — MATCH BACKUP LOGIC)
    po_completion = df_lines.groupby("PO_No")["Outstanding_Qty"].sum()
    completed_pos = po_completion[po_completion == 0].index.tolist()

    df_po = df_po[df_po["PO_No"].isin(completed_pos)]

    if df_po.empty:
        metrics = {"Total_RM_POs": 0, "On_Time_POs": 0, "Late_POs": 0, "On_Time_Pct": 0.0}
        table_df = pd.DataFrame(columns=["PO_No", "Vendor", "Order_Date", "Last_Receipt_Date",
                                        "Days_To_Receive", "Order_Quarter", "On_Time"])
        return metrics, table_df

    # 5. RECEIPT DATE MAPPING
    df_receipts = df_receipts.rename(columns={
        "No.": "Receipt_No",
        "Posting Date": "Posting_Date"
    })

    df_receipts["Receipt_No"] = df_receipts["Receipt_No"].astype(str).str.strip().str.upper()
    df_receipts["Posting_Date"] = df_receipts["Posting_Date"].apply(to_date)

    receipt_map = dict(zip(df_receipts["Receipt_No"], df_receipts["Posting_Date"]))
    df_po["Receipt_Date"] = df_po["Last_Receiving_No"].map(receipt_map)

    # 6. SLA: SAME QUARTER AS ORDER (MATCH BACKUP)
    df_po["Days_To_Receive"] = (df_po["Receipt_Date"] - df_po["Order_Date"]).dt.days

    df_po = df_po[
        df_po["Receipt_Date"].notna() &
        (df_po["Days_To_Receive"] >= 0)
    ].copy()

    if df_po.empty:
        metrics = {"Total_RM_POs": 0, "On_Time_POs": 0, "Late_POs": 0, "On_Time_Pct": 0.0}
        table_df = pd.DataFrame(columns=["PO_No", "Vendor", "Order_Date", "Last_Receipt_Date",
                                        "Days_To_Receive", "Order_Quarter", "On_Time"])
        return metrics, table_df

    # Same-quarter logic (exact match to backup)
    df_po["Order_Quarter"] = df_po["Order_Date"].dt.to_period("Q")
    df_po["Receipt_Quarter"] = df_po["Receipt_Date"].dt.to_period("Q")
    df_po["SLA_Status"] = (df_po["Receipt_Quarter"] == df_po["Order_Quarter"]).map({
        True: "On-Time",
        False: "Late"
    })

    df_po["Quarter"] = df_po["Order_Date"].dt.to_period("Q").astype(str)
    df_po["Month"] = df_po["Order_Date"].dt.to_period("M").astype(str)

    # 8. PERIOD SUMMARY
    summary = (
        df_po.groupby(["Month", "Quarter", "SLA_Status"])
        .size()
        .reset_index(name="PO_Count")
    )

    total_per_period = (
        summary.groupby(["Month", "Quarter"])["PO_Count"]
        .sum()
        .reset_index(name="Total_POs")
    )

    on_time_per_period = (
        summary[summary["SLA_Status"] == "On-Time"]
        .groupby(["Month", "Quarter"])["PO_Count"]
        .sum()
        .reset_index(name="On_Time_POs")
    )

    df_period = total_per_period.merge(on_time_per_period, on=["Month", "Quarter"], how="left").fillna(0)
    df_period["Within_SLA_Pct"] = (df_period["On_Time_POs"] / df_period["Total_POs"] * 100).round(2)

    df_final = df_po.merge(df_period[["Month", "Quarter", "Within_SLA_Pct"]], on=["Month", "Quarter"], how="left")

    # 9. OVERALL METRICS
    overall_total = len(df_po)
    overall_on_time = len(df_po[df_po["SLA_Status"] == "On-Time"])

    metrics = {
        "Total_RM_POs": int(overall_total),
        "On_Time_POs": int(overall_on_time),
        "Late_POs": int(overall_total - overall_on_time),
        "On_Time_Pct": round((overall_on_time / overall_total) * 100, 2) if overall_total else 0.0
    }

    # 10. TABLE VIEW
    table_df = df_final[[
        "PO_No", "Vendor", "Order_Date", "Receipt_Date",
        "Days_To_Receive", "Quarter", "SLA_Status"
    ]].copy()

    table_df = table_df.rename(columns={
        "Receipt_Date": "Last_Receipt_Date",
        "Quarter": "Order_Quarter",
        "SLA_Status": "On_Time"  # "On-Time" or "Late"
    })

    # Convert Excel-unsafe types
    if "Order_Quarter" in table_df.columns:
        table_df["Order_Quarter"] = table_df["Order_Quarter"].astype(str)

    if "Order_Date" in table_df.columns:
        table_df["Order_Date"] = table_df["Order_Date"].dt.strftime("%d-%m-%Y")

    if "Last_Receipt_Date" in table_df.columns:
        table_df["Last_Receipt_Date"] = table_df["Last_Receipt_Date"].dt.strftime("%d-%m-%Y")


    return metrics, table_df