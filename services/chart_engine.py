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

        else:
            continue  # Skip unknown chart types

        # -------------------------------------------------
        # RENDER TO HTML
        # -------------------------------------------------
        charts[f"chart_{i}"] = pio.to_html(fig, full_html=False)

    return charts

