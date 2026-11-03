import pandas as pd
import streamlit as st

from src.config.labels import MONTHS


def render_report_month_filter(
    df,
    key_prefix="report",
    date_column="Report Date",
):
    if df.empty or date_column not in df.columns:
        st.info("No report dates available.")
        return None

    dates = pd.to_datetime(
        df[date_column],
        errors="coerce",
    ).dropna()

    if dates.empty:
        st.info("No valid report dates available.")
        return None

    available_months = sorted(
        dates.dt.month.unique().tolist()
    )

    latest_month = int(dates.max().month)

    default_month = (
        latest_month
        if latest_month in available_months
        else available_months[-1]
    )

    report_month = st.selectbox(
        "Report Month",
        options=available_months,
        index=available_months.index(default_month),
        format_func=lambda month: MONTHS[month - 1],
        key=f"{key_prefix}_report_month",
        width=200,
    )

    return report_month