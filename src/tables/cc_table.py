
import pandas as pd
import streamlit as st

from src.transforms.transform_cc import (
    CONDITION_ORDER,
    is_five_year_average,
    latest_condition_observations,
)
from src.config.theme import UPC, DNC, MU
from src.components.tables import (
    render_styled_table,
    usda_table_style,
)


def _filter_cc(
    df: pd.DataFrame,
    commodity: str,
    crop_type: str,
    geo_level: str,
    state: str | None = None,
) -> pd.DataFrame:
    mask = (
        (df["Geo Level"] == geo_level)
        & (df["Commodity"] == commodity)
        & (df["Crop Type"] == crop_type)
    )

    if state is not None and "State" in df.columns:
        mask &= df["State"] == state

    return df.loc[mask].copy()


def _latest_values(
    df: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=group_columns + ["Value"])

    return (
        df.sort_values("Week Ending", kind="stable")
        .drop_duplicates(subset=group_columns, keep="last")
        [group_columns + ["Value"]]
    )


def _national_condition_values(
    df: pd.DataFrame,
    year: int,
    week: int,
) -> pd.Series:
    data = df.loc[
        (df["Year"] == year)
        & (df["Week"] == week)
    ].copy()

    data = latest_condition_observations(data)

    if data.empty:
        return pd.Series(dtype="float64")

    return data.groupby("Condition", observed=True)["Value"].first()


def _national_ge_value(values: pd.Series) -> float:
    values = values.reindex(["Good", "Excellent"])

    if values.isna().any():
        return float("nan")

    return float(values.sum())


def _previous_available_week(
    df: pd.DataFrame,
    year: int,
    week: int,
) -> int | None:
    weeks = df.loc[
        (df["Year"] == year)
        & (df["Week"] < week),
        "Week",
    ].dropna().unique()

    return int(max(weeks)) if len(weeks) else None


def prepare_cc_ge_seasonal(
    df: pd.DataFrame,
    commodity: str,
    crop_type: str,
    geo_level: str = "NATIONAL",
    state: str | None = None,
) -> pd.DataFrame:
    data = _filter_cc(
        df,
        commodity,
        crop_type,
        geo_level,
        state,
    )

    data = data.loc[
        data["Condition"].isin(["Good", "Excellent"])
    ]

    if data.empty:
        return pd.DataFrame(columns=["Year", "Week", "Value"])

    data = data.loc[~is_five_year_average(data)]
    data = latest_condition_observations(data)

    return (
        data.groupby(
            ["Year", "Week"],
            as_index=False,
            observed=True,
        )["Value"]
        .sum(min_count=2)
        .sort_values(["Year", "Week"])
        .reset_index(drop=True)
    )


def prepare_cc_weekly_table(
    df: pd.DataFrame,
    commodity: str,
    crop_type: str,
    year: int,
    geo_level: str = "NATIONAL",
    state: str | None = None,
) -> pd.DataFrame:
    data = _filter_cc(
        df,
        commodity,
        crop_type,
        geo_level,
        state,
    )

    data = data.loc[
        (data["Year"] == year)
        & data["Condition"].isin(CONDITION_ORDER)
    ]

    data = data.loc[~is_five_year_average(data)]
    data = latest_condition_observations(data)

    if data.empty:
        return pd.DataFrame()

    table = data.pivot_table(
        index=["Week", "Week Ending"],
        columns="Condition",
        values="Value",
        aggfunc="first",
        observed=False,
    )

    return (
        table.reindex(columns=CONDITION_ORDER)
        .reset_index()
        .sort_values("Week")
        .reset_index(drop=True)
    )


def prepare_national_cc_table(
    df: pd.DataFrame,
    commodity: str,
    crop_type: str,
    year: int,
) -> pd.DataFrame:
    return prepare_cc_weekly_table(
        df,
        commodity,
        crop_type,
        year,
        geo_level="NATIONAL",
    )


