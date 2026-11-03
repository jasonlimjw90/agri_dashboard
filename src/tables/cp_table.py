
import pandas as pd
import streamlit as st

from src.transforms.transform_cp import is_five_year_average
from src.components.tables import (
    render_styled_table,
    usda_table_style,
)
from src.config.theme import UPC, DNC, MU


def _filter_progress_data(
    df: pd.DataFrame,
    measure: str,
    geography: str,
    crop_type: str | None = None,
) -> pd.DataFrame:

    data = df.loc[
        (df["Geo Level"] == geography)
        & (df["Measure"] == measure)
    ].copy()

    if crop_type is not None:
        data = data.loc[
            data["Crop Type"] == crop_type
        ].copy()

    return data


def _split_actual_average(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    average_mask = is_five_year_average(df)

    return (
        df.loc[~average_mask].copy(),
        df.loc[average_mask].copy(),
    )


def _latest_weekly_value(
    df: pd.DataFrame,
    value_name: str,
    group_columns: list[str],
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame(
            columns=group_columns + [value_name]
        )

    return (
        df.sort_values("Week Ending")
        .drop_duplicates(
            subset=group_columns,
            keep="last",
        )
        [group_columns + ["Value"]]
        .rename(
            columns={"Value": value_name}
        )
    )


def prepare_national_progress_table(
    df: pd.DataFrame,
    measure: str,
    year: int,
    crop_type: str | None = None,
) -> pd.DataFrame:

    data = _filter_progress_data(
        df=df,
        measure=measure,
        geography="NATIONAL",
        crop_type=crop_type,
    )

    if data.empty:
        return pd.DataFrame()

    actual_data, average_data = _split_actual_average(data)

    current_data = actual_data.loc[
        actual_data["Year"] == year
    ].copy()

    previous_data = actual_data.loc[
        actual_data["Year"] == year - 1
    ].copy()

    average_data = average_data.loc[
        average_data["Year"] == year
    ].copy()

    if current_data.empty:
        return pd.DataFrame()

    current = (
        current_data
        .sort_values("Week Ending")
        .drop_duplicates(
            subset=["Week"],
            keep="last",
        )
        [["Week", "Week Ending", "Value"]]
        .rename(
            columns={"Value": str(year)}
        )
    )

    previous = _latest_weekly_value(
        df=previous_data,
        value_name=str(year - 1),
        group_columns=["Week"],
    )

    average = _latest_weekly_value(
        df=average_data,
        value_name="5-Year Avg",
        group_columns=["Week"],
    )

    table = (
        current
        .merge(
            previous,
            on="Week",
            how="left",
            validate="one_to_one",
        )
        .merge(
            average,
            on="Week",
            how="left",
            validate="one_to_one",
        )
    )

    return (
        table[
            [
                "Week",
                "Week Ending",
                str(year - 1),
                str(year),
                "5-Year Avg",
            ]
        ]
        .sort_values("Week")
        .reset_index(drop=True)
    )


def render_national_progress_table(
    df: pd.DataFrame,
) -> None:

    if df.empty:
        st.info("No national progress data available.")
        return

    display = df.copy()

    display["Week"] = display["Week"].map(
        lambda value: (
            f"W{int(value):02d}"
            if pd.notna(value)
            else "—"
        )
    )

    display["Week Ending"] = (
        pd.to_datetime(
            display["Week Ending"],
            errors="coerce",
        )
        .dt.strftime("%d %b %Y")
        .fillna("—")
    )

    percentage_columns = [
        column
        for column in display.columns
        if column not in ["Week", "Week Ending"]
    ]

    formatters = {
        column: lambda value: (
            f"{value:.1f}%"
            if pd.notna(value)
            else "—"
        )
        for column in percentage_columns
    }

    styled = display.style.format(formatters)
    styled = usda_table_style(styled)

    render_styled_table(styled)


def _latest_state_values(
    df: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame(
            columns=group_columns + ["Value"]
        )

    return (
        df.sort_values(
            "Week Ending",
            kind="stable",
        )
        .drop_duplicates(
            subset=group_columns,
            keep="last",
        )
        [group_columns + ["Value"]]
    )


def prepare_state_comparison_table(
    df: pd.DataFrame,
    measure: str,
    year: int,
    crop_type: str | None = None,
    week: int | None = None,
) -> pd.DataFrame:

    data = _filter_progress_data(
        df=df,
        measure=measure,
        geography="STATE",
        crop_type=crop_type,
    )

    if data.empty:
        return pd.DataFrame()

    actual_data, average_data = _split_actual_average(data)

    actual_data = actual_data.loc[
        actual_data["Year"].isin([year - 1, year])
    ].copy()

    current_year_data = actual_data.loc[
        actual_data["Year"] == year
    ]

    if current_year_data.empty:
        return pd.DataFrame()

    if week is None:
        week = int(current_year_data["Week"].max())

    week = int(week)

    current_week_data = actual_data.loc[
        (actual_data["Year"] == year)
        & (actual_data["Week"] == week)
    ].copy()

    if current_week_data.empty:
        return pd.DataFrame()

    states = current_week_data["State"].dropna().unique()

    current = _latest_state_values(
        current_week_data,
        ["State"],
    ).rename(
        columns={"Value": "Current Week"}
    )

    previous_week = (
        actual_data.loc[
            (actual_data["Year"] == year)
            & (actual_data["Week"] < week)
            & actual_data["State"].isin(states)
        ]
        .sort_values(
            ["State", "Week", "Week Ending"],
            kind="stable",
        )
        .drop_duplicates(
            subset=["State"],
            keep="last",
        )
        [["State", "Week", "Value"]]
        .rename(
            columns={
                "Week": "Last Available Week",
                "Value": "Last Week",
            }
        )
    )

    previous_year = _latest_state_values(
        actual_data.loc[
            (actual_data["Year"] == year - 1)
            & (actual_data["Week"] == week)
        ],
        ["State"],
    ).rename(
        columns={"Value": "Same Week Last Year"}
    )

    average = _latest_state_values(
        average_data.loc[
            (average_data["Year"] == year)
            & (average_data["Week"] == week)
        ],
        ["State"],
    ).rename(
        columns={"Value": "5Y Avg"}
    )

    table = (
        current
        .merge(previous_week, on="State", how="left")
        .merge(previous_year, on="State", how="left")
        .merge(average, on="State", how="left")
    )

    table["Week Diff"] = (
        table["Current Week"] - table["Last Week"]
    )

    table["Year Diff"] = (
        table["Current Week"]
        - table["Same Week Last Year"]
    )

    table["5Y Avg Diff"] = (
        table["Current Week"] - table["5Y Avg"]
    )

    table["Week"] = week

    table[str(year)] = table["Current Week"]
    table["5-Year Avg"] = table["5Y Avg"]

    return (
        table[
            [
                "State",
                "Week",
                str(year),
                "5-Year Avg",
                "Current Week",
                "Last Week",
                "Week Diff",
                "Same Week Last Year",
                "Year Diff",
                "5Y Avg",
                "5Y Avg Diff",
            ]
        ]
        .sort_values("State")
        .reset_index(drop=True)
    )


def render_state_comparison_table(
    df: pd.DataFrame,
) -> None:

    if df.empty:
        st.info("No state comparison data available.")
        return

    display_columns = [
        "State",
        "Week",
        "Current Week",
        "Last Week",
        "Week Diff",
        "Same Week Last Year",
        "Year Diff",
        "5Y Avg",
        "5Y Avg Diff",
    ]

    display = df[
        [
            column
            for column in display_columns
            if column in df.columns
        ]
    ].copy()

    if "Week" in display.columns:
        display["Week"] = display["Week"].map(
            lambda value: (
                f"W{int(value):02d}"
                if pd.notna(value)
                else "—"
            )
        )

    percentage_columns = [
        "Current Week",
        "Last Week",
        "Week Diff",
        "Same Week Last Year",
        "Year Diff",
        "5Y Avg",
        "5Y Avg Diff",
    ]

    difference_columns = [
        "Week Diff",
        "Year Diff",
        "5Y Avg Diff",
    ]

    formatters = {}

    for column in percentage_columns:
        if column not in display.columns:
            continue

        if column in difference_columns:
            formatters[column] = lambda value: (
                f"{value:+.1f} pp"
                if pd.notna(value)
                else "—"
            )
        else:
            formatters[column] = lambda value: (
                f"{value:.1f}%"
                if pd.notna(value)
                else "—"
            )

    styled = display.style.format(formatters)

    def difference_color(value):
        if pd.isna(value):
            return ""
        if value > 0:
            return f"color: {UPC};"
        if value < 0:
            return f"color: {DNC};"
        return f"color: {MU};"

    for column in difference_columns:
        if column in display.columns:
            styled = styled.map(
                difference_color,
                subset=[column],
            )

    styled = usda_table_style(styled)

    render_styled_table(styled)
