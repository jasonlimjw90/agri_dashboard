
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative

from src.components.format_years import format_marketing_year

from src.config.theme import (
    AC,
    UPC,
    DNC,
    MU,
    OR,
    W,
    PALETTE,
    CHART_HEIGHT,
    CHART_MARGIN,
    HISTORICAL_RANGE_FILL,
    WEEK_TICK_VALUES,
    WEEK_TICK_TEXT,
    MONTH_TICK_VALUES,
    MONTH_TICK_TEXT,
)


def _historical_stats(
    series: dict,
    historical_years: list,
    periods: int,
):

    if not historical_years:
        return None, None, None

    data = {}

    for year in historical_years:

        values = np.asarray(
            series[year],
            dtype=float,
        )

        data[year] = pd.Series(
            values,
            index=range(1, len(values) + 1),
        )

    df = pd.DataFrame(data).T

    df = df.reindex(
        columns=range(1, periods + 1)
    )

    historical_max = df.max(axis=0)
    historical_min = df.min(axis=0)
    historical_avg = df.mean(axis=0)

    return (
        historical_max.to_numpy(),
        historical_min.to_numpy(),
        historical_avg.to_numpy(),
    )


def _prepare_seasonal_data(
    series: dict,
    years: int,
):

    if not series:
        return None

    series = {
        int(year): values
        for year, values in series.items()
    }

    latest_year = max(series)
    previous_year = latest_year - 1

    historical_years = sorted(
        year
        for year in series
        if year < latest_year
    )[-years:]

    return (
        series,
        latest_year,
        previous_year,
        historical_years,
    )


def _seasonal_layout(
    fig: go.Figure,
    tick_values: list,
    tick_text: list,
    x_title: str,
    title: str | None = None,
):

    fig.update_xaxes(
        tickvals=tick_values,
        ticktext=tick_text,
        showgrid=False,
        title=x_title,
    )

    fig.update_layout(
        title=title,
        height=CHART_HEIGHT,
        margin={**CHART_MARGIN, "r": 105},
        legend=dict(
            orientation="v",
            x=1.02,
            xanchor="left",
            y=1,
            yanchor="top",
            font_size=10,
        ),
    )

    return fig


def _add_historical_range(
    fig: go.Figure,
    x: np.ndarray,
    historical_max: np.ndarray,
    historical_min: np.ndarray,
    name: str,
):

    polygon_x = np.concatenate([
        x,
        x[::-1],
    ])

    polygon_y = np.concatenate([
        historical_max,
        historical_min[::-1],
    ])

    fig.add_trace(
        go.Scatter(
            x=polygon_x,
            y=polygon_y,
            mode="lines",
            line=dict(
                color="rgba(0,0,0,0)",
                width=0,
            ),
            fill="toself",
            fillcolor=HISTORICAL_RANGE_FILL,
            name=name,
            hoverinfo="skip",
        )
    )


def _add_current_and_previous(
    fig: go.Figure,
    series: dict,
    latest_year: int,
    previous_year: int,
):

    if previous_year in series:

        previous_values = np.asarray(
            series[previous_year],
            dtype=float,
        )

        fig.add_scatter(
            x=np.arange(
                1,
                len(previous_values) + 1,
            ),
            y=previous_values,
            mode="lines",
            line=dict(
                color=MU,
                dash="dash",
                width=1.8,
            ),
            name=str(previous_year),
        )

    latest_values = np.asarray(
        series[latest_year],
        dtype=float,
    )

    fig.add_scatter(
        x=np.arange(
            1,
            len(latest_values) + 1,
        ),
        y=latest_values,
        mode="lines",
        line=dict(
            color=AC,
            width=3,
        ),
        name=str(latest_year),
    )


def _seasonal_period_fig(
    series: dict,
    periods: int,
    tick_values: list,
    tick_text: list,
    x_title: str,
    years: int,
    title: str | None = None,
) -> go.Figure:

    if not series:
        return go.Figure()

    series, latest_year, previous_year, historical_years = (
        _prepare_seasonal_data(series, years)
    )

    x = np.arange(1, periods + 1)
    fig = go.Figure()

    historical_max, historical_min, historical_avg = _historical_stats(
        series,
        historical_years,
        periods,
    )

    if historical_max is not None:
        _add_historical_range(
            fig,
            x,
            historical_max,
            historical_min,
            f"{len(historical_years)}-yr range",
        )

        fig.add_scatter(
            x=x,
            y=historical_avg,
            mode="lines",
            line=dict(color=MU, width=1.8),
            name=f"{len(historical_years)}-yr avg",
        )

    _add_current_and_previous(
        fig,
        series,
        latest_year,
        previous_year,
    )

    return _seasonal_layout(
        fig,
        tick_values,
        tick_text,
        x_title,
        title,
    )


