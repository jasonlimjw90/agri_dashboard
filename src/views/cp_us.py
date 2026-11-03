import pandas as pd
import streamlit as st

from src.transforms.transform_cp import (
    is_five_year_average,
    get_chronological_measure_order,
    prepare_seasonal_data,
)

from src.filters.filter_cp import (
    render_crop_type_filter,
    render_measure_filter,
    render_year_filter,
    render_week_filter,
)

from src.components.cp_charts import (
    national_all_stages_fig,
    state_comparison_fig,
    seasonal_history_fig,
    weekly_progress_fig,
)

from src.tables.cp_table import (
    prepare_national_progress_table,
    render_national_progress_table,
    prepare_state_comparison_table,
    render_state_comparison_table,
)


def _render_market_filters(
    df,
    key_prefix,
    year_filter=False,
):
    if year_filter:
        col1, col2, _ = st.columns([1, 1, 10])
    else:
        col1, _ = st.columns([1, 10])

    with col1:
        crop_type = render_crop_type_filter(
            df,
            key_prefix,
        )

    if crop_type is None:
        return None, None

    if not year_filter:
        return crop_type, None

    crop_df = df.loc[
        df["Crop Type"] == crop_type
    ]

    actual_crop_df = crop_df.loc[
        ~is_five_year_average(crop_df)
    ]

    with col2:
        year = render_year_filter(
            actual_crop_df,
            key_prefix,
        )

    return crop_type, year


