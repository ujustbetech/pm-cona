import pandas as pd

SLA_DAYS = 15   # keep configurable


def run_component3a(df_po: pd.DataFrame,
                    df_rcpt: pd.DataFrame,
                    df_lines: pd.DataFrame):
    """
    Component 3A — Vendor On-Time Delivery Performance
    Bucketing aligned EXACTLY with backup logic (PO completion rate)
    """

    # ---------------- CLEAN COLUMN NAMES ----------------
    df_po = df_po.copy()
    df_rcpt = df_rcpt.copy()
    df_lines = df_lines.copy()

    for df in [df_po, df_rcpt, df_lines]:
        df.columns = df.columns.str.strip()

    # ---------------- PURCHASE ORDER ----------------
    df_po = df_po.rename(columns={
        "No.": "PO_No",
        "Pay-to Name": "Vendor",
        "Order Date": "Order_Date",
        "Last Receiving No.": "Last_Receiving_No"
    })

    df_po = df_po[[
        "PO_No",
        "Vendor",
        "Order_Date",
        "Last_Receiving_No"
    ]]

    df_po["Order_Date"] = pd.to_datetime(
        df_po["Order_Date"], errors="coerce"
    )

    # ---------------- PURCHASE LINES (COMPLETION CHECK) ----------------
    df_lines = df_lines.rename(columns={
        "Document No.": "PO_No",
        "Outstanding Quantity": "Outstanding_Qty"
    })

    df_lines["Outstanding_Qty"] = pd.to_numeric(
        df_lines["Outstanding_Qty"], errors="coerce"
    ).fillna(0)

    po_completion = (
        df_lines
        .groupby("PO_No")["Outstanding_Qty"]
        .sum()
    )

    completed_po_nos = po_completion[po_completion == 0].index

    # ---------------- RECEIPT DATE ----------------
    df_rcpt = df_rcpt.rename(columns={
        "No.": "Receipt_No",
        "Posting Date": "Posting_Date"
    })

    df_rcpt["Posting_Date"] = pd.to_datetime(
        df_rcpt["Posting_Date"], errors="coerce"
    )

    receipt_dates = df_rcpt[[
        "Receipt_No",
        "Posting_Date"
    ]]

    # ---------------- MERGE (FOR DELIVERY METRICS ONLY) ----------------
    df = (
        df_po
        .merge(
            pd.DataFrame({"PO_No": completed_po_nos}),
            on="PO_No",
            how="inner"
        )
        .merge(
            receipt_dates,
            left_on="Last_Receiving_No",
            right_on="Receipt_No",
            how="left"
        )
    )

    df = df.dropna(subset=["Order_Date", "Posting_Date"])

    # ---------------- DELIVERY DAYS ----------------
    df["Delivery_Days"] = (
        df["Posting_Date"] - df["Order_Date"]
    ).dt.days

    df = df[df["Delivery_Days"] >= 0]

    # ---------------- ON-TIME FLAG (≤15 DAYS) ----------------
    df["On_Time"] = df["Delivery_Days"] <= SLA_DAYS

    # ---------------- VENDOR KPI (UNCHANGED) ----------------
    vendor_kpi = (
        df.groupby("Vendor")
        .agg(
            Total_POs=("PO_No", "count"),
            On_Time_POs=("On_Time", "sum")
        )
        .reset_index()
    )

    vendor_kpi["Late_POs"] = (
        vendor_kpi["Total_POs"] - vendor_kpi["On_Time_POs"]
    )

    vendor_kpi["On_Time_Pct"] = round(
        (vendor_kpi["On_Time_POs"] /
         vendor_kpi["Total_POs"]) * 100,
        2
    )

    # =====================================================
    # ✅ ONLY CHANGE STARTS HERE — BUCKETING LOGIC
    # =====================================================

    # === BACKUP-ALIGNED COMPLETION UNIVERSE ===
    valid_pos = df_po[df_po["PO_No"].isin(df_lines["PO_No"].unique())]

    total_pos_vendor = (
        valid_pos.groupby("Vendor")["PO_No"]
        .nunique()
    )

    completed_pos_vendor = (
        valid_pos[valid_pos["PO_No"].isin(completed_po_nos)]
        .groupby("Vendor")["PO_No"]
        .nunique()
    )

    completion_rate = (
        completed_pos_vendor / total_pos_vendor * 100
    ).round(2).fillna(0)


    completion_rate = (
        completed_pos_vendor / total_pos_vendor * 100
    ).round(2).fillna(0)

    def bucket_performance(pct):
        if pct == 100:
            return '100%'
        elif pct >= 90:
            return '90–99%'
        elif pct >= 80:
            return '80–89%'
        elif pct >= 70:
            return '70–79%'
        else:
            return '<70%'

    buckets = completion_rate.reset_index(name="Completion_Pct")
    buckets["Bucket"] = buckets["Completion_Pct"].apply(bucket_performance)

    bucket_summary = (
        buckets["Bucket"]
        .value_counts()
        .reindex(['100%', '90–99%', '80–89%', '70–79%', '<70%'], fill_value=0)
        .reset_index()
    )
    bucket_summary.columns = ["Bucket", "Vendor Count"]
    # ---------------- ADD BUCKET ROWS FOR CHART ENGINE ----------------
    bucket_rows = bucket_summary.copy()

    bucket_rows["Vendor"] = bucket_rows["Bucket"]
    bucket_rows["Total_POs"] = None
    bucket_rows["On_Time_POs"] = None
    bucket_rows["Late_POs"] = None
    bucket_rows["On_Time_Pct"] = None
    bucket_rows["Performance_Bucket"] = bucket_rows["Bucket"]

    # Align column order
    # ---------------- ADD BUCKET ROWS FOR CHART ENGINE ----------------
    bucket_rows = bucket_summary.copy()

    # Add all vendor columns with NaN
    bucket_rows["Vendor"] = None
    bucket_rows["Total_POs"] = None
    bucket_rows["On_Time_POs"] = None
    bucket_rows["Late_POs"] = None
    bucket_rows["On_Time_Pct"] = None
    bucket_rows["Performance_Bucket"] = bucket_rows["Bucket"]

    # Keep Bucket + Vendor_Count intact
    final_df = pd.concat(
        [vendor_kpi, bucket_rows],
        ignore_index=True,
        sort=False
    )



    # =====================================================
    # ✅ ONLY CHANGE ENDS HERE
    # =====================================================

    # ---------------- OVERALL METRICS (UNCHANGED) ----------------
    metrics = {
        "Total_Completed_POs": int(len(df)),
        "Overall_On_Time_Pct": round(
            (df["On_Time"].sum() / len(df)) * 100,
            2
        ) if len(df) else 0,
        "Vendors_Below_95": int(
            (vendor_kpi["On_Time_Pct"] < 95).sum()
        ),
        "Total_On_Time_POs": int(vendor_kpi["On_Time_POs"].sum()),
        "Total_Late_POs": int(vendor_kpi["Late_POs"].sum())
    }
        # ---------------- TABLE VISUAL FIX (NO app.py CHANGE) ----------------
        # ---------------- TABLE VISUAL FIX (NO app.py CHANGE) ----------------
    table_df = final_df.copy()
    int_cols = ["Total_POs", "On_Time_POs", "Late_POs"]

    for col in int_cols:
        if col in table_df.columns:
            # Convert vendor rows to proper int
            table_df.loc[table_df["Vendor"].notna(), col] = (
                table_df.loc[table_df["Vendor"].notna(), col]
                .astype("Int64")
            )
            # Bucket rows stay blank
            table_df.loc[table_df["Vendor"].isna(), col] = ""

    # Hide bucket-only columns for vendor rows (visual cleanliness)
    mask_vendor_rows = table_df["Vendor"].notna()

    for col in ["Bucket", "Vendor Count", "Performance_Bucket"]:
        if col in table_df.columns:
            table_df.loc[mask_vendor_rows, col] = None

    return metrics, table_df




