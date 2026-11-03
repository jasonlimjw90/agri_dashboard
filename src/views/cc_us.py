
import streamlit as st

from src.transforms.transform_cc import (
    prepare_cc_base_data,
    prepare_national_cc_data,
    prepare_state_cc_data,
)

from src.filters.filter_cc import (
    render_cc_filters,
)

from src.components.cc_charts import (
    seasonal_ge_fig,
    weekly_condition_fig,
    state_comparison_bar_fig,
)

from src.tables.cc_table import (
    prepare_cc_ge_seasonal,
    prepare_cc_weekly_table,
    prepare_national_cc_comparison,
    prepare_national_cc_historical,
    prepare_state_cc_table,
    prepare_state_cc_ge_chart_data,
    render_national_cc_comparison_table,
    render_national_cc_historical_table,
    render_state_cc_comparison_table,
)


def _render_national(national_df):

    filters = render_cc_filters(
        national_df,
        key="cc_national",
        week_df=national_df,
    )

    if not filters:
        st.info("No national crop condition data available.")
        return

    commodity = filters["commodity"]
    crop_type = filters["crop_type"]
    year = filters["year"]
    selected_week = filters["week"]

    if year is None:
        st.info("No national crop condition data available.")
        return

    seasonal_df = prepare_cc_ge_seasonal(
        df=national_df,
        commodity=commodity,
        crop_type=crop_type,
        geo_level="NATIONAL",
    )

    weekly_df = prepare_cc_weekly_table(
        df=national_df,
        commodity=commodity,
        crop_type=crop_type,
        year=year,
        geo_level="NATIONAL",
    )

    historical_df = prepare_national_cc_historical(
        df=national_df,
        commodity=commodity,
        crop_type=crop_type,
        year=year,
    )

    st.subheader("National Crop Conditions")

    chart_columns = st.columns(2)

    with chart_columns[0]:
        with st.container(border=True):
            st.plotly_chart(
                seasonal_ge_fig(
                    df=seasonal_df,
                    latest_year=year,
                    crop_type=crop_type,
                    title="Good + Excellent — Seasonal Progress",
                    yaxis_range=[10, 80],
                ),
                width="stretch",
            )

    with chart_columns[1]:
        with st.container(border=True):
            st.plotly_chart(
                weekly_condition_fig(
                    df=weekly_df,
                    title=f"{year} — Weekly Condition Distribution",
                ),
                width="stretch",
            )

    if selected_week is None:
        st.info("No national comparison weeks available.")
        return

    comparison_df = prepare_national_cc_comparison(
        df=national_df,
        commodity=commodity,
        crop_type=crop_type,
        year=year,
        week=int(selected_week),
    )

    render_national_cc_comparison_table(
        comparison_df,
        year,
        selected_week,
    )

    render_national_cc_historical_table(
        historical_df,
        year,
    )


def _render_state(state_df, state_table_df):

    filters = render_cc_filters(
        state_df,
        key="cc_state",
        include_state=True,
        week_df=state_table_df,
    )

    if not filters:
        st.info("No state crop condition data available.")
        return

    commodity = filters["commodity"]
    crop_type = filters["crop_type"]
    year = filters["year"]
    state = filters["state"]
    selected_week = filters["week"]

    if year is None or state is None:
        st.info("No state crop condition data available.")
        return

    seasonal_df = prepare_cc_ge_seasonal(
        df=state_df,
        commodity=commodity,
        crop_type=crop_type,
        geo_level="STATE",
        state=state,
    )

    weekly_df = prepare_cc_weekly_table(
        df=state_df,
        commodity=commodity,
        crop_type=crop_type,
        year=year,
        geo_level="STATE",
        state=state,
    )

    st.subheader(f"{state} Crop Conditions")

    chart_columns = st.columns(3)

    with chart_columns[0]:
        with st.container(border=True):
            st.plotly_chart(
                seasonal_ge_fig(
                    df=seasonal_df,
                    latest_year=year,
                    crop_type=crop_type,
                    title=f"{state} — Good + Excellent Seasonal Progress",
                ),
                width="stretch",
            )

    with chart_columns[1]:
        with st.container(border=True):
            st.plotly_chart(
                weekly_condition_fig(
                    df=weekly_df,
                    title=f"{state} — {year} Weekly Condition Distribution",
                ),
                width="stretch",
            )

    if selected_week is None:
        st.info("No state comparison weeks available.")
        return

    comparison_df = prepare_state_cc_table(
        df=state_table_df,
        commodity=commodity,
        crop_type=crop_type,
        year=year,
        week=int(selected_week),
    )

    chart_df = prepare_state_cc_ge_chart_data(
        comparison_df,
    )

    st.subheader("Good + Excellent — State Comparison")
    st.caption(
        f"Week {int(selected_week):02d}, {year}"
    )

    if chart_df.empty:
        st.info("No Good + Excellent state comparison data available.")
    else:
        with chart_columns[2]:
            with st.container(border=True):
                st.plotly_chart(
                    state_comparison_bar_fig(
                        df=chart_df,
                        value_column="Current Week",
                        title="Current Week — Good + Excellent",
                    ),
                    width="stretch",
                )

        change_columns = st.columns(3)

        with change_columns[0]:
            with st.container(border=True):
                st.plotly_chart(
                    state_comparison_bar_fig(
                        df=chart_df,
                        value_column="Week Diff",
                        title="Week-on-Week Change",
                        change=True,
                    ),
                    width="stretch",
                )

        with change_columns[1]:
            with st.container(border=True):
                st.plotly_chart(
                    state_comparison_bar_fig(
                        df=chart_df,
                        value_column="Year Diff",
                        title="Year-on-Year Change",
                        change=True,
                    ),
                    width="stretch",
                )

        with change_columns[2]:
            with st.container(border=True):
                st.plotly_chart(
                    state_comparison_bar_fig(
                        df=chart_df,
                        value_column="5Y Avg Diff",
                        title="Difference from 5-Year Average",
                        change=True,
                    ),
                    width="stretch",
                )

    st.subheader("Good + Excellent — State Condition Comparison")

    render_state_cc_comparison_table(
        comparison_df,
        week=int(selected_week),
    )


def render_cc_us(df):

    base_df = prepare_cc_base_data(df)

    national_df = prepare_national_cc_data(base_df)
    state_df = prepare_state_cc_data(base_df)

    national_tab, state_tab = st.tabs(
        ["National", "State"]
    )

    with national_tab:
        _render_national(national_df)

    with state_tab:
        _render_state(
            state_df,
            state_df,
        )
