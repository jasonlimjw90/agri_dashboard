
import pandas as pd
import plotly.graph_objects as go

from src.config.theme import (
    AC,
    MU,
    BLACK,
    PALETTE,
    CHART_HEIGHT,
)

from src.transforms.transform_cp import (
    is_five_year_average,
    get_chronological_measure_order,
)

from src.components.state_map import (
    state_comparison_map,
)


CHART_MARGIN = dict(
    l=55,
    r=180,
    t=45,
    b=35,
)

WINTER_WHEAT_START_WEEK = 33
WINTER_WHEAT_SEASON_LENGTH = 54

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


def _week_customdata(
    df: pd.DataFrame,
) -> pd.DataFrame:

    return df[
        ["Week", "Week Ending"]
    ].astype(object).to_numpy()


def _add_month_labels(
    fig: go.Figure,
) -> go.Figure:

    fig.update_layout(
        margin=dict(
            l=CHART_MARGIN["l"],
            r=CHART_MARGIN["r"],
            t=CHART_MARGIN["t"],
            b=CHART_MARGIN["b"] + 55,
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
                    color=MU,
                ),
            )
            for month, week in MONTH_LABELS
        ],
    )

    return fig


def _base_layout(
    fig: go.Figure,
    title: str | None = None,
) -> go.Figure:

    fig.update_layout(
        title=title,
        height=CHART_HEIGHT,
        autosize=True,
        margin=CHART_MARGIN,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=MU),
        hovermode="x unified",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
            traceorder="normal",
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor=MU,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(128,128,128,0.15)",
            zeroline=False,
        ),
    )

    return fig


def _week_axis(
    fig: go.Figure,
) -> go.Figure:

    fig.update_xaxes(
        title=None,
        tickmode="array",
        tickvals=list(range(1, 54, 2)),
        ticktext=[
            f"W{week:02d}"
            for week in range(1, 54, 2)
        ],
        range=[1, 53],
    )

    return _add_month_labels(fig)


def _winter_wheat_axis(
    fig: go.Figure,
) -> go.Figure:

    tick_positions = list(range(1, 54, 2))

    if WINTER_WHEAT_SEASON_LENGTH not in tick_positions:
        tick_positions.append(WINTER_WHEAT_SEASON_LENGTH)

    tick_labels = []

    for position in tick_positions:

        if position == 1:
            tick_labels.append("W33 Start")

        elif position == WINTER_WHEAT_SEASON_LENGTH:
            tick_labels.append("W33 End")

        else:
            week = (
                position + WINTER_WHEAT_START_WEEK - 1
                if position <= 21
                else position - 21
            )
            tick_labels.append(f"W{week:02d}")

    fig.update_xaxes(
        title=None,
        tickmode="array",
        tickvals=tick_positions,
        ticktext=tick_labels,
        range=[1, WINTER_WHEAT_SEASON_LENGTH],
    )

    return fig


def _prepare_weekly_series(
    df: pd.DataFrame,
) -> pd.DataFrame:

    weeks = pd.DataFrame(
        {
            "Week": range(1, 54),
        }
    )

    return weeks.merge(
        df[
            [
                "Week",
                "Week Ending",
                "Value",
            ]
        ],
        on="Week",
        how="left",
        sort=False,
    )


