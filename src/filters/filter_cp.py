import pandas as pd
import streamlit as st

from src.transforms.transform_cp import (
    get_chronological_measure_order,
)


def render_crop_type_filter(
    df,
    key_prefix="cp",
):
    if df.empty or "Crop Type" not in df.columns:
        return None

    crop_types = sorted(
        df["Crop Type"].dropna().unique().tolist()
    )

    if not crop_types:
        return None

    return st.selectbox(
        "Crop Type",
        options=crop_types,
        key=f"{key_prefix}_crop_type",
        width=200,
    )


def render_measure_filter(
    df,
    key_prefix="cp",
):
    if df.empty or "Measure" not in df.columns:
        return None

    measures = get_chronological_measure_order(
        df
    )

    if not measures:
        return None

    return st.selectbox(
        "Stage",
        options=measures,
        key=f"{key_prefix}_measure",
        width=200,
    )


def render_year_filter(
    df,
    key_prefix="cp",
):
    if df.empty or "Year" not in df.columns:
        return None

    years = sorted(
        pd.to_numeric(
            df["Year"],
            errors="coerce",
        ).dropna().astype(int).unique().tolist()
    )

    if not years:
        return None

    return st.selectbox(
        "Year",
        options=years,
        index=len(years) - 1,
        key=f"{key_prefix}_year",
        width=200,
    )


def render_week_filter(
    df,
    key_prefix="cp",
):
    if df.empty or "Week" not in df.columns:
        return None

    weeks = sorted(
        pd.to_numeric(
            df["Week"],
            errors="coerce",
        ).dropna().astype(int).unique().tolist()
    )

    if not weeks:
        return None

    return st.selectbox(
        "Week",
        options=weeks,
        index=len(weeks) - 1,
        format_func=lambda week: f"Week {week:02d}",
        key=f"{key_prefix}_week",
        width=200,
    )