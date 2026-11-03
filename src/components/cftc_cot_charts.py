import pandas as pd
import plotly.graph_objects as go

from src.config.theme import (
    AC,
    UPC,
    DNC,
    MU,
    OR,
)

from src.config.labels import (
    MONTH_TICK_VALUES,
    CALENDAR_MONTH_TICK_TEXT,
)

from src.transforms.transform_cftc import (
    DATE_COL,
    TRADER_GROUPS,
    get_position_column,
)


CARD_HEIGHT = 350


def apply_layout(fig, yaxis_title=None, height=None):

    fig.update_layout(
        height=height or CARD_HEIGHT,
        margin=dict(l=10, r=120, t=45, b=35),
        hovermode="closest",
        yaxis_title=yaxis_title,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
        ),
    )

    return fig


def prepare_chart_data(df):

    result = df.copy()

    result[DATE_COL] = pd.to_datetime(
        result[DATE_COL],
        errors="coerce",
    )

    result = result.dropna(
        subset=[DATE_COL]
    )

    return result.sort_values(
        DATE_COL
    ).reset_index(drop=True)


def update_date_axis(fig, df):

    if df.empty:
        return fig

    latest_date = df[DATE_COL].max()
    earliest_date = df[DATE_COL].min()

    fig.update_xaxes(
        type="date",
        range=[
            earliest_date,
            latest_date + pd.Timedelta(days=7),
        ],
        dtick="M12",
        tickformat="%Y",
        tickangle=0,
        showgrid=False,
    )

    return fig


def get_available_cftc_years(df):

    result = prepare_chart_data(df)

    if result.empty:
        return []

    return sorted(
        result[DATE_COL].dt.year.unique().tolist()
    )


def plot_gross_long_short_net(
    df,
    trader_group="Managed Money",
):

    result = prepare_chart_data(df)

    columns = TRADER_GROUPS.get(trader_group)

    if columns is None:
        return go.Figure()

    long_col = get_position_column(
        result,
        columns["long"],
    )

    short_col = get_position_column(
        result,
        columns["short"],
    )

    if long_col is None or short_col is None:
        return go.Figure()

    result["Long"] = pd.to_numeric(
        result[long_col],
        errors="coerce",
    )

    result["Short"] = pd.to_numeric(
        result[short_col],
        errors="coerce",
    )

    result["Net"] = (
        result["Long"] - result["Short"]
    )

    fig = go.Figure()

    fields = [
        ("Long", "Long", UPC, 1.8),
        ("Short", "Short", DNC, 1.8),
        ("Net", "Net", AC, 2.5),
    ]

    for label, column, color, width in fields:

        values = (
            -result[column]
            if column == "Short"
            else result[column]
        )

        fig.add_trace(
            go.Scatter(
                x=result[DATE_COL],
                y=values,
                name=label,
                mode="lines+markers",
                marker=dict(size=4),
                line=dict(
                    color=color,
                    width=width,
                ),
            )
        )

    fig.add_hline(
        y=0,
        line_color=MU,
        line_width=1,
    )

    update_date_axis(fig, result)

    return apply_layout(
        fig,
        yaxis_title="Contracts",
    )


def plot_2026_cross_commodity_net_positions(
    df,
    trader_group="Managed Money",
    year=None,
):

    result = prepare_chart_data(df)

    columns = TRADER_GROUPS.get(trader_group)

    if columns is None:
        return go.Figure()

    long_col = get_position_column(
        result,
        columns["long"],
    )

    short_col = get_position_column(
        result,
        columns["short"],
    )

    required_columns = [
        "Market_and_Exchange_Names",
        "CFTC_Contract_Market_Code",
    ]

    if (
        long_col is None
        or short_col is None
        or any(col not in result.columns for col in required_columns)
    ):
        return go.Figure()

    if result.empty:
        return go.Figure()

    result["Net Position"] = (
        pd.to_numeric(result[long_col], errors="coerce")
        - pd.to_numeric(result[short_col], errors="coerce")
    )

    result = result.dropna(
        subset=["Net Position"]
    )

    available_years = sorted(
        result[DATE_COL].dt.year.unique().tolist()
    )

    if not available_years:
        return go.Figure()

    if year is None:
        year = available_years[-1]

    result = result[
        result[DATE_COL].dt.year == year
    ].copy()

    if result.empty:
        return go.Figure()

    result = (
        result.sort_values(DATE_COL)
        .groupby(
            [
                "CFTC_Contract_Market_Code",
                "Market_and_Exchange_Names",
                DATE_COL,
            ],
            as_index=False,
        )
        .last()
    )

    fig = go.Figure()

    for market_code, market_df in result.groupby(
        "CFTC_Contract_Market_Code"
    ):

        market_df = market_df.sort_values(DATE_COL)

        market_name = market_df[
            "Market_and_Exchange_Names"
        ].iloc[-1]

        fig.add_trace(
            go.Scatter(
                x=market_df[DATE_COL],
                y=market_df["Net Position"],
                name=market_name,
                mode="lines+markers",
                marker=dict(size=4),
                line=dict(width=2),
            )
        )

    fig.add_hline(
        y=0,
        line_color=MU,
        line_width=1,
    )

    fig.update_xaxes(
        type="date",
        tickformat="%b",
        dtick="M1",
        showgrid=False,
    )

    fig.update_layout(
        xaxis_title="Report Date",
        yaxis_title="Net Position (Contracts)",
    )

    return apply_layout(
        fig,
        yaxis_title="Net Position (Contracts)",
    )


