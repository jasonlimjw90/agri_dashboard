import pandas as pd
import streamlit as st

from src.config.labels import CALENDAR_MONTH_TICK_TEXT

from src.tables.snd_table import (
    prepare_current_my_data,
    render_current_my_table,
    render_historical_table,
    render_country_monthly_table,
    render_country_historical_table,
    format_wasde_item,
    _ordered_items,
)

from src.components.cards import (
    render_change_view_toggle,
    render_change_cards,
    cards,
    render_country_historical_cards,
    format_marketing_year,
)

from src.components.layout import section_header

from src.filters.filter_time import render_report_month_filter

from src.components.charts import (
    country_monthly_change_history_fig,
)


COUNTRY_ITEMS = {
    "Production": "production",
    "Exports": "exports",
    "Imports": "imports",
    "Consumption": "domestic total",
}

EXCLUDED_COUNTRIES = {
    "world",
    "world less china",
    "total foreign",
    "major exporters",
    "major importers",
}


def _get_card_items(
    df: pd.DataFrame,
    label_prefix: str = "World",
) -> dict:

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


def _get_top_countries(
    country_df: pd.DataFrame,
    ranking_item: str = "exports",
    top_n: int = 5,
) -> list:

    if country_df.empty:
        return []

    ranking_df = country_df[
        country_df["snd_item"] == ranking_item
    ]

    if ranking_df.empty:
        return []

    ranking_df = ranking_df[
        ~ranking_df["country"].str.casefold().isin(EXCLUDED_COUNTRIES)
    ]

    if ranking_df.empty:
        return []

    latest_crop_year = ranking_df["crop year"].max()

    ranking_df = ranking_df[
        ranking_df["crop year"] == latest_crop_year
    ]

    return (
        ranking_df
        .sort_values("Report Date")
        .drop_duplicates(
            subset=["country"],
            keep="last",
        )
        .sort_values("Value", ascending=False)
        ["country"]
        .head(top_n)
        .tolist()
    )


def render_current_my_view(
    df: pd.DataFrame,
    seasonal_df: pd.DataFrame,
    commodity: str,
    cols: int = 2,
):

    current_my_data, _ = prepare_current_my_data(df)

    card_items = _get_card_items(
        current_my_data,
        label_prefix=str(current_my_data["country"].iloc[0]),
    )

    if card_items:

        selected_view = render_change_view_toggle(
            key="current_my"
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
                        prefix=f"current_my_{start}_{i}",
                        commodity=commodity,
                        change_df=current_my_data,
                        seasonal_df=seasonal_df,
                        selected_view=selected_view,
                    )

    section_header("Balance Sheet MoM Change")

    st.caption(
        "Monthly WASDE estimates from May to the latest available "
        "report. Change shows the revision versus the previous "
        "available observation for each item."
    )

    render_current_my_table(
        current_my_data,
        prepared=True,
    )


def render_global_balance_view(
    market_df: pd.DataFrame,
    seasonal_df: pd.DataFrame,
    commodity: str,
    years: int = 5,
    cols: int = 4,
    key_prefix: str = "global_snd_historical",
    card_prefix: str = "global_balance",
    label_prefix: str = "World",
    report_month: int = None,
):

    if seasonal_df.empty:
        st.info("No world balance sheet data available.")
        return

    card_items = _get_card_items(
        seasonal_df,
        label_prefix=label_prefix,
    )

    if not card_items:
        st.info("No world balance sheet items available.")
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

    section_header("Balance Sheet")

    render_historical_table(seasonal_df)


def render_country_analysis_view(
    country_df: pd.DataFrame,
    country_change_df: pd.DataFrame,
    commodity: str,
    years: int = 5,
    ranking_item: str = "exports",
    key_prefix: str = "country_analysis",
):

    if country_df.empty:
        st.info("No country-level WASDE data available.")
        return

    country_df = country_df[
        ~country_df["country"].str.casefold().isin(EXCLUDED_COUNTRIES)
    ]

    top_countries = _get_top_countries(
        country_df,
        ranking_item=ranking_item,
        top_n=5,
    )

    if not top_countries:
        st.info(
            f"No data available for ranking countries by {ranking_item}."
        )
        return

    report_month = render_report_month_filter(
        country_df,
        key_prefix=key_prefix,
    )

    if report_month is None:
        return

    selected_metric = st.segmented_control(
        "Metric",
        options=list(COUNTRY_ITEMS.keys()),
        default="Production",
        key=f"{key_prefix}_metric",
        label_visibility="collapsed",
        width=500,
    )

    if selected_metric is None:
        return

    snd_item = COUNTRY_ITEMS[selected_metric]
    title = selected_metric

    item_df = country_df[
        (country_df["snd_item"] == snd_item)
        & (country_df["country"].isin(top_countries))
    ]

    if item_df.empty:
        st.info(f"No data available for {title}.")
        return

    report_month_name = CALENDAR_MONTH_TICK_TEXT[report_month - 1]
    previous_month_name = CALENDAR_MONTH_TICK_TEXT[(report_month - 2) % 12]

    st.subheader(
        f"Major Exporters {title} Change: "
        f"{report_month_name} vs {previous_month_name}"
    )

    revision_df = country_change_df[
        (country_change_df["snd_item"] == snd_item)
        & (
            country_change_df["Report Date"].dt.month
            == report_month
        )
        & (
            country_change_df["country"].isin(top_countries)
        )
    ]

    if revision_df.empty:
        st.info(
            "No monthly revision data available "
            "for the selected report month."
        )
    else:

        columns = st.columns(5, gap="small", border=True)

        for i, country in enumerate(top_countries):

            country_revision_df = revision_df[
                revision_df["country"] == country
            ].copy()

            if country_revision_df.empty:
                continue

            with columns[i]:

                fig = country_monthly_change_history_fig(
                    df=country_revision_df,
                    countries=[country],
                )

                fig.update_layout(
                    title=dict(
                        text=country,
                        x=0.5,
                        xanchor="center",
                    )
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                    config={"displayModeBar": False},
                    key=(
                        f"{key_prefix}_monthly_revision_"
                        f"{snd_item}_{commodity}_{country}"
                    ),
                )

        current_crop_year = item_df["crop year"].max()
        current_my = format_marketing_year(int(current_crop_year))

        st.subheader(
            f"{current_my} {title} MoM Change"
        )

    render_country_monthly_table(
        item_df,
        countries=top_countries,
        report_month=report_month,
    )

    st.subheader(
        f"Historical {title}"
    )

    render_country_historical_cards(
        df=item_df,
        countries=top_countries,
        prefix=f"{key_prefix}|{snd_item}|{commodity}",
        years=years,
        title=title,
    )

    render_country_historical_table(
        item_df,
        countries=top_countries,
        years=10,
    )