def prepare_national_cc_comparison(
    df: pd.DataFrame,
    commodity: str,
    crop_type: str,
    year: int,
    week: int,
) -> pd.DataFrame:
    data = _filter_cc(
        df,
        commodity,
        crop_type,
        "NATIONAL",
    )

    data = data.loc[data["Condition"].isin(CONDITION_ORDER)]

    if data.empty:
        return pd.DataFrame()

    average_mask = is_five_year_average(data)
    actual = data.loc[~average_mask]
    average = data.loc[average_mask]

    actual = actual.loc[actual["Year"].isin([year - 1, year])]

    previous_week = _previous_available_week(actual, year, week)

    current = _national_condition_values(actual, year, week)
    previous = (
        _national_condition_values(actual, year, previous_week)
        if previous_week is not None
        else pd.Series(dtype="float64")
    )
    last_year = _national_condition_values(actual, year - 1, week)
    five_year = _national_condition_values(average, year, week)

    rows = []

    for condition in CONDITION_ORDER:
        current_value = current.get(condition, float("nan"))
        previous_value = previous.get(condition, float("nan"))
        last_year_value = last_year.get(condition, float("nan"))
        average_value = five_year.get(condition, float("nan"))

        rows.append({
            "Condition": condition,
            "Current Week": current_value,
            "Previous Week": previous_value,
            "WoW Change": (
                current_value - previous_value
                if pd.notna(current_value) and pd.notna(previous_value)
                else float("nan")
            ),
            "Same Week Last Year": last_year_value,
            "YoY Change": (
                current_value - last_year_value
                if pd.notna(current_value) and pd.notna(last_year_value)
                else float("nan")
            ),
            "5Y Average": average_value,
            "vs 5Y Average": (
                current_value - average_value
                if pd.notna(current_value) and pd.notna(average_value)
                else float("nan")
            ),
        })

    current_ge = _national_ge_value(current)
    previous_ge = _national_ge_value(previous)
    last_year_ge = _national_ge_value(last_year)
    average_ge = _national_ge_value(five_year)

    rows.append({
        "Condition": "Good + Excellent",
        "Current Week": current_ge,
        "Previous Week": previous_ge,
        "WoW Change": (
            current_ge - previous_ge
            if pd.notna(current_ge) and pd.notna(previous_ge)
            else float("nan")
        ),
        "Same Week Last Year": last_year_ge,
        "YoY Change": (
            current_ge - last_year_ge
            if pd.notna(current_ge) and pd.notna(last_year_ge)
            else float("nan")
        ),
        "5Y Average": average_ge,
        "vs 5Y Average": (
            current_ge - average_ge
            if pd.notna(current_ge) and pd.notna(average_ge)
            else float("nan")
        ),
    })

    result = pd.DataFrame(rows)
    result.attrs.update({
        "year": year,
        "week": week,
        "previous_week": previous_week,
    })

    return result


def prepare_national_cc_historical(
    df: pd.DataFrame,
    commodity: str,
    crop_type: str,
    year: int,
) -> pd.DataFrame:
    data = _filter_cc(
        df,
        commodity,
        crop_type,
        "NATIONAL",
    )

    data = data.loc[
        data["Condition"].isin(["Good", "Excellent"])
    ]

    if data.empty:
        return pd.DataFrame()

    average_mask = is_five_year_average(data)
    actual = data.loc[~average_mask]
    average = data.loc[average_mask]

    actual = actual.loc[actual["Year"].isin([year - 1, year])]
    average = average.loc[average["Year"] == year]

    actual = latest_condition_observations(actual)
    average = latest_condition_observations(average)

    def prepare_series(
        source: pd.DataFrame,
        source_year: int | None = None,
    ) -> pd.DataFrame:
        if source_year is not None:
            source = source.loc[source["Year"] == source_year]

        if source.empty:
            return pd.DataFrame(columns=["Week", "Value"])

        return (
            source.groupby(
                "Week",
                as_index=False,
                observed=True,
            )["Value"]
            .sum(min_count=2)
        )

    current = prepare_series(actual, year).rename(
        columns={"Value": "Current Year"}
    )
    previous = prepare_series(actual, year - 1).rename(
        columns={"Value": "Previous Year"}
    )
    five_year = prepare_series(average).rename(
        columns={"Value": "5Y Average"}
    )

    return (
        current
        .merge(previous, on="Week", how="outer")
        .merge(five_year, on="Week", how="outer")
        .sort_values("Week")
        .reset_index(drop=True)
    )