def _prepare_winter_wheat_series(
    df: pd.DataFrame,
    crop_year: int,
) -> pd.DataFrame:

    columns = [
        "Season Position",
        "Week",
        "Week Ending",
        "Value",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    data = df[
        [
            "Week",
            "Week Ending",
            "Value",
        ]
    ].copy()

    calendar_year = data["Week Ending"].dt.year

    start_season_mask = (
        (calendar_year == crop_year - 1)
        & (data["Week"] >= WINTER_WHEAT_START_WEEK)
    )

    end_season_mask = (
        (calendar_year == crop_year)
        & (data["Week"] <= WINTER_WHEAT_START_WEEK)
    )

    data["Season Position"] = pd.NA

    data.loc[
        start_season_mask,
        "Season Position",
    ] = (
        data.loc[start_season_mask, "Week"]
        - WINTER_WHEAT_START_WEEK
        + 1
    )

    data.loc[
        end_season_mask,
        "Season Position",
    ] = (
        data.loc[end_season_mask, "Week"]
        + 21
    )

    data = data.dropna(
        subset=["Season Position"]
    )

    if data.empty:
        return pd.DataFrame(columns=columns)

    data["Season Position"] = (
        data["Season Position"].astype(int)
    )

    data = (
        data
        .drop_duplicates(
            subset=["Season Position"],
            keep="last",
        )
    )

    positions = pd.DataFrame(
        {
            "Season Position": range(
                1,
                WINTER_WHEAT_SEASON_LENGTH + 1,
            )
        }
    )

    return (
        positions
        .merge(
            data,
            on="Season Position",
            how="left",
            sort=True,
        )[columns]
    )


def national_all_stages_fig(
    df: pd.DataFrame,
    crop_type: str,
    year: int,
    title: str | None = None,
) -> go.Figure:

    fig = go.Figure()

    data = df.loc[
        df["Crop Type"] == crop_type
    ]

    if "Geo Level" in data.columns:
        data = data.loc[
            data["Geo Level"] == "NATIONAL"
        ]

    if data.empty:
        return _base_layout(fig, title)

    average_mask = is_five_year_average(data)

    average_data = data.loc[
        average_mask
        & (data["Year"] == year)
    ]

    actual_data = data.loc[
        ~average_mask
        & data["Year"].isin(
            [
                year - 1,
                year,
            ]
        )
    ]

    measure_data = pd.concat(
        [
            actual_data[["Measure", "Week"]],
            average_data[["Measure", "Week"]],
        ],
        ignore_index=True,
    )

    measures = get_chronological_measure_order(
        measure_data
    )

    if not measures:
        return _base_layout(fig, title)

    is_winter_wheat = crop_type == "Winter Wheat"

    for i, measure in enumerate(measures):

        color = PALETTE[i % len(PALETTE)]

        previous_data = actual_data.loc[
            (actual_data["Measure"] == measure)
            & (actual_data["Year"] == year - 1)
        ]

        current_data = actual_data.loc[
            (actual_data["Measure"] == measure)
            & (actual_data["Year"] == year)
        ]

        average_measure_data = average_data.loc[
            average_data["Measure"] == measure
        ]

        if not previous_data.empty:

            if is_winter_wheat:
                previous = _prepare_winter_wheat_series(
                    previous_data,
                    crop_year=year - 1,
                )
                x_column = "Season Position"
            else:
                previous = _prepare_weekly_series(
                    previous_data
                )
                x_column = "Week"

            if not previous.empty:

                fig.add_trace(
                    go.Scatter(
                        x=previous[x_column],
                        y=previous["Value"],
                        customdata=_week_customdata(previous),
                        mode="lines",
                        name=f"{measure} ({year - 1})",
                        legendgroup=measure,
                        legendrank=i * 3,
                        line=dict(
                            color=MU,
                            width=1.8,
                            dash="dot",
                        ),
                        connectgaps=False,
                        hovertemplate=(
                            "Week %{customdata[0]}<br>"
                            + measure
                            + f" ({year - 1}): "
                            + "%{y:.1f}%<br>"
                            + "Week ending: %{customdata[1]|%d %b %Y}"
                            + "<extra></extra>"
                        ),
                    )
                )

        if not current_data.empty:

            if is_winter_wheat:
                current = _prepare_winter_wheat_series(
                    current_data,
                    crop_year=year,
                )
                x_column = "Season Position"
            else:
                current = _prepare_weekly_series(
                    current_data
                )
                x_column = "Week"

            if not current.empty:

                fig.add_trace(
                    go.Scatter(
                        x=current[x_column],
                        y=current["Value"],
                        customdata=_week_customdata(current),
                        mode="lines+markers",
                        name=f"{measure} ({year})",
                        legendgroup=measure,
                        legendrank=i * 3 + 1,
                        line=dict(
                            color=color,
                            width=2.8,
                        ),
                        marker=dict(size=4),
                        connectgaps=False,
                        hovertemplate=(
                            "Week %{customdata[0]}<br>"
                            + measure
                            + f" ({year}): "
                            + "%{y:.1f}%<br>"
                            + "Week ending: %{customdata[1]|%d %b %Y}"
                            + "<extra></extra>"
                        ),
                    )
                )

        if not average_measure_data.empty:

            if is_winter_wheat:
                average = _prepare_winter_wheat_series(
                    average_measure_data,
                    crop_year=year,
                )
                x_column = "Season Position"
            else:
                average = _prepare_weekly_series(
                    average_measure_data
                )
                x_column = "Week"

            if not average.empty:

                fig.add_trace(
                    go.Scatter(
                        x=average[x_column],
                        y=average["Value"],
                        customdata=_week_customdata(average),
                        mode="lines",
                        name=f"{measure} (5Y Avg)",
                        legendgroup=measure,
                        legendrank=i * 3 + 2,
                        line=dict(
                            color=BLACK,
                            width=2.2,
                            dash="dash",
                        ),
                        connectgaps=False,
                        hovertemplate=(
                            "Week %{customdata[0]}<br>"
                            + measure
                            + " (5Y Avg): %{y:.1f}%"
                            "<extra></extra>"
                        ),
                    )
                )

    fig.update_yaxes(
        title="Progress (%)",
        ticksuffix="%",
        range=[0, 100],
    )

    fig = _base_layout(fig, title)

    if is_winter_wheat:
        return _winter_wheat_axis(fig)

    return _week_axis(fig)


def state_comparison_fig(
    df: pd.DataFrame,
    year: int,
    title: str | None = None,
) -> go.Figure:

    return state_comparison_map(
        df=df,
        year=year,
        value_label="Progress",
        title=title,
    )


def seasonal_history_fig(
    series,
    title: str | None = None,
    current_year: int | None = None,
    season_start_week: int | None = None,
) -> go.Figure:

    fig = go.Figure()

    if not series:
        return _base_layout(fig, title)

    is_winter_wheat = (
        season_start_week == WINTER_WHEAT_START_WEEK
    )

    for i, (year, data) in enumerate(
        sorted(
            series.items(),
            key=lambda item: int(item[0]),
        )
    ):

        year = int(year)

        if year == current_year:
            color = AC
            width = 3
        else:
            color = PALETTE[i % len(PALETTE)]
            width = 1.5

        if isinstance(data, pd.DataFrame):

            if is_winter_wheat:
                plot_data = _prepare_winter_wheat_series(
                    data,
                    crop_year=year,
                )
                x_column = "Season Position"
            else:
                plot_data = data
                x_column = "Week"

            if plot_data.empty:
                continue

            fig.add_trace(
                go.Scatter(
                    x=plot_data[x_column],
                    y=plot_data["Value"],
                    customdata=_week_customdata(plot_data),
                    mode="lines",
                    name=str(year),
                    line=dict(
                        color=color,
                        width=width,
                    ),
                    marker=dict(size=4),
                    connectgaps=False,
                    hovertemplate=(
                        "Week %{customdata[0]}<br>"
                        + str(year)
                        + ": %{y:.1f}%<br>"
                        + "Week ending: %{customdata[1]|%d %b %Y}"
                        + "<extra></extra>"
                    ),
                )
            )

        else:

            fig.add_trace(
                go.Scatter(
                    x=list(range(1, len(data) + 1)),
                    y=data,
                    mode="lines",
                    name=str(year),
                    line=dict(
                        color=color,
                        width=width,
                    ),
                    connectgaps=False,
                    hovertemplate=(
                        "Week %{x}<br>"
                        + str(year)
                        + ": %{y:.1f}%"
                        "<extra></extra>"
                    ),
                )
            )

    fig.update_yaxes(
        title="Progress (%)",
        ticksuffix="%",
        range=[0, 100],
    )

    fig = _base_layout(fig, title)

    if is_winter_wheat:
        return _winter_wheat_axis(fig)

    return _week_axis(fig)


def weekly_comparison_fig(
    df: pd.DataFrame,
    week: int,
    current_year: int,
    average_value: float | None = None,
    title: str | None = None,
) -> go.Figure:

    fig = go.Figure()

    if df.empty:
        return _base_layout(fig, title)

    colors = [
        AC if year == current_year else MU
        for year in df["Year"]
    ]

    fig.add_trace(
        go.Bar(
            x=df["Year"].astype(str),
            y=df["Value"],
            marker_color=colors,
            text=df["Value"].map(
                lambda value: f"{value:.1f}%"
            ),
            textposition="outside",
            name="Progress",
            hovertemplate=(
                "Year: %{x}<br>"
                "Progress: %{y:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    if average_value is not None:
        fig.add_hline(
            y=average_value,
            line_dash="dash",
            line_color=BLACK,
            line_width=2,
            annotation_text=f"5Y Avg: {average_value:.1f}%",
            annotation_position="top left",
        )

    fig.update_xaxes(
        title="Crop Year",
        type="category",
    )

    fig.update_yaxes(
        title="Progress (%)",
        ticksuffix="%",
        range=[0, 100],
    )

    fig.update_layout(
        showlegend=False,
        bargap=0.25,
    )

    return _base_layout(
        fig,
        title=title or f"Progress in Week {week}",
    )


def weekly_progress_fig(
    df: pd.DataFrame,
    crop_type: str,
    measure: str,
    week: int,
    current_year: int,
    title: str | None = None,
) -> go.Figure:

    fig = go.Figure()

    data = df.loc[
        (df["Crop Type"] == crop_type)
        & (df["Measure"] == measure)
        & (df["Week"] == week)
    ]

    if "Geo Level" in data.columns:
        data = data.loc[
            data["Geo Level"] == "NATIONAL"
        ]

    if data.empty:
        return _base_layout(fig, title)

    actual_data = data.loc[
        ~is_five_year_average(data)
    ]

    if actual_data.empty:
        return _base_layout(fig, title)

    years = actual_data["Year"].tolist()
    values = actual_data["Value"].tolist()

    colors = [
        AC if year == current_year else MU
        for year in years
    ]

    fig.add_trace(
        go.Bar(
            x=years,
            y=values,
            marker_color=colors,
            name="Progress",
            text=[
                f"{value:.1f}%"
                for value in values
            ],
            textposition="outside",
            customdata=actual_data[
                ["Week Ending"]
            ],
            hovertemplate=(
                "Year %{x}<br>"
                "Progress: %{y:.1f}%<br>"
                "Week ending: %{customdata[0]|%d %b %Y}"
                "<extra></extra>"
            ),
        )
    )

    current_year_data = actual_data.loc[
        actual_data["Year"] == current_year
    ]

    if not current_year_data.empty:

        latest_year_value = float(
            current_year_data["Value"].iloc[-1]
        )

        fig.add_hline(
            y=latest_year_value,
            line_dash="dash",
            line_color=AC,
            line_width=2,
            annotation_text=(
                f"{current_year}: {latest_year_value:.1f}%"
            ),
            annotation_position="top left",
        )

    fig.update_xaxes(
        title="Crop Year",
        tickmode="linear",
        dtick=1,
    )

    fig.update_yaxes(
        title="Progress (%)",
        ticksuffix="%",
        range=[0, 110],
    )

    return _base_layout(
        fig,
        title=title,
    ).update_layout(height=450)