def seasonal_weekly_fig(
    series: dict,
    years: int = 5,
    title: str | None = None,
) -> go.Figure:

    return _seasonal_period_fig(
        series=series,
        periods=53,
        tick_values=WEEK_TICK_VALUES,
        tick_text=WEEK_TICK_TEXT,
        x_title="Week",
        years=years,
        title=title,
    )


def seasonal_monthly_fig(
    series: dict,
    years: int = 5,
    title: str | None = None,
) -> go.Figure:

    return _seasonal_period_fig(
        series=series,
        periods=12,
        tick_values=MONTH_TICK_VALUES,
        tick_text=MONTH_TICK_TEXT,
        x_title="Month",
        years=years,
        title=title,
    )


def seasonal_history_fig(
    series: dict,
    years: int = 10,
) -> go.Figure:

    if not series:
        return go.Figure()

    series = {
        int(year): np.asarray(values, dtype=float)
        for year, values in series.items()
    }

    selected_years = sorted(series)[-years:]

    fig = go.Figure()

    palette = qualitative.Plotly
    latest_year = max(selected_years)

    for i, year in enumerate(selected_years):

        color = (
            AC
            if year == latest_year
            else palette[i % len(palette)]
        )

        fig.add_scatter(
            x=MONTH_TICK_VALUES,
            y=series[year],
            mode="lines",
            line=dict(
                color=color,
                width=3 if year == latest_year else 1.5,
            ),
            opacity=1 if year == latest_year else 0.75,
            name=str(year),
        )

    return _seasonal_layout(
        fig,
        MONTH_TICK_VALUES,
        MONTH_TICK_TEXT,
        "Month",
    )