def prepare_state_cc_comparison(
    df: pd.DataFrame,
    commodity: str,
    crop_type: str,
    condition: str,
    year: int,
    week: int,
) -> pd.DataFrame:
    data = _filter_cc(
        df,
        commodity,
        crop_type,
        "STATE",
    )

    data = data.loc[data["Condition"] == condition]

    if data.empty:
        return pd.DataFrame()

    average_mask = is_five_year_average(data)
    actual = data.loc[~average_mask]
    average = data.loc[average_mask]

    actual = actual.loc[actual["Year"].isin([year - 1, year])]

    current_data = actual.loc[
        (actual["Year"] == year)
        & (actual["Week"] == week)
    ].copy()

    if current_data.empty:
        return pd.DataFrame()

    states = current_data["State"].dropna().unique()

    current = _latest_values(
        current_data,
        ["State"],
    ).rename(columns={"Value": "Current Week"})

    previous = (
        actual.loc[
            (actual["Year"] == year)
            & (actual["Week"] < week)
            & actual["State"].isin(states)
        ]
        .sort_values(
            ["State", "Week", "Week Ending"],
            kind="stable",
        )
        .drop_duplicates("State", keep="last")
        [["State", "Week", "Value"]]
        .rename(columns={
            "Week": "Last Available Week",
            "Value": "Last Week",
        })
    )

    last_year = _latest_values(
        actual.loc[
            (actual["Year"] == year - 1)
            & (actual["Week"] == week)
        ],
        ["State"],
    ).rename(columns={"Value": "Same Week Last Year"})

    five_year = _latest_values(
        average.loc[
            (average["Year"] == year)
            & (average["Week"] == week)
        ],
        ["State"],
    ).rename(columns={"Value": "5Y Avg"})

    table = (
        current
        .merge(previous, on="State", how="left")
        .merge(last_year, on="State", how="left")
        .merge(five_year, on="State", how="left")
    )

    table["Week Diff"] = table["Current Week"] - table["Last Week"]
    table["Year Diff"] = (
        table["Current Week"] - table["Same Week Last Year"]
    )
    table["5Y Avg Diff"] = table["Current Week"] - table["5Y Avg"]
    table["Week"] = week

    return (
        table[[
            "State",
            "Week",
            "Current Week",
            "Last Week",
            "Last Available Week",
            "Week Diff",
            "Same Week Last Year",
            "Year Diff",
            "5Y Avg",
            "5Y Avg Diff",
        ]]
        .sort_values("State")
        .reset_index(drop=True)
    )


