
import pandas as pd
import streamlit as st

from src.filters.filter_cftc import (
    filter_cftc_market,
    filter_cftc_report,
    filter_cftc_date,
)

from src.transforms.transform_cftc import (
    DATE_COL,
    prepare_trader_positions,
)

from src.components.cftc_cot_charts import (
    get_available_cftc_years,
    plot_2026_cross_commodity_net_positions,
    plot_cross_commodity_weekly_net_change,
    plot_weekly_open_interest_change,
    plot_seasonal_open_interest,
    plot_seasonal_net_position,
    plot_cross_commodity_open_interest,
)

from src.tables.cftc_table import (
    render_cftc_position_table,
)


CHART_HEIGHT = 340
CHART_CARD_HEIGHT = 430
CHART_HEADER_HEIGHT = 65


def render_cftc_cards(df):

    if df.empty:
        return

    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else None

    net_change = (
        latest["Net"] - previous["Net"]
        if previous is not None
        else None
    )

    oi_change = (
        latest["Open Interest"] - previous["Open Interest"]
        if previous is not None
        else None
    )

    metrics = [
        ("Net Position", f"{latest['Net']:,.0f}"),
        (
            "Net Position Change",
            f"{net_change:+,.0f}" if net_change is not None else "N/A",
        ),
        ("Open Interest", f"{latest['Open Interest']:,.0f}"),
        (
            "Open Interest Change",
            f"{oi_change:+,.0f}" if oi_change is not None else "N/A",
        ),
    ]

    columns = st.columns(4, gap="medium")

    for column, (label, value) in zip(columns, metrics):

        with column:

            with st.container(border=True, height=110):

                st.caption(label)
                st.markdown(f"### {value}")


def render_cftc_chart_card(title, fig):

    with st.container(
        border=True,
        height=CHART_CARD_HEIGHT,
    ):

        st.markdown(
            f"**{title}**"
        )

        st.plotly_chart(
            fig,
            width="stretch",
            height=CHART_HEIGHT,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )


def render_cftc_view(
    df,
    market_code,
    commodity=None,
    report_type="Combined",
    trader_group="Managed Money",
    start_date=None,
    end_date=None,
):

    commodity_label = commodity or market_code

    report_df = filter_cftc_report(
        df,
        report_type,
    )

    market_df = filter_cftc_market(
        report_df,
        market_code,
    )

    market_df = market_df.sort_values(
        DATE_COL
    ).copy()

    position_raw_df = filter_cftc_date(
        market_df,
        start_date,
        end_date,
    )

    position_df = prepare_trader_positions(
        position_raw_df,
        trader_group,
    )

    position_df = position_df.sort_values(
        DATE_COL
    ).reset_index(drop=True)

    if position_df.empty:
        st.warning(
            "No CFTC positioning data is available for the selected filters."
        )
        return

    st.subheader("Positioning Summary")

    render_cftc_cards(position_df)

    st.divider()

    st.subheader("CFTC Positioning Charts")

    cross_commodity_df = filter_cftc_date(
        report_df,
        start_date,
        end_date,
    )

    latest_report_date = pd.to_datetime(
        cross_commodity_df[DATE_COL],
        errors="coerce",
    ).max()

    as_of_date = (
        latest_report_date.strftime("%d %b %Y")
        if pd.notna(latest_report_date)
        else "N/A"
    )

    row_1 = st.columns(3, gap="medium")

    with row_1[0]:
        render_cftc_chart_card(
            f"{commodity_label} — Seasonal Net Position ({trader_group})",
            plot_seasonal_net_position(
                market_df,
                trader_group,
            ),
        )

    with row_1[1]:
        render_cftc_chart_card(
            f"Weekly Net Position Change — {trader_group}",
            plot_cross_commodity_weekly_net_change(
                report_df,
                trader_group,
            ),
        )

    with row_1[2]:

        with st.container(
            border=True,
            height=CHART_CARD_HEIGHT,
        ):

            years = get_available_cftc_years(
                cross_commodity_df
            )

            if years:

                title_col, filter_col = st.columns(
                    [3, 1],
                    vertical_alignment="center",
                )

                with title_col:
                    st.markdown(
                        "**Managed Money Net Positions Across Agricultural Markets**"
                    )

                with filter_col:
                    selected_year = st.selectbox(
                        "Year",
                        options=years,
                        index=len(years) - 1,
                        key="cftc_cross_commodity_net_year",
                        label_visibility="collapsed",
                    )

                fig = plot_2026_cross_commodity_net_positions(
                    cross_commodity_df,
                    trader_group="Managed Money",
                    year=selected_year,
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                    height=CHART_HEIGHT,
                    config={
                        "displayModeBar": False,
                        "responsive": True,
                    },
                )

            else:
                st.info(
                    "No annual positioning data is available."
                )

    row_2 = st.columns(3, gap="medium")

    with row_2[0]:
        render_cftc_chart_card(
            f"{commodity_label} — Seasonal Open Interest",
            plot_seasonal_open_interest(market_df),
        )

    with row_2[1]:
        render_cftc_chart_card(
            "Weekly Open Interest Change Across Markets",
            plot_weekly_open_interest_change(
                report_df
            ),
        )

    with row_2[2]:
        render_cftc_chart_card(
            f"Cross-Commodity Open Interest (As of {as_of_date})",
            plot_cross_commodity_open_interest(
                cross_commodity_df
            ),
        )

    st.divider()

    st.subheader("Positioning Data")

    period = st.segmented_control(
        "Period",
        options=["1M", "6M", "1Y", "5Y"],
        default="1M",
        key="cftc_table_period",
    )

    period_months = {
        "1M": 1,
        "6M": 6,
        "1Y": 12,
        "5Y": 60,
    }

    latest_date = pd.to_datetime(
        position_df[DATE_COL],
        errors="coerce",
    ).max()

    table_start_date = (
        latest_date - pd.DateOffset(
            months=period_months[period]
        )
    )

    table_df = position_df[
        position_df[DATE_COL] >= table_start_date
    ].copy()

    table_df = table_df.sort_values(
        DATE_COL,
        ascending=False,
    ).reset_index(drop=True)

    render_cftc_position_table(table_df)
