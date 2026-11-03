
import pandas as pd
import plotly.graph_objects as go

from src.config.theme import (
    AC,
    UPC,
    DNC,
    CHART_HEIGHT as THEME_CHART_HEIGHT,
)

from src.transforms.transform_cc import CONDITION_ORDER


CONDITION_COLORS = {
    "Very Poor": "#8B1E3F",
    "Poor": "#D1432F",
    "Fair": "#F58220",
    "Good": "#1A9A55",
    "Excellent": "#006B3C",
}

CHART_HEIGHT = 450
CHART_MARGIN = dict(l=10, r=120, t=35, b=105)

MONTH_LABELS = [
    ("Jan", 2.5),
    ("Feb", 6.5),
    ("Mar", 11),
    ("Apr", 15.5),
    ("May", 19.5),
    ("Jun", 24),
    ("Jul", 28.5),
    ("Aug", 33),
    ("Sep", 37.5),
    ("Oct", 41.5),
    ("Nov", 46),
    ("Dec", 51),
]


def _add_month_labels(fig, month_labels=MONTH_LABELS):

    fig.update_layout(
        margin=dict(
            l=CHART_MARGIN["l"],
            r=CHART_MARGIN["r"],
            t=CHART_MARGIN["t"],
            b=CHART_MARGIN["b"] + 25,
        ),
        annotations=[
            dict(
                x=week,
                y=-0.22,
                xref="x",
                yref="paper",
                text=month,
                showarrow=False,
                xanchor="center",
                yanchor="top",
                font=dict(
                    size=10,
                    color="#6B7686",
                ),
            )
            for month, week in month_labels
        ],
    )

    return fig


def _add_missing_week_gaps(year_data, week_column):

    x_values = []
    y_values = []

    previous_week = None

    for _, row in year_data.iterrows():

        week = int(row[week_column])

        if (
            previous_week is not None
            and week - previous_week > 1
        ):
            for missing_week in range(
                previous_week + 1,
                week,
            ):
                x_values.append(missing_week)
                y_values.append(None)

        x_values.append(week)
        y_values.append(row["Value"])

        previous_week = week

    return x_values, y_values


def seasonal_ge_fig(
    df,
    latest_year=None,
    title="Good + Excellent",
    yaxis_range=None,
    crop_type=None,
):

    fig = go.Figure()

    if df.empty:
        fig.update_layout(
            title=title,
            height=CHART_HEIGHT,
            margin=CHART_MARGIN,
        )
        return fig

    data = df.copy()

    data["Year"] = pd.to_numeric(
        data["Year"],
        errors="coerce",
    )

    data["Week"] = pd.to_numeric(
        data["Week"],
        errors="coerce",
    )

    data["Value"] = pd.to_numeric(
        data["Value"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["Year", "Week", "Value"]
    )

    years = sorted(
        data["Year"].unique()
    )

    for year in years:

        year_data = (
            data.loc[data["Year"] == year]
            .sort_values("Week")
            .drop_duplicates(
                subset=["Week"],
                keep="last",
            )
        )

        x_values, y_values = _add_missing_week_gaps(
            year_data,
            "Week",
        )

        is_latest = (
            latest_year is not None
            and int(year) == int(latest_year)
        )

        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines",
                name=str(int(year)),
                connectgaps=False,
                line=dict(
                    width=3 if is_latest else 1.5,
                    color=AC if is_latest else None,
                ),
            )
        )

    fig.update_layout(
        title=title,
        height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        hovermode="x unified",
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
        ),
        xaxis=dict(
            title="Reporting Week",
            dtick=2,
            rangemode="tozero",
            range=[1, 53],
        ),
        yaxis=dict(
            title="Percent",
            ticksuffix="%",
            range=yaxis_range or [0, 100],
        ),
    )

    _add_month_labels(fig)

    return fig


def weekly_condition_fig(
    df,
    title="Weekly Crop Condition",
):

    fig = go.Figure()

    if df.empty:
        fig.update_layout(
            title=title,
            height=CHART_HEIGHT,
            margin=CHART_MARGIN,
        )
        return fig

    for condition in CONDITION_ORDER:

        if condition not in df.columns:
            continue

        fig.add_trace(
            go.Bar(
                x=df["Week"],
                y=df[condition],
                name=condition,
                marker_color=CONDITION_COLORS[condition],
                hovertemplate=(
                    f"{condition}: "
                    "%{y:.1f}%"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=title,
        barmode="stack",
        height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        hovermode="x unified",
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
        ),
        xaxis=dict(
            title="Reporting Week",
            dtick=2,
            range=[1, 53],
        ),
        yaxis=dict(
            title="Percent",
            ticksuffix="%",
            range=[0, 100],
        ),
    )

    _add_month_labels(fig)

    return fig


def state_comparison_bar_fig(
    df,
    value_column,
    title,
    change=False,
):

    fig = go.Figure()

    if df.empty or value_column not in df.columns:
        fig.update_layout(
            title=title,
            height=THEME_CHART_HEIGHT,
        )
        return fig

    data = df[
        ["State", value_column]
    ].copy()

    data[value_column] = pd.to_numeric(
        data[value_column],
        errors="coerce",
    )

    data = data.dropna(
        subset=["State", value_column]
    )

    data = data.sort_values(
        value_column,
        ascending=False,
    )

    if data.empty:
        fig.update_layout(
            title=title,
            height=THEME_CHART_HEIGHT,
        )
        return fig

    if change:
        colors = [
            UPC if value > 0 else DNC
            for value in data[value_column]
        ]
    else:
        colors = AC

    fig.add_trace(
        go.Bar(
            x=data["State"],
            y=data[value_column],
            marker_color=colors,
            hovertemplate=(
                "%{x}: %{y:.1f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=title,
        height=CHART_HEIGHT,
        margin=dict(
            l=45,
            r=15,
            t=45,
            b=100,
        ),
        showlegend=False,
        xaxis=dict(
            title="State",
            tickangle=-45,
            categoryorder="array",
            categoryarray=data["State"].tolist(),
        ),
        yaxis=dict(
            title="Change" if change else "Good + Excellent",
            zeroline=change,
            zerolinecolor="#9AA3AF",
            zerolinewidth=1,
        ),
        bargap=0.2,
    )

    return fig
