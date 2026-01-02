import plotly.express as px

def generate_charts(df):
    charts = {}

    if df is None or df.empty:
        return charts

    cols = df.columns.str.lower()

    # -------------------------------
    # 1️⃣ Percentage Gauge / Donut
    # -------------------------------
    pct_cols = [c for c in df.columns if "pct" in c.lower() or "percent" in c.lower()]
    if pct_cols:
        pct_col = pct_cols[0]
        value = df[pct_col].mean()

        fig = px.pie(
            values=[value, 100 - value],
            names=["Achieved", "Remaining"],
            hole=0.6,
            title=pct_col.replace("_", " ").title()
        )

        charts["Performance %"] = fig.to_html(full_html=False)

    # -------------------------------
    # 2️⃣ Categorical vs Numeric Bar
    # -------------------------------
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    num_cols = df.select_dtypes(include="number").columns.tolist()

    if cat_cols and num_cols:
        fig = px.bar(
            df.head(20),
            x=cat_cols[0],
            y=num_cols[0],
            title=f"{num_cols[0]} by {cat_cols[0]}"
        )
        charts["Distribution"] = fig.to_html(full_html=False)

    # -------------------------------
    # 3️⃣ Time Trend (if Month/Date)
    # -------------------------------
    time_cols = [c for c in df.columns if "month" in c.lower() or "date" in c.lower()]
    if time_cols and num_cols:
        fig = px.line(
            df,
            x=time_cols[0],
            y=num_cols[0],
            title=f"{num_cols[0]} Trend"
        )
        charts["Trend"] = fig.to_html(full_html=False)

    return charts
