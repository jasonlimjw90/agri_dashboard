
import pandas as pd
import streamlit as st

from src.components.charts import (
    seasonal_monthly_fig,
    seasonal_history_fig,
    historical_bars_fig,
    monthly_change_fig,
    country_historical_stacked_fig,
    country_historical_pie_fig,
    add_change_line,
)

from src.components.format_years import format_marketing_year

from src.tables.snd_table import prepare_yoy_change_data

from src.transforms.transform_df import (
    prepare_card_data,
    prepare_seasonal_series,
    prepare_history_data,
    prepare_monthly_change_data,
    filter_latest_month_offset,
)


CHANGE_CARD_VIEWS = [
    "5 Year",
    "Seasonal",
    "MoM Change",
]


def render_change_view_toggle(key: str) -> str:
    return st.segmented_control(
        "View",
        options=CHANGE_CARD_VIEWS,
        default="5 Year",
        key=f"change_view|{key}",
        label_visibility="collapsed",
        width=500,
    )


def _filter_card_data(
    df: pd.DataFrame,
    commodity: str,
    snd_item: str,
) -> pd.DataFrame:

    if df.empty:
        return df.copy()

    return df[
        (df["commodity"].astype(str).str.casefold() == commodity.casefold())
        & (df["snd_item"].astype(str).str.casefold() == snd_item.casefold())
    ].copy()


def _render_historical_card(
    title: str,
    key: str,
    seasonal_data: pd.DataFrame,
    series: dict,
    snd_item: str,
    yoy_df: pd.DataFrame = None,
    show_yoy_change: bool = False,
):

    with st.container(border=True):

        st.markdown(f"**{title}**")

        if not series:
            st.info(f"No historical data available for {title}.")
            return

        values, crop_years = prepare_history_data(
            seasonal_data,
            years=None,
        )

        labels = [
            format_marketing_year(int(year))
            for year in crop_years
        ]

        fig = historical_bars_fig(
            values,
            x_labels=labels,
        )

        if (
            show_yoy_change
            and yoy_df is not None
            and not yoy_df.empty
        ):

            yoy_card_data = yoy_df[
                (
                    yoy_df["snd_item"].astype(str).str.casefold()
                    == snd_item.casefold()
                )
                & (
                    yoy_df["crop year"].isin(crop_years)
                )
            ].copy()

            yoy_card_data = (
                yoy_card_data
                .drop_duplicates(
                    subset=["crop year"],
                    keep="last",
                )
                .set_index("crop year")
                .reindex(crop_years)
            )

            change_values = (
                pd.to_numeric(
                    yoy_card_data["YoY Change (%)"],
                    errors="coerce",
                )
                .to_numpy(
                    dtype=float,
                    na_value=float("nan"),
                    copy=True,
                )
            )

            if len(change_values) > 0:
                change_values[0] = float("nan")

            if not pd.isna(change_values).all():

                fig = add_change_line(
                    fig=fig,
                    x_values=labels,
                    change_values=change_values.tolist(),
                    name="YoY Change",
                )

        fig.update_layout(height=350)

        st.plotly_chart(
            fig,
            width="stretch",
            key=f"historical_chart|{key}",
        )


def _render_change_card(
    title: str,
    key: str,
    change_data: pd.DataFrame,
    seasonal_data: pd.DataFrame,
    series: dict,
    selected_view: str,
):

    with st.container(border=True):

        st.markdown(f"**{title}**")

        if selected_view == "5 Year":

            if not series:
                st.info(f"No historical data available for {title}.")
                return

            caption = "Average monthly values over the last 5 years."

            fig = seasonal_monthly_fig(
                series,
                years=5,
            )

        elif selected_view == "Seasonal":

            if not series:
                st.info(f"No historical data available for {title}.")
                return

            caption = "Historical monthly values by marketing year."

            fig = seasonal_history_fig(
                series,
                years=10,
            )

        else:

            if change_data.empty:
                st.info(f"No monthly change data available for {title}.")
                return

            latest = change_data.iloc[-1]

            latest_change = latest["Change"]
            latest_month = latest["Report Date"].strftime("%b %Y")

            caption = (
                f"Latest revision: {latest_change:+,.2f} "
                f"· {latest_month}"
            )

            fig = monthly_change_fig(
                data=change_data,
                title=title,
            )

        st.caption(caption)

        fig.update_layout(
            height=350,
            autosize=True,
        )

        st.plotly_chart(
            fig,
            width="stretch",
            key=f"change_chart|{key}|{selected_view}",
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )


def render_historical_cards(
    items: dict,
    prefix: str,
    commodity: str,
    seasonal_df: pd.DataFrame,
):

    for title, snd_item in items.items():

        seasonal_data = _filter_card_data(
            seasonal_df,
            commodity,
            snd_item,
        )

        seasonal_data = filter_latest_month_offset(
            seasonal_data,
        )

        seasonal_data = prepare_card_data(
            seasonal_data,
        )

        series = prepare_seasonal_series(
            seasonal_data,
        )

        if not series:
            st.info(f"No historical data available for {title}.")
            continue

        _render_historical_card(
            title=title,
            key=f"{prefix}|{title}|{commodity}",
            seasonal_data=seasonal_data,
            series=series,
            snd_item=snd_item,
        )


def render_change_cards(
    items: dict,
    prefix: str,
    commodity: str,
    change_df: pd.DataFrame,
    seasonal_df: pd.DataFrame,
    selected_view: str = "5 Year",
):

    for title, snd_item in items.items():

        change_data = _filter_card_data(
            change_df,
            commodity,
            snd_item,
        )

        change_data = prepare_monthly_change_data(
            change_data,
        )

        seasonal_data = _filter_card_data(
            seasonal_df,
            commodity,
            snd_item,
        )

        seasonal_data = prepare_card_data(
            seasonal_data,
        )

        series = prepare_seasonal_series(
            seasonal_data,
        )

        _render_change_card(
            title=title,
            key=f"{prefix}|{title}|{commodity}",
            change_data=change_data,
            seasonal_data=seasonal_data,
            series=series,
            selected_view=selected_view,
        )


def card(
    title: str,
    snd_item: str,
    key: str,
    commodity: str,
    seasonal_df: pd.DataFrame,
    change_df: pd.DataFrame = None,
    yoy_df: pd.DataFrame = None,
    show_yoy_change: bool = False,
):

    seasonal_data = _filter_card_data(
        seasonal_df,
        commodity,
        snd_item,
    )

    seasonal_data = filter_latest_month_offset(
        seasonal_data,
    )

    if show_yoy_change:
        yoy_df = prepare_yoy_change_data(
            seasonal_data,
        )

    seasonal_data = prepare_card_data(
        seasonal_data,
    )

    series = prepare_seasonal_series(
        seasonal_data,
    )

    if not series:
        st.info(f"No data available for {title}.")
        return

    _render_historical_card(
        title=title,
        key=key,
        seasonal_data=seasonal_data,
        series=series,
        snd_item=snd_item,
        yoy_df=yoy_df,
        show_yoy_change=show_yoy_change,
    )


def cards(
    items: dict,
    prefix: str,
    commodity: str,
    seasonal_df: pd.DataFrame,
    change_df: pd.DataFrame = None,
    years: int = 5,
    cols: int = 2,
    yoy_df: pd.DataFrame = None,
    show_yoy_change: bool = False,
):

    item_list = list(items.items())

    for start in range(0, len(item_list), cols):

        row_items = item_list[start:start + cols]

        columns = st.columns(
            cols,
            gap="medium",
        )

        for column, (title, snd_item) in zip(
            columns,
            row_items,
        ):

            with column:

                card(
                    title=title,
                    snd_item=snd_item,
                    key=f"{prefix}|{title}|{commodity}",
                    commodity=commodity,
                    seasonal_df=seasonal_df,
                    yoy_df=yoy_df,
                    show_yoy_change=show_yoy_change,
                )


def render_country_historical_cards(
    df: pd.DataFrame,
    countries: list,
    prefix: str,
    title: str,
    years: int = 5,
):

    df = filter_latest_month_offset(df)

    columns = st.columns(
        [0.5, 0.5],
        gap="medium",
    )

    with columns[0]:

        with st.container(border=True):

            st.markdown(f"**{title} by Country**")

            fig = country_historical_stacked_fig(
                df,
                countries=countries,
                years=None,
            )

            fig.update_layout(
                height=350,
                autosize=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.02,
                    font=dict(size=10),
                ),
            )

            st.plotly_chart(
                fig,
                width="stretch",
                key=f"{prefix}|stacked",
                config={"displayModeBar": False},
            )

    with columns[1]:

        with st.container(border=True):

            st.markdown(f"{title}")

            fig = country_historical_pie_fig(
                df,
                countries=countries,
            )

            fig.update_layout(
                height=350,
                autosize=True,
            )

            st.plotly_chart(
                fig,
                width="stretch",
                key=f"{prefix}|pie",
                config={"displayModeBar": False},
            )
