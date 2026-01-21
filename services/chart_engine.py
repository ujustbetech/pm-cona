import plotly.express as px
import plotly.io as pio


def generate_charts(df, chart_configs):
    charts = {}

    for i, cfg in enumerate(chart_configs):
        chart_type = cfg["type"]
        title = cfg.get("title", "")

        # -------------------------------------------------
        # DONUT CHART (CATEGORY BASED)
        # -------------------------------------------------
        if chart_type == "donut":
            color_map = cfg.get("colors")
            
            fig = px.pie(
                df,
                names=cfg["column"],
                hole=0.55,
                title=title
            )

            fig.update_traces(
                domain=dict(x=[0.0, 0.45]),
                textinfo="percent+label",
                textposition="outside",
                pull=[0.02] * len(df)
            )

            fig.update_layout(
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=0.7
                ),
                margin=dict(t=60, b=20, l=20, r=120)
            )
        # -------------------------------------------------
# DONUT VALUE CHART (VALUE BASED)
# -------------------------------------------------
        elif chart_type == "donut_value":
            fig = px.pie(
                df,
                names=cfg["column"],
                values=df[cfg["value"]],
                hole=0.55,
                title=title
            )

            fig.update_traces(
                domain=dict(x=[0.0, 0.45]),
                textinfo="percent+label",
                textposition="outside",
                pull=[0.02] * len(df)
            )

            fig.update_layout(
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=0.7
                ),
                margin=dict(t=60, b=20, l=20, r=120)
            )


        # -------------------------------------------------
        # BAR CHART
        # -------------------------------------------------
        elif chart_type == "bar":
            fig = px.bar(
                df,
                x=cfg["x"],
                y=cfg["y"],
                title=title
            )

        # -------------------------------------------------
        # STACKED BAR CHART
        # -------------------------------------------------
        elif chart_type == "stacked_bar":
            fig = px.bar(
                df,
                x=cfg["x"],
                color=cfg["color"],
                title=title
            )

        # -------------------------------------------------
        # DONUT SUMMARY (AGGREGATED COUNTS)
        # -------------------------------------------------
        elif chart_type == "donut_summary":
            fig = px.pie(
                names=cfg["labels"],
                values=[
                    df[cfg["values"][0]].sum(),
                    df[cfg["values"][1]].sum()
                ],
                hole=0.55,
                title=title
            )

            fig.update_traces(
                 domain=dict(x=[0.0, 0.45]),
                textinfo="percent+label",
                textposition="outside"
            )

            fig.update_layout(
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=0.5
                ),
                margin=dict(t=60, b=20, l=20, r=120)
            )
       # -------------------------------------------------
# DONUT VALUE (SMALL LABELS – Component-specific)
# -------------------------------------------------
        elif chart_type == "donut_value_smalllabels":
                # ✔ FIX: Use only summary rows if present
            if "row_type" in df.columns:
                df = df[df["row_type"] == "SUMMARY"]

            fig = px.pie(
                df,
                names=cfg["column"],
                values=df[cfg["value"]],
                hole=0.55,
                title=title
            )

            fig.update_traces(
                domain=dict(x=[0.15, 0.85]),
                textinfo="percent+label",
                textposition="outside",
                textfont_size=10,   # SMALLER LABELS = FIXES OVERLAP
                pull=[0.02] * len(df)
            )

            fig.update_layout(
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=0.7
                ),
                margin=dict(t=60, b=20, l=20, r=120)
            )
        
        elif chart_type == "bar_horizontal":
            fig = px.bar(
            df,
            x="Percentage",
            y="Stock_Status",
            text="Percentage",
            orientation="h",
            title=title
                )
            fig.update_traces(textposition="auto")
            fig.update_layout(yaxis_title=None)
        else:
            continue  # Skip unknown chart types

        

        # -------------------------------------------------
        # RENDER TO HTML
        # -------------------------------------------------
        # fig.update_layout(title_x=0.5)  
        charts[f"chart_{i}"] = pio.to_html(fig, full_html=False)

    return charts