def prepare_state_cc_table(
    df: pd.DataFrame,
    commodity: str,
    crop_type: str,
    year: int,
    week: int,
) -> pd.DataFrame:
    frames = []

    for condition in CONDITION_ORDER:
        table = prepare_state_cc_comparison(
            df,
            commodity,
            crop_type,
            condition,
            year,
            week,
        )

        if not table.empty:
            table.insert(1, "Condition", condition)
            frames.append(table)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def prepare_state_cc_ge_chart_data(
    df: pd.DataFrame,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    data = df.loc[
        df["Condition"].isin(["Good", "Excellent"])
    ].copy()

    if data.empty:
        return pd.DataFrame()

    columns = [
        "Current Week",
        "Last Week",
        "Same Week Last Year",
        "5Y Avg",
    ]

    data[columns] = data[columns].apply(
        pd.to_numeric,
        errors="coerce",
    )

    result = (
        data.groupby("State")[columns]
        .sum(min_count=2)
        .reset_index()
    )

    result["Week Diff"] = result["Current Week"] - result["Last Week"]
    result["Year Diff"] = result["Current Week"] - result["Same Week Last Year"]
    result["5Y Avg Diff"] = result["Current Week"] - result["5Y Avg"]

    previous = (
        df.groupby("State")["Last Available Week"]
        .max()
        .rename("Last Available Week")
        .reset_index()
    )

    return (
        result.merge(previous, on="State", how="left")
        .sort_values("State")
        .reset_index(drop=True)
    )


def _difference_color(value):
    if pd.isna(value):
        return ""
    if value > 0:
        return f"color: {UPC};"
    if value < 0:
        return f"color: {DNC};"
    return f"color: {MU};"


def _format_cc_table(
    df: pd.DataFrame,
    percentage_columns: list[str],
    difference_columns: list[str] | None = None,
):
    display = df.copy()
    difference_columns = difference_columns or []

    formatters = {}

    for column in percentage_columns:
        if column not in display.columns:
            continue

        if column in difference_columns:
            formatters[column] = (
                lambda value: f"{value:+.1f}" if pd.notna(value) else "—"
            )
        else:
            formatters[column] = (
                lambda value: f"{value:.1f}%" if pd.notna(value) else "—"
            )

    for column in ["Week", "Last Available Week"]:
        if column in display.columns:
            display[column] = display[column].map(
                lambda value: (
                    f"W{int(value):02d}" if pd.notna(value) else "—"
                )
            )

    if "Week Ending" in display.columns:
        display["Week Ending"] = (
            pd.to_datetime(display["Week Ending"], errors="coerce")
            .dt.strftime("%d %b %Y")
            .fillna("—")
        )

    styled = display.style.format(formatters)

    for column in difference_columns:
        if column in display.columns:
            styled = styled.map(_difference_color, subset=[column])

    return usda_table_style(styled)


def render_national_cc_comparison_table(
    df: pd.DataFrame,
    year: int,
    week: int | None = None,
) -> None:
    st.subheader("National Condition Comparison")

    if df.empty:
        st.info("No national crop condition comparison data available.")
        return

    metadata_week = df.attrs.get("week", week)
    previous_week = df.attrs.get("previous_week")

    if metadata_week is not None:
        current_label = f"W{int(metadata_week):02d}"
        last_year_label = f"W{int(metadata_week):02d} LY"
        average_label = f"5Y Avg W{int(metadata_week):02d}"
    else:
        current_label = "Current Week"
        last_year_label = "Same Week Last Year"
        average_label = "5Y Average"

    previous_label = (
        f"W{int(previous_week):02d}"
        if previous_week is not None
        else "Previous Week"
    )

    display = df.rename(columns={
        "Current Week": current_label,
        "Previous Week": previous_label,
        "Same Week Last Year": last_year_label,
        "5Y Average": average_label,
    })

    if metadata_week is not None:
        st.caption(f"Reporting week {current_label}, {year}")

    differences = ["WoW Change", "YoY Change", "vs 5Y Average"]

    styled = _format_cc_table(
        display,
        [
            current_label,
            previous_label,
            "WoW Change",
            last_year_label,
            "YoY Change",
            average_label,
            "vs 5Y Average",
        ],
        differences,
    )

    render_styled_table(styled)


def render_national_cc_historical_table(
    df: pd.DataFrame,
    year: int,
) -> None:
    st.subheader("Good + Excellent — Historical Seasonal Comparison")

    if df.empty:
        st.info("No historical national crop condition data available.")
        return

    value_columns = [
        "Current Year",
        "Previous Year",
        "5Y Average",
    ]

    display = df.copy()

    display = display.set_index("Week").reindex(
        columns=value_columns
    ).T

    display.index = [
        f"Current ({year})",
        f"Previous Year ({year - 1})",
        "5Y Average",
    ]

    display.columns = [
        f"W{int(week):02d}"
        for week in display.columns
    ]

    display.index.name = "Period"

    styled = display.style.format(
        lambda value: f"{value:.1f}%" if pd.notna(value) else "—"
    )

    styled = usda_table_style(styled)

    st.caption(f"Weekly Good + Excellent progression — {year}")

    render_styled_table(styled)


def render_cc_table(
    df: pd.DataFrame,
    title: str,
) -> None:
    st.subheader(title)

    if df.empty:
        st.info("No crop condition data available.")
        return

    display = df.copy()

    if "Week" in display.columns:
        display["Week"] = display["Week"].map(
            lambda value: (
                f"W{int(value):02d}" if pd.notna(value) else "—"
            )
        )

    if "Week Ending" in display.columns:
        display["Week Ending"] = (
            pd.to_datetime(display["Week Ending"], errors="coerce")
            .dt.strftime("%d %b %Y")
            .fillna("—")
        )

    formatters = {
        column: lambda value: (
            f"{value:.1f}%" if pd.notna(value) else "—"
        )
        for column in CONDITION_ORDER
        if column in display.columns
    }

    styled = display.style.format(formatters)
    styled = usda_table_style(styled)

    render_styled_table(styled)


def render_state_cc_comparison_table(
    df: pd.DataFrame,
    week: int,
) -> None:
    if df.empty:
        st.info("No state comparison data available.")
        return

    display = prepare_state_cc_ge_chart_data(df)

    if display.empty:
        st.info("No Good + Excellent state comparison data available.")
        return

    previous_weeks = display["Last Available Week"].dropna().astype(int)
    previous_week = (
        int(previous_weeks.mode().iloc[0])
        if not previous_weeks.empty
        else None
    )

    previous_label = (
        f"W{previous_week:02d}"
        if previous_week is not None
        else "Previous Week"
    )

    display = display.rename(columns={
        "Current Week": f"W{week:02d}",
        "Last Week": previous_label,
        "Same Week Last Year": f"W{week:02d} LY",
        "5Y Avg": f"5Y Avg W{week:02d}",
        "Week Diff": "WoW Change",
        "Year Diff": "YoY Change",
        "5Y Avg Diff": "vs 5Y Avg",
    }).drop(columns=["Last Available Week"], errors="ignore")

    differences = ["WoW Change", "YoY Change", "vs 5Y Avg"]

    styled = _format_cc_table(
        display,
        [
            f"W{week:02d}",
            previous_label,
            "WoW Change",
            f"W{week:02d} LY",
            "YoY Change",
            f"5Y Avg W{week:02d}",
            "vs 5Y Avg",
        ],
        differences,
    )

    render_styled_table(styled)