def historical_bars_fig(
    values: np.ndarray,
    x_labels: list,
) -> go.Figure:

    values = np.asarray(
        values,
        dtype=float,
    )

    if values.size == 0:
        return go.Figure()

    fig = go.Figure(
        go.Bar(
            x=x_labels,
            y=values,
            marker=dict(
                color=AC,
            ),
            hovertemplate=(
                "%{x}<br>"
                "%{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        showlegend=False,
        bargap=0.25,
    )

    fig.update_xaxes(
        title="Marketing Year",
        showgrid=False,
        type="category",
    )

    fig.update_yaxes(
        showgrid=True,
        zeroline=False,
    )

    return fig


def bars_fig(
    values: np.ndarray,
    x_title: str = "Report",
    x_labels: list = None,
) -> go.Figure:

    values = np.asarray(
        values,
        dtype=float,
    )

    if values.size == 0:
        return go.Figure()

    rms = np.sqrt(
        np.nanmean(values ** 2)
    )

    if not np.isfinite(rms) or rms == 0:
        rms = 1

    x_values = np.arange(
        1,
        len(values) + 1,
    )

    fig = go.Figure(
        go.Bar(
            x=x_values,
            y=values,
            marker=dict(
                color=[
                    UPC if value >= 0 else DNC
                    for value in values
                ],
                opacity=[
                    1 if abs(value) > 1.5 * rms else 0.55
                    for value in values
                ],
            ),
            hovertemplate=(
                "%{x}<br>"
                "%{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        bargap=0.15,
        showlegend=False,
    )

    fig.update_xaxes(
        title=x_title,
        showgrid=False,
    )

    if x_labels is not None:

        fig.update_xaxes(
            tickvals=x_values,
            ticktext=x_labels,
        )

    fig.update_yaxes(
        zeroline=True,
    )

    return fig


def add_change_line(
    fig: go.Figure,
    x_values: list,
    change_values: list,
    name: str = "YoY Change",
) -> go.Figure:

    if len(x_values) == 0 or len(change_values) == 0:
        return fig

    if len(x_values) != len(change_values):
        return fig

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=change_values,
            mode="lines",
            line=dict(
                color=OR,
                width=3.5,
            ),
            name=name,
            yaxis="y2",
            connectgaps=False,
            hoverinfo="skip",
            showlegend=False,
        )
    )

    for i, value in enumerate(change_values):
        if pd.isna(value):
            continue

        color = UPC if value > 0 else W if value < 0 else MU

        fig.add_trace(
            go.Scatter(
                x=[x_values[i]],
                y=[value],
                mode="text",
                text=[f"{value:+.1f}%"],
                textposition="top center",
                textfont=dict(
                    color=color,
                    size=12,
                ),
                name=name,
                yaxis="y2",
                showlegend=False,
                hovertemplate=(
                    "%{x}<br>"
                    f"{name}: " + "%{y:.1f}%"
                    "<extra></extra>"
                ),
                cliponaxis=False,
            )
        )

    fig.update_layout(
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor="rgba(128,128,128,0.5)",
            showticklabels=False,
            ticks="",
            title=None,
        ),
    )

    return fig


def seasonal_fig(
    series: dict,
    years: int = 5,
) -> go.Figure:

    return seasonal_weekly_fig(
        series=series,
        years=years,
    )


def monthly_change_fig(
    data: pd.DataFrame,
    title: str = None,
):
    if data.empty:
        return go.Figure()

    values = data["Change"].to_numpy(dtype=float)
    labels = data["Report Date"].dt.strftime("%b %y").tolist()

    colors = [
        "#16A34A" if value >= 0 else "#DC2626"
        for value in values
    ]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            hovertemplate=(
                "%{x}<br>"
                "Change: %{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=None,
        height=300,
        margin=dict(
            l=10,
            r=10,
            t=20,
            b=10,
        ),
        xaxis=dict(
            title=None,
            type="category",
            categoryorder="array",
            categoryarray=labels,
            tickangle=0,
        ),
        yaxis=dict(
            title=None,
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor="rgba(128,128,128,0.5)",
        ),
        showlegend=False,
    )

    return fig


def _prepare_country_historical_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return df.copy()

    data = df.copy()
    data["crop year"] = pd.to_numeric(data["crop year"], errors="coerce")
    data["Value"] = pd.to_numeric(data["Value"], errors="coerce")

    return data.dropna(subset=["crop year", "Value", "country"])



def country_historical_stacked_fig(
    df: pd.DataFrame,
    countries: list,
    years: int | None = 5,
) -> go.Figure:

    data = _prepare_country_historical_data(df)

    if data.empty:
        return go.Figure()

    countries = list(countries)
    

    country_colors = {
        country: PALETTE[i % len(PALETTE)]
        for i, country in enumerate(countries)
    }

    data = (
        data
        .sort_values("Report Date")
        .drop_duplicates(
            subset=["country", "crop year"],
            keep="last",
        )
    )

    selected_years = sorted(
        data["crop year"].unique()
    )

    if years is not None:
        selected_years = selected_years[-years:]

    data = data[
        data["crop year"].isin(selected_years)
    ]

    pivot = data.pivot(
        index="crop year",
        columns="country",
        values="Value",
    )

    pivot = pivot.reindex(
        index=selected_years,
        columns=countries,
    )

    fig = go.Figure()

    for country in countries:

        fig.add_trace(
            go.Bar(
                x=pivot.index.astype(str),
                y=pivot[country],
                name=country,
                marker_color=country_colors[country],
                hovertemplate=(
                    f"{country}<br>"
                    "Marketing Year: %{x}<br>"
                    "Value: %{y:,.2f}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        barmode="stack",
        height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        bargap=0.25,
        legend=dict(
            orientation="h",
            y=1.02,
            x=0,
            font_size=10,
        ),
    )

    fig.update_xaxes(
        title="Marketing Year",
        showgrid=False,
    )

    fig.update_yaxes(
        title="Value",
        showgrid=True,
        zeroline=False,
    )

    return fig



def country_historical_pie_fig(
    df: pd.DataFrame,
    countries: list,
) -> go.Figure:

    data = _prepare_country_historical_data(df)

    if data.empty:
        return go.Figure()

    latest_year = data["crop year"].max()

    latest = (
        data[data["crop year"] == latest_year]
        .groupby("country")["Value"]
        .last()
        .reindex(countries)
        .dropna()
    )

    latest = latest[latest > 0]

    if latest.empty:
        return go.Figure()

    fig = go.Figure(
        go.Pie(
            labels=latest.index,
            values=latest.values,
            hole=0,
            marker=dict(
                colors=[
                    PALETTE[
                        countries.index(country) % len(PALETTE)
                    ]
                    for country in latest.index
                ],
            ),
            textinfo="label+percent",
            hovertemplate=(
                "%{label}<br>"
                "Value: %{value:,.2f}<br>"
                "Share: %{percent}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=CHART_HEIGHT,
        margin=CHART_MARGIN,
        showlegend=False,
        title=dict(
            text=f"Marketing Year {int(latest_year)}",
            x=0,
            y=0.5,
            xanchor="left",
            yanchor="middle",
        ),
    )

    return fig


def monthly_change_history_fig(
    df: pd.DataFrame,
    group_col: str = "country",
    groups: list = None,
    title: str = None,
) -> go.Figure:

    if df.empty:
        return go.Figure()

    marketing_years = sorted(
        df["crop year"].unique()
    )

    x_labels = [
        format_marketing_year(year)
        for year in marketing_years
    ]

    fig = go.Figure()

    if group_col is None:

        values = (
            df.set_index("crop year")["Change"]
            .reindex(marketing_years)
        )

        bar_colors = [
            UPC if pd.notna(value) and value > 0
            else DNC if pd.notna(value) and value < 0
            else MU
            for value in values
        ]

        fig.add_trace(
            go.Bar(
                x=x_labels,
                y=values,
                marker_color=bar_colors,
                hovertemplate=(
                    "Marketing Year: %{x}<br>"
                    "Revision: %{y:+,.2f}"
                    "<extra></extra>"
                ),
            )
        )

        fig.update_layout(
            title=dict(
                text=title or "",
                x=0.5,
                xanchor="center",
                font=dict(
                    size=14,
                    color=AC,
                ),
            ),
            height=380,
            margin=dict(
                l=CHART_MARGIN["l"],
                r=CHART_MARGIN["r"],
                t=65,
                b=CHART_MARGIN["b"],
            ),
            showlegend=False,
            bargap=0.2,
        )

        fig.update_yaxes(
            title=None,
            showgrid=True,
            zeroline=True,
        )

    else:

        if groups is None:
            groups = sorted(
                df[group_col].unique().tolist()
            )

        pivot = df.pivot(
            index="crop year",
            columns=group_col,
            values="Change",
        )

        pivot = pivot.reindex(
            index=marketing_years,
            columns=groups,
        )

        for i, group in enumerate(groups):

            if group not in pivot.columns:
                continue

            values = pivot[group]

            bar_colors = [
                UPC if pd.notna(value) and value > 0
                else DNC if pd.notna(value) and value < 0
                else MU
                for value in values
            ]

            fig.add_trace(
                go.Bar(
                    x=x_labels,
                    y=values,
                    name=group,
                    marker_color=bar_colors,
                    hovertemplate=(
                        "Marketing Year: %{x}<br>"
                        f"{group}: "
                        "%{y:+,.2f}"
                        "<extra></extra>"
                    ),
                )
            )

        fig.update_layout(
            title=dict(
                text=title or "",
                x=0.5,
                xanchor="center",
                font=dict(
                    size=14,
                    color=AC,
                ),
            ),
            barmode="group",
            height=380,
            margin=dict(
                l=CHART_MARGIN["l"],
                r=CHART_MARGIN["r"],
                t=65,
                b=CHART_MARGIN["b"],
            ),
            bargap=0.2,
            bargroupgap=0.05,
            showlegend=len(groups) > 1,
            legend=dict(
                orientation="h",
                y=1.12,
                x=0,
                font_size=10,
            ),
        )

        fig.update_yaxes(
            title="Monthly Revision",
            showgrid=True,
            zeroline=True,
        )

    fig.update_xaxes(
        title="Marketing Year",
        showgrid=False,
        type="category",
        categoryorder="array",
        categoryarray=x_labels,
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=MU),
    )

    return fig


def country_monthly_change_history_fig(
    df: pd.DataFrame,
    countries: list,
    title: str = None,
) -> go.Figure:

    return monthly_change_history_fig(
        df=df,
        group_col="country",
        groups=countries,
        title=title,
    )


def current_report_change_fig(
    table: pd.DataFrame,
) -> go.Figure:

    if table.empty or not isinstance(table.columns, pd.MultiIndex):
        return go.Figure()

    item_labels = (
        table.index.get_level_values("WASDE Item").tolist()
        if isinstance(table.index, pd.MultiIndex)
        else table.index.astype(str).tolist()
    )

    fig = go.Figure()

    change_groups = [
        group
        for group in table.columns.get_level_values(0).unique()
        if any(
            column[0] == group and column[1] == "Change"
            for column in table.columns
        )
    ]

    for group in change_groups:

        values = pd.to_numeric(
            table[(group, "Change")],
            errors="coerce",
        )

        fig.add_trace(
            go.Bar(
                x=values,
                y=item_labels,
                name=group,
                orientation="h",
                marker_color=[
                    UPC if value > 0
                    else DNC if value < 0
                    else MU
                    for value in values
                ],
                hovertemplate=(
                    "%{y}<br>"
                    f"{group}: " + "%{x:+,.2f}"
                    "<extra></extra>"
                ),
            )
        )

    chart_height = max(
        CHART_HEIGHT,
        len(item_labels) * 35 + 100,
    )

    fig.update_layout(
        barmode="group",
        height=chart_height,
        margin=dict(
            l=10,
            r=20,
            t=20,
            b=35,
        ),
        bargap=0.25,
        bargroupgap=0.1,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=MU),
        legend=dict(
            orientation="h",
            y=1.08,
            x=0,
            font_size=10,
        ),
    )

    fig.update_xaxes(
        title=None,
        showgrid=True,
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor="rgba(128,128,128,0.6)",
    )

    fig.update_yaxes(
        title=None,
        showgrid=False,
        categoryorder="array",
        categoryarray=item_labels[::-1],
    )

    return fig
