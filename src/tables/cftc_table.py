import pandas as pd
import streamlit as st


def render_cftc_position_table(df):
    if df.empty:
        st.info("No CFTC data available.")
        return

    table = df.copy()

    table["Report_Date_as_YYYY-MM-DD"] = pd.to_datetime(
        table["Report_Date_as_YYYY-MM-DD"],
        errors="coerce",
    )

    # Sort chronologically to calculate changes correctly
    table = table.sort_values(
        "Report_Date_as_YYYY-MM-DD",
        ascending=True,
    )

    if "Open Interest" in table.columns:
        table["Open Interest Change"] = (
            table["Open Interest"].diff()
        )

    if "Net % OI" in table.columns:
        table["Net % OI Change"] = (
            table["Net % OI"].diff()
        )

    # Display latest report date first
    table = table.sort_values(
        "Report_Date_as_YYYY-MM-DD",
        ascending=False,
    )

    columns = [
        "Report_Date_as_YYYY-MM-DD",
        "Long",
        "Short",
        "Spreading",
        "Net",
        "Net Change",
        "Open Interest",
        "Open Interest Change",
        "Long % OI",
        "Short % OI",
        "Net % OI",
        "Net % OI Change",
    ]

    columns = [
        col for col in columns
        if col in table.columns
    ]

    table = table[columns].copy()

    table["Report_Date_as_YYYY-MM-DD"] = (
        table["Report_Date_as_YYYY-MM-DD"]
        .dt.strftime("%d %b %Y")
    )

    table = table.rename(
        columns={
            "Report_Date_as_YYYY-MM-DD": "Report Date",
            "Open Interest": "Open Interest All",
            "Open Interest Change": "Open Interest Change All",
        }
    )

    numeric_columns = table.select_dtypes(
        include="number"
    ).columns

    st.dataframe(
        table.style.format(
            {
                col: "{:,.0f}"
                for col in numeric_columns
                if "% OI" not in col
            }
            | {
                col: "{:.2f}%"
                for col in numeric_columns
                if "% OI" in col
            }
        ),
        hide_index=True,
        width="stretch",
    )