def plot_change_bar(
    latest,
    value_column,
    xaxis_title,
    hover_label,
):

    if latest.empty:
        return go.Figure()

    latest = latest.copy()

    latest[value_column] = pd.to_numeric(
        latest[value_column],
        errors="coerce",
    )

    latest = latest.dropna(
        subset=[value_column]
    )

    if latest.empty:
        return go.Figure()

    latest["Color"] = latest[value_column].apply(
        lambda value: UPC if value > 0 else DNC if value < 0 else MU
    )

    values = latest[value_column]

    minimum = min(values.min(), 0)
    maximum = max(values.max(), 0)

    span = max(maximum - minimum, 1)

    axis_min = minimum - span * 0.05

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=values,
            y=latest["Market_and_Exchange_Names"],
            orientation="h",
            marker_color=latest["Color"],
            name=hover_label,
            customdata=latest[[DATE_COL]],
            hovertemplate=(
                "%{y}<br>"
                f"{hover_label}: " + "%{x:+,.0f} contracts<br>"
                "Report Date: %{customdata[0]|%d %b %Y}"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )

    for _, row in latest.iterrows():
        fig.add_annotation(
            x=1,
            xref="paper",
            y=row["Market_and_Exchange_Names"],
            yref="y",
            xanchor="left",
            yanchor="middle",
            xshift=8,
            text=f"{row[value_column]:+,.0f}",
            showarrow=False,
            font=dict(size=12),
            align="left",
        )

    fig.add_vline(
        x=0,
        line_color=MU,
        line_width=1,
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title=xaxis_title,
        yaxis_title=None,
        margin=dict(l=10, r=90, t=45, b=35),
        yaxis=dict(
            categoryorder="array",
            categoryarray=latest[
                "Market_and_Exchange_Names"
            ].tolist(),
        ),
    )

    fig.update_xaxes(
        range=[
            axis_min,
            maximum if maximum > axis_min else axis_min + 1,
        ],
        showgrid=True,
        zeroline=False,
    )

    return fig


def plot_cross_commodity_weekly_net_change(
    df,
    trader_group="Managed Money",
):

    result = prepare_chart_data(df)

    columns = TRADER_GROUPS.get(trader_group)

    if columns is None:
        return go.Figure()

    long_col = get_position_column(
        result,
        columns["long"],
    )

    short_col = get_position_column(
        result,
        columns["short"],
    )

    required_columns = [
        "Market_and_Exchange_Names",
        "CFTC_Contract_Market_Code",
    ]

    if (
        long_col is None
        or short_col is None
        or any(col not in result.columns for col in required_columns)
    ):
        return go.Figure()

    result["Net Position"] = (
        pd.to_numeric(result[long_col], errors="coerce")
        - pd.to_numeric(result[short_col], errors="coerce")
    )

    result = result.sort_values(
        DATE_COL
    )

    result["Weekly Net Change"] = (
        result.groupby(
            "CFTC_Contract_Market_Code"
        )["Net Position"].diff()
    )

    latest = (
        result.dropna(
            subset=["Weekly Net Change"]
        )
        .groupby(
            "CFTC_Contract_Market_Code"
        )
        .tail(1)
        .sort_values(
            "Weekly Net Change",
            ascending=True,
        )
    )

    return plot_change_bar(
        latest=latest,
        value_column="Weekly Net Change",
        xaxis_title="Weekly Net Change (Contracts)",
        hover_label="Weekly Net Change",
    )


def plot_weekly_open_interest_change(df):

    result = prepare_chart_data(df)

    required_columns = [
        "Market_and_Exchange_Names",
        "CFTC_Contract_Market_Code",
        "Open_Interest_All",
    ]

    if any(col not in result.columns for col in required_columns):
        return go.Figure()

    result["Open_Interest_All"] = pd.to_numeric(
        result["Open_Interest_All"],
        errors="coerce",
    )

    result = result.dropna(
        subset=["Open_Interest_All"]
    )

    if result.empty:
        return go.Figure()

    result = result.sort_values(DATE_COL)

    result["Open Interest Change"] = (
        result.groupby(
            "CFTC_Contract_Market_Code"
        )["Open_Interest_All"].diff()
    )

    latest = (
        result.dropna(
            subset=["Open Interest Change"]
        )
        .groupby(
            "CFTC_Contract_Market_Code"
        )
        .tail(1)
        .sort_values(
            "Open Interest Change",
            ascending=True,
        )
    )

    return plot_change_bar(
        latest=latest,
        value_column="Open Interest Change",
        xaxis_title="Weekly Open Interest Change (Contracts)",
        hover_label="Open Interest Change",
    )


