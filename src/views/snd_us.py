
import pandas as pd
import streamlit as st

from src.tables.snd_table import (
    prepare_current_my_data,
    prepare_current_report_table,
    render_current_my_table,
    render_historical_table,
    render_current_report_table,
    format_wasde_item,
    _ordered_items,
)

from src.components.cards import (
    render_change_view_toggle,
    render_change_cards,
    cards,
)

from src.components.charts import (
    monthly_change_history_fig,
    current_report_change_fig,
)

from src.components.layout import section_header

from src.filters.filter_time import render_report_month_filter


MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def _get_card_items(
    df,
    label_prefix="US",
):

    if df.empty:
        return {}

    snd_items = (
        df["snd_item"]
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    ordered_items = _ordered_items(snd_items)

    return {
        f"{label_prefix} {format_wasde_item(item)}": item
        for item in ordered_items
    }


def render_current_my_view(
    df,
    seasonal_df,
    commodity,
    current_report_df=None,
    cols=2,
    label_prefix="US",
    key_prefix="us_current_my",
):

    current_my_data, _ = prepare_current_my_data(df)

    card_items = _get_card_items(
        current_my_data,
        label_prefix=label_prefix,
    )

    if card_items:

        selected_view = render_change_view_toggle(
            key=key_prefix
        )

        item_list = list(card_items.items())

        n_cols = max(
            1,
            min(4, len(item_list)),
        )

        for start in range(0, len(item_list), n_cols):

            row_items = item_list[start:start + n_cols]

            columns = st.columns(
                n_cols,
                gap="medium",
            )

            for i, (title, snd_item) in enumerate(row_items):

                with columns[i]:

                    render_change_cards(
                        items={title: snd_item},
                        prefix=f"{key_prefix}_{start}_{i}",
                        commodity=commodity,
                        change_df=current_my_data,
                        seasonal_df=seasonal_df,
                        selected_view=selected_view,
                    )

    report_prepared = None

    if current_report_df is not None:
        report_prepared = prepare_current_report_table(
            current_report_df
        )

    col1, col2 = st.columns(
        [1, 1],
        gap="medium",
    )

    with col1:

        section_header("Latest WASDE Report")

        if report_prepared is not None and not report_prepared[0].empty:

            render_current_report_table(
                current_report_df,
                prepared=report_prepared,
            )

        else:
            st.info(
                "No current report comparison data available."
            )

    with col2:

        section_header(
            f"{label_prefix} Balance Sheet MoM Change"
        )

        st.caption(
            "Monthly WASDE estimates from May to the latest available "
            "report. Change shows the revision versus the previous "
            "available observation for each item."
        )

        render_current_my_table(
            current_my_data,
            prepared=True,
        )


def render_us_balance_view(
    market_df,
    seasonal_df,
    commodity,
    years=5,
    cols=4,
    key_prefix="us_balance",
    card_prefix="us_balance",
    label_prefix="US",
    report_month=None,
):

    if seasonal_df.empty:
        st.info("No US balance sheet data available.")
        return

    card_items = _get_card_items(
        seasonal_df,
        label_prefix=label_prefix,
    )

    if not card_items:
        st.info("No US balance sheet items available.")
        return

    cards(
        items=card_items,
        prefix=card_prefix,
        commodity=commodity,
        seasonal_df=seasonal_df,
        show_yoy_change=True,
        years=years,
        cols=cols,
    )

    section_header(
        f"{label_prefix} Balance Sheet"
    )

    render_historical_table(seasonal_df)


def render_us_monthly_change_view(
    change_df,
    key_prefix="us_monthly_change",
    label_prefix="US",
):

    if change_df.empty:
        st.info("No monthly revision data available.")
        return

    report_month = render_report_month_filter(
        change_df,
        key_prefix=f"{key_prefix}_report_month",
    )

    if report_month is None:
        return

    filtered_df = change_df[
        change_df["Report Date"].dt.month == report_month
    ].copy()

    if filtered_df.empty:
        st.info(
            "No monthly revision data available "
            "for the selected report month."
        )
        return

    previous_month = (
        12 if report_month == 1
        else report_month - 1
    )

    current_month_name = MONTH_NAMES[report_month]
    previous_month_name = MONTH_NAMES[previous_month]

    card_items = _get_card_items(
        filtered_df,
        label_prefix=label_prefix,
    )

    if not card_items:
        st.info("No balance sheet items available.")
        return

    st.subheader(
        f"{label_prefix} MoM Revisions by Marketing Year "
        f"({current_month_name} vs {previous_month_name})"
    )

    item_list = list(card_items.items())

    for start in range(0, len(item_list), 4):

        row_items = item_list[start:start + 4]

        columns = st.columns(
            4,
            gap="medium",
        )

        for i, (title, snd_item) in enumerate(row_items):

            item_df = filtered_df[
                filtered_df["snd_item"] == snd_item
            ].copy()

            with columns[i]:

                with st.container(border=True):

                    fig = monthly_change_history_fig(
                        df=item_df,
                        group_col=None,
                        title=title,
                    )

                    st.plotly_chart(
                        fig,
                        width="stretch",
                        config={"displayModeBar": False},
                        key=f"{key_prefix}_{start}_{i}_{snd_item}",
                    )


def render_us_current_report_view(
    df,
    key_prefix="us_current_report",
):

    prepared = prepare_current_report_table(df)

    table, _, _ = prepared

    if table.empty:
        st.info(
            "No current report comparison data available."
        )
        return

    section_header("Latest WASDE Report")

    render_current_report_table(
        df,
        prepared=prepared,
    )

    change_groups = [
        group
        for group in table.columns.get_level_values(0).unique()
        if (group, "Change") in table.columns
    ]

    if not change_groups:
        return

    chart_cols = st.columns(
        len(change_groups),
        gap="medium",
    )

    for i, group in enumerate(change_groups):

        chart_table = table.loc[
            :,
            table.columns.get_level_values(0) == group,
        ]

        with chart_cols[i]:

            with st.container(border=True):

                st.markdown(f"**{group}**")

                fig = current_report_change_fig(
                    chart_table
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                    config={"displayModeBar": False},
                    key=f"{key_prefix}_change_{i}",
                )