def render_national(
    national_df: pd.DataFrame,
) -> None:

    if national_df.empty:
        st.info("No national crop progress data available.")
        return

    crop_type, year = _render_market_filters(
        national_df,
        "cp_national",
        year_filter=True,
    )

    if crop_type is None or year is None:
        return

    year = int(year)

    crop_df = national_df.loc[
        national_df["Crop Type"] == crop_type
    ].copy()

    actual_crop_df = crop_df.loc[
        ~is_five_year_average(crop_df)
    ].copy()

    year_df = actual_crop_df.loc[
        actual_crop_df["Year"] == year
    ].copy()

    if year_df.empty:
        st.info(f"No crop progress data available for {year}.")
        return

    is_winter_wheat = crop_type == "Winter Wheat"

    fig = national_all_stages_fig(
        df=crop_df,
        crop_type=crop_type,
        year=year,
        title=f"{crop_type} Progress",
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key="cp_national_all_stages_chart",
    )

    seasonal_data = prepare_seasonal_data(
        df=national_df,
        crop_type=crop_type,
        geography="NATIONAL",
    )

    latest_report_date = year_df[
        "Week Ending"
    ].max()

    average_mask = is_five_year_average(crop_df)

    measure_order_data = pd.concat(
        [
            crop_df.loc[
                ~average_mask
                & crop_df["Year"].isin([year - 1, year]),
                ["Measure", "Week"],
            ],
            crop_df.loc[
                average_mask
                & (crop_df["Year"] == year),
                ["Measure", "Week"],
            ],
        ],
        ignore_index=True,
    )

    chronological_measures = get_chronological_measure_order(
        measure_order_data
    )

    current_year_measures = set(
        year_df["Measure"].dropna().unique()
    )

    available_measures = [
        measure
        for measure in chronological_measures
        if measure in current_year_measures
    ]

    if not available_measures:
        st.info("No progress stages available for this year.")
        return

    latest_report_measures = (
        year_df.loc[
            year_df["Week Ending"] == latest_report_date,
            "Measure",
        ]
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    default_measure = next(
        (
            measure
            for measure in available_measures
            if measure in latest_report_measures
        ),
        available_measures[0],
    )

    measure_col, _ = st.columns([1, 10])

    with measure_col:
        measure = st.selectbox(
            "Stage",
            options=available_measures,
            index=available_measures.index(default_measure),
            key=(
                f"cp_national_measure_"
                f"{crop_type}_{year}"
            ),
            width=200,
        )

    measure_series = seasonal_data.get(
        measure,
        {},
    )

    if measure_series:
        seasonal_fig = seasonal_history_fig(
            series=measure_series,
            title=f"{measure} - Seasonal Progress",
            current_year=year,
            season_start_week=33 if is_winter_wheat else None,
        )

        st.plotly_chart(
            seasonal_fig,
            width="stretch",
            key="cp_national_seasonal_chart",
        )
    else:
        st.info(
            "No seasonal data available for this stage."
        )

    st.divider()

    comparison_data = year_df.loc[
        year_df["Measure"] == measure
    ].copy()

    week_dates = (
        comparison_data
        .dropna(subset=["Week", "Week Ending"])
        .sort_values(["Week", "Week Ending"])
        .drop_duplicates("Week", keep="last")
    )

    if week_dates.empty:
        st.info(
            "No weekly comparison data available for this stage."
        )
    else:
        available_weeks = (
            week_dates["Week"]
            .astype(int)
            .sort_values()
            .tolist()
        )

        latest_measure_report = week_dates[
            "Week Ending"
        ].max()

        latest_week = int(
            week_dates.loc[
                week_dates["Week Ending"] == latest_measure_report,
                "Week",
            ].iloc[-1]
        )

        week_col, _ = st.columns([1, 10])

        with week_col:
            selected_week = st.selectbox(
                "Week",
                options=available_weeks,
                index=available_weeks.index(latest_week),
                format_func=lambda value: f"Week {value}",
                key=(
                    f"cp_national_comparison_week_"
                    f"{crop_type}_{measure}_{year}"
                ),
                width=200,
            )

        st.subheader(
            f"Week {selected_week} Historical Comparison"
        )

        selected_week_date = week_dates.loc[
            week_dates["Week"] == selected_week,
            "Week Ending",
        ].max()

        if pd.notna(selected_week_date):
            st.caption(
                f"Week ending: {selected_week_date:%d %b %Y}"
            )

        weekly_fig = weekly_progress_fig(
            df=crop_df,
            crop_type=crop_type,
            measure=measure,
            week=selected_week,
            current_year=year,
            title=(
                f"{crop_type} {measure} "
                f"- Week {selected_week} Comparison"
            ),
        )

        st.plotly_chart(
            weekly_fig,
            width="stretch",
            key="cp_national_weekly_comparison_chart",
        )

    st.divider()

    st.subheader(f"National Progress Table - {measure}")

    table = prepare_national_progress_table(
        df=national_df,
        measure=measure,
        crop_type=crop_type,
        year=year,
    )

    render_national_progress_table(table)


def render_state(
    state_df: pd.DataFrame,
    state_table_df: pd.DataFrame,
) -> None:

    if state_df.empty:
        st.info("No state crop progress data available.")
        return

    crop_type, year = _render_market_filters(
        state_df,
        "cp_state",
        year_filter=True,
    )

    if crop_type is None or year is None:
        return

    year = int(year)
    map_year = year

    crop_df = state_df.loc[
        state_df["Crop Type"] == crop_type
    ].copy()

    map_source = crop_df.loc[
        crop_df["Year"] == map_year
    ].copy()

    if map_source.empty:
        st.info(
            f"No {map_year} state crop progress data available."
        )
        return

    stage_col, week_col, _ = st.columns([1, 1, 10])

    with stage_col:
        measure = render_measure_filter(
            map_source,
            "cp_state",
        )

    if measure is None:
        return

    measure_df = map_source.loc[
        map_source["Measure"] == measure
    ].copy()

    with week_col:
        selected_week = render_week_filter(
            measure_df,
            f"cp_state_{measure}",
        )

    if selected_week is None:
        return

    selected_week = int(selected_week)

    selected_week_data = measure_df.loc[
        measure_df["Week"] == selected_week
    ].copy()

    selected_week_date = selected_week_data[
        "Week Ending"
    ].max()

    map_df = prepare_state_comparison_table(
        df=state_df,
        measure=measure,
        year=map_year,
        crop_type=crop_type,
        week=selected_week,
    )

    comparison_df = prepare_state_comparison_table(
        df=state_table_df,
        measure=measure,
        year=year,
        crop_type=crop_type,
        week=selected_week,
    )

    map_col, table_col = st.columns([1.2, 1])

    with map_col:
        st.subheader("State Progress Map")

        if pd.notna(selected_week_date):
            st.caption(
                f"Week {selected_week:02d} ending "
                f"{selected_week_date:%d %b %Y}"
            )
        else:
            st.caption(
                f"Week {selected_week:02d}, {map_year}"
            )

        if (
            map_df.empty
            or str(map_year) not in map_df.columns
            or map_df[str(map_year)].isna().all()
        ):
            st.info(
                f"No state progress data available for "
                f"{measure}, Week {selected_week:02d}, {map_year}."
            )
        else:
            fig = state_comparison_fig(
                df=map_df,
                year=map_year,
                title=(
                    f"{crop_type} {measure} "
                    f"- Week {selected_week:02d}, {map_year}"
                ),
            )

            st.plotly_chart(
                fig,
                width="stretch",
                key="cp_state_progress_map",
            )

    with table_col:
        st.subheader(
            f"State Progress Comparison ({year})"
        )

        st.caption(
            f"Week {selected_week:02d}"
        )

        render_state_comparison_table(
            comparison_df
        )