def plot_net_by_trader_group(df):

    result = prepare_chart_data(df)

    fig = go.Figure()

    colors = {
        "Managed Money": AC,
        "Producer/Merchant": UPC,
        "Swap Dealer": OR,
        "Other Reportables": DNC,
        "Total Reportables": "#7651A8",
    }

    for trader_group, columns in TRADER_GROUPS.items():

        long_col = get_position_column(
            result,
            columns["long"],
        )

        short_col = get_position_column(
            result,
            columns["short"],
        )

        if long_col is None or short_col is None:
            continue

        net = result[long_col] - result[short_col]

        fig.add_trace(
            go.Scatter(
                x=result[DATE_COL],
                y=net,
                name=trader_group,
                mode="lines+markers",
                marker=dict(size=3),
                line=dict(
                    color=colors.get(trader_group, MU),
                    width=2 if trader_group == "Managed Money" else 1.5,
                ),
            )
        )

    fig.add_hline(
        y=0,
        line_color=MU,
        line_width=1,
    )

    update_date_axis(fig, result)

    return apply_layout(
        fig,
        yaxis_title="Net Position (Contracts)",
    )


def prepare_seasonal_yearly_data(df, value_column):

    result = prepare_chart_data(df)

    if value_column not in result.columns:
        return pd.DataFrame()

    result[value_column] = pd.to_numeric(
        result[value_column],
        errors="coerce",
    )

    result = result.dropna(
        subset=[value_column]
    )

    if result.empty:
        return pd.DataFrame()

    result["Year"] = result[DATE_COL].dt.year
    result["Month"] = result[DATE_COL].dt.month

    result = (
        result.groupby(
            ["Year", "Month"],
            as_index=False,
        )
        .last()
        .sort_values(["Year", "Month"])
    )

    return result


def plot_seasonal_yearly_lines(
    df,
    value_column,
    yaxis_title,
):

    result = prepare_seasonal_yearly_data(
        df,
        value_column,
    )

    fig = go.Figure()

    if result.empty:
        return apply_layout(
            fig,
            yaxis_title=yaxis_title,
        )

    years = sorted(result["Year"].unique())
    latest_year = max(years)

    colors = [
        MU,
        "#9AA3AE",
        "#8A9B83",
        OR,
        UPC,
        AC,
    ]

    for index, year in enumerate(years):

        yearly = result[
            result["Year"] == year
        ].sort_values("Month")

        is_latest = year == latest_year

        fig.add_trace(
            go.Scatter(
                x=yearly["Month"],
                y=yearly[value_column],
                name=str(year),
                mode="lines+markers",
                marker=dict(
                    size=5 if is_latest else 3,
                ),
                line=dict(
                    color=AC if is_latest else colors[index % len(colors)],
                    width=2.8 if is_latest else 1.5,
                ),
            )
        )

    fig.update_xaxes(
        title_text="Calendar Month",
        tickmode="array",
        tickvals=MONTH_TICK_VALUES,
        ticktext=CALENDAR_MONTH_TICK_TEXT,
        range=[0.7, 12.3],
        showgrid=False,
    )

    return apply_layout(
        fig,
        yaxis_title=yaxis_title,
    )


def plot_seasonal_open_interest(df):

    return plot_seasonal_yearly_lines(
        df=df,
        value_column="Open_Interest_All",
        yaxis_title="Open Interest (Contracts)",
    )


def plot_seasonal_net_position(
    df,
    trader_group="Managed Money",
):

    if trader_group not in TRADER_GROUPS:
        return go.Figure()

    columns = TRADER_GROUPS[trader_group]

    long_col = get_position_column(
        df,
        columns["long"],
    )

    short_col = get_position_column(
        df,
        columns["short"],
    )

    if long_col is None or short_col is None:
        return go.Figure()

    result = prepare_chart_data(df)

    result["Net Position"] = (
        result[long_col] - result[short_col]
    )

    return plot_seasonal_yearly_lines(
        df=result,
        value_column="Net Position",
        yaxis_title="Net Position (Contracts)",
    )


def plot_cross_commodity_open_interest(df):

    result = prepare_chart_data(df)

    required_columns = [
        "Market_and_Exchange_Names",
        "Open_Interest_All",
    ]

    if any(col not in result.columns for col in required_columns):
        return go.Figure()

    result["Open_Interest_All"] = pd.to_numeric(
        result["Open_Interest_All"],
        errors="coerce",
    )

    result = result.dropna(
        subset=required_columns
    )

    if result.empty:
        return go.Figure()

    latest = (
        result.sort_values(DATE_COL)
        .groupby("Market_and_Exchange_Names")
        .tail(1)
        .sort_values("Open_Interest_All")
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=latest["Open_Interest_All"],
            y=latest["Market_and_Exchange_Names"],
            orientation="h",
            marker_color=AC,
            text=latest["Open_Interest_All"].map(
                lambda value: f"{value:,.0f}"
            ),
            textposition="outside",
            cliponaxis=False,
            name="Open Interest",
            showlegend=False,
        )
    )

    fig.update_layout(
        height=CARD_HEIGHT,
        showlegend=False,
        margin=dict(l=10, r=65, t=45, b=35),
        xaxis_title="Open Interest (Contracts)",
        yaxis_title=None,
    )

    return fig