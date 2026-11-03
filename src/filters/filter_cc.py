
import pandas as pd
import streamlit as st


def _available_values(df, column):

    if df.empty or column not in df.columns:
        return []

    return sorted(
        df[column]
        .dropna()
        .unique()
        .tolist(),
        key=str,
    )


def render_cc_filters(
    df,
    key,
    include_state=False,
    week_df=None,
):

    if df.empty:
        return {}

    if include_state:
        col1, col2, col3, col4, col5 = st.columns(
            [1, 1, 1, 1, 10]
        )
    else:
        col1, col2, col3, col4 = st.columns(
            [1, 1, 1, 10]
        )

    crop_types = _available_values(
        df,
        "Crop Type",
    )

    if not crop_types:
        return {}

    with col1:
        crop_type = st.selectbox(
            "Crop Type",
            crop_types,
            key=f"{key}_crop_type",
        )

    filtered = df.loc[
        df["Crop Type"] == crop_type
    ]

    commodities = _available_values(
        filtered,
        "Commodity",
    )

    commodity = commodities[0] if commodities else None

    years = [
        int(year)
        for year in _available_values(filtered, "Year")
        if pd.notna(year)
    ]

    with col2:
        year = st.selectbox(
            "Year",
            years,
            index=len(years) - 1 if years else 0,
            key=f"{key}_year",
        ) if years else None

    selected_state = None

    if include_state:
        states = _available_values(
            filtered,
            "State",
        )

        with col3:
            selected_state = st.selectbox(
                "State",
                states,
                key=f"{key}_state",
            ) if states else None

    selected_week = None

    if week_df is not None and year is not None:

        week_data = week_df.loc[
            (week_df["Crop Type"] == crop_type)
            & (week_df["Year"] == year)
        ]

        if commodity is not None:
            week_data = week_data.loc[
                week_data["Commodity"] == commodity
            ]

        if include_state and selected_state is not None:
            week_data = week_data.loc[
                week_data["State"] == selected_state
            ]

        weeks = sorted(
            week_data["Week"]
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        )

        week_column = col4 if include_state else col3

        with week_column:
            selected_week = st.selectbox(
                "Comparison Week",
                weeks,
                index=len(weeks) - 1 if weeks else 0,
                format_func=lambda value: f"W{value:02d}",
                key=f"{key}_week",
            ) if weeks else None

    return {
        "commodity": commodity,
        "crop_type": crop_type,
        "year": year,
        "state": selected_state,
        "week": selected_week,
    }


def filter_cc_data(
    df,
    commodity,
    crop_type,
    year=None,
    state=None,
):

    data = df.loc[
        (df["Commodity"] == commodity)
        & (df["Crop Type"] == crop_type)
    ].copy()

    if year is not None:
        data = data.loc[
            data["Year"] == year
        ]

    if state is not None:
        data = data.loc[
            data["State"] == state
        ]

    return data
