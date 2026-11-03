
import pandas as pd
import streamlit as st

from src.components.tables import (
    fmt,
    sign_color,
    style_map,
    usda_table_style,
    render_styled_table,
)

from src.components.format_years import format_marketing_year
from src.config.labels import (
    WASDE_LABELS,
    LABEL_ALIASES,
    format_label,
)

from src.transforms.transform_df import filter_latest_month_offset


MONTH_ORDER = [
    5, 6, 7, 8, 9, 10, 11, 12,
    1, 2, 3, 4,
]


def format_wasde_item(item):
    return format_label(item)


def _canonical_wasde_item(item):
    key = str(item).strip().casefold()

    reverse_lookup = {
        label.casefold(): raw_key
        for section in WASDE_LABELS.values()
        for raw_key, label in section.items()
    }

    key = reverse_lookup.get(key, key)

    return LABEL_ALIASES.get(key, key)


def _ordered_items(items):
    ordered = []

    for section_items in WASDE_LABELS.values():
        for item in section_items:
            if item in items and item not in ordered:
                ordered.append(item)

    for item in items:
        if item not in ordered:
            ordered.append(item)

    return ordered


def _apply_wasde_multiindex(table):
    if table.empty:
        return table

    section_lookup = {
        _canonical_wasde_item(item): section
        for section, items in WASDE_LABELS.items()
        for item in items
    }

    ordered_items = _ordered_items(table.index)

    index_tuples = []

    for item in ordered_items:
        canonical_item = _canonical_wasde_item(item)

        section = section_lookup.get(
            canonical_item,
            "Other",
        )

        index_tuples.append(
            (
                section,
                format_wasde_item(item),
            )
        )

    table = table.reindex(ordered_items)

    table.index = pd.MultiIndex.from_tuples(
        index_tuples,
        names=["Section", "WASDE Item"],
    )

    return table


def _add_latest_change(
    table: pd.DataFrame,
    column_name: str,
) -> pd.DataFrame:

    if table.empty or len(table.columns) < 2:
        return table

    def calculate_change(row):
        values = row.dropna()

        if len(values) < 2:
            return pd.NA

        return values.iloc[-1] - values.iloc[-2]

    table[column_name] = table.apply(
        calculate_change,
        axis=1,
    )

    return table


def prepare_current_my_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Timestamp | None]:

    if df.empty:
        return pd.DataFrame(), None

    latest_crop_year = int(df["crop year"].max())

    data = df[
        df["crop year"] == latest_crop_year
    ].copy()

    if data.empty:
        return pd.DataFrame(), None

    latest_date = data["Report Date"].max()

    data["report_month"] = data["Report Date"].dt.month

    data = (
        data
        .sort_values("Report Date")
        .drop_duplicates(
            subset=["snd_item", "report_month"],
            keep="last",
        )
    )

    latest_month_position = MONTH_ORDER.index(
        latest_date.month
    )

    available_months = [
        month
        for month in MONTH_ORDER[:latest_month_position + 1]
        if month in data["report_month"].unique()
    ]

    if not available_months:
        return pd.DataFrame(), latest_date

    data = data[
        data["report_month"].isin(available_months)
    ].copy()

    data = data.sort_values(
        ["snd_item", "Report Date"]
    )

    data["Change"] = (
        data
        .groupby("snd_item")["Value"]
        .diff()
    )

    return data, latest_date


def _build_current_my_table(
    data: pd.DataFrame,
) -> pd.DataFrame:

    if data.empty:
        return pd.DataFrame()

    table = data.pivot(
        index="snd_item",
        columns="report_month",
        values="Value",
    )

    available_months = [
        month
        for month in MONTH_ORDER
        if month in data["report_month"].unique()
    ]

    table = table.reindex(
        columns=available_months,
    )

    month_labels = (
        data.groupby("report_month")["Report Date"]
        .max()
        .dt.strftime("%b %y")
        .to_dict()
    )

    table = table.rename(
        columns=month_labels,
    )

    table = _add_latest_change(
        table,
        "Change",
    )

    table = _apply_wasde_multiindex(table)

    return table


def prepare_current_my_table(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Timestamp | None]:

    data, latest_date = prepare_current_my_data(df)

    table = _build_current_my_table(data)

    return table, latest_date


def style_current_my_table(
    table: pd.DataFrame,
):

    formatters = {}

    for column in table.columns:

        if column == "Change":
            formatters[column] = (
                lambda value: (
                    fmt(value, 1)
                    if pd.notna(value)
                    else ""
                )
            )

        else:
            formatters[column] = (
                lambda value: (
                    f"{value:,.2f}"
                    if pd.notna(value)
                    else ""
                )
            )

    styled = table.style.format(
        formatters,
        na_rep="",
    )

    if "Change" in table.columns:
        styled = style_map(
            styled,
            sign_color,
            subset=["Change"],
        )

    return usda_table_style(styled)


def render_current_my_table(
    df: pd.DataFrame,
    prepared: bool = False,
):

    if prepared:
        data = df

        latest_date = (
            data["Report Date"].max()
            if not data.empty
            else None
        )

        table = _build_current_my_table(data)

    else:
        table, latest_date = prepare_current_my_table(df)

    if table.empty:
        st.info("No current marketing-year data available.")
        return

    if latest_date is not None:
        st.caption(
            f"Latest WASDE report: {latest_date:%d %B %Y}"
        )

    render_styled_table(
        style_current_my_table(table)
    )


def prepare_historical_table(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame()

    data = filter_latest_month_offset(df)

    if data.empty:
        return pd.DataFrame()

    duplicates = data[
        data.duplicated(
            subset=["snd_item", "crop year"],
            keep=False,
        )
    ]

    if not duplicates.empty:
        st.error(
            "Duplicate WASDE records found for the same "
            "item and crop year."
        )

        st.dataframe(
            duplicates[
                ["Report Date", "snd_item", "crop year", "Value"]
            ].sort_values(
                ["snd_item", "crop year", "Report Date"]
            ),
            width="content",
        )

        return pd.DataFrame()

    table = data.pivot(
        index="snd_item",
        columns="crop year",
        values="Value",
    )

    table = table.reindex(
        sorted(table.columns),
        axis=1,
    )

    table = _add_latest_change(
        table,
        "YoY Change",
    )

    table.columns = [
        format_marketing_year(int(year))
        if year != "YoY Change"
        else year
        for year in table.columns
    ]

    table = _apply_wasde_multiindex(table)

    return table


def prepare_yoy_change_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    columns = [
        "snd_item",
        "crop year",
        "YoY Change (%)",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    data = (
        df
        .sort_values("Report Date")
        .drop_duplicates(
            subset=["snd_item", "crop year"],
            keep="last",
        )
    )

    table = data.pivot(
        index="snd_item",
        columns="crop year",
        values="Value",
    )

    table = table.reindex(
        sorted(table.columns),
        axis=1,
    )

    yoy = (
        table
        .pct_change(
            axis=1,
            fill_method=None,
        )
        .mul(100)
    )

    yoy_data = (
        yoy
        .rename_axis(columns="crop year")
        .reset_index()
        .melt(
            id_vars="snd_item",
            var_name="crop year",
            value_name="YoY Change (%)",
        )
    )

    yoy_data["crop year"] = (
        yoy_data["crop year"].astype(int)
    )

    yoy_data["YoY Change (%)"] = (
        yoy_data["YoY Change (%)"]
        .replace(
            [float("inf"), float("-inf")],
            pd.NA,
        )
    )

    return yoy_data


def style_historical_table(
    table: pd.DataFrame,
):

    formatters = {}

    for column in table.columns:

        if column == "YoY Change":
            formatters[column] = (
                lambda value: (
                    fmt(value, 1)
                    if pd.notna(value)
                    else ""
                )
            )

        else:
            formatters[column] = (
                lambda value: (
                    f"{value:,.2f}"
                    if pd.notna(value)
                    else ""
                )
            )

    styled = table.style.format(
        formatters,
        na_rep="",
    )

    if "YoY Change" in table.columns:
        styled = style_map(
            styled,
            sign_color,
            subset=["YoY Change"],
        )

    return usda_table_style(styled)


def render_historical_table(
    df: pd.DataFrame,
):

    table = prepare_historical_table(df)

    if table.empty:
        st.info("No historical WASDE data available.")
        return

    render_styled_table(
        style_historical_table(table)
    )


def prepare_country_monthly_table(
    df: pd.DataFrame,
    countries: list,
    report_month: int | None = None,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame()

    latest_crop_year = df["crop year"].max()

    data = df[
        df["crop year"] == latest_crop_year
    ].copy()

    if data.empty:
        return pd.DataFrame()

    data["report_month"] = data["Report Date"].dt.month

    if report_month is None:
        report_month = data["Report Date"].max().month

    if report_month not in MONTH_ORDER:
        return pd.DataFrame()

    selected_month_position = MONTH_ORDER.index(
        report_month
    )

    available_months = [
        month
        for month in MONTH_ORDER[:selected_month_position + 1]
        if month in data["report_month"].unique()
    ]

    if not available_months:
        return pd.DataFrame()

    data = data[
        data["report_month"].isin(available_months)
    ].copy()

    data = (
        data
        .sort_values("Report Date")
        .drop_duplicates(
            subset=["country", "report_month"],
            keep="last",
        )
    )

    table = data.pivot(
        index="country",
        columns="report_month",
        values="Value",
    )

    month_labels = (
        data.groupby("report_month")["Report Date"]
        .max()
        .dt.strftime("%b %y")
        .to_dict()
    )

    latest_report_date = data["Report Date"].max()

    selected_year = (
        latest_report_date.year
        if report_month >= latest_report_date.month
        else latest_report_date.year + 1
    )

    month_labels[report_month] = pd.Timestamp(
        year=selected_year,
        month=report_month,
        day=1,
    ).strftime("%b %y")

    table = table.rename(
        columns={
            month: label
            for month, label in month_labels.items()
        }
    )

    ordered_columns = [
        month_labels[month]
        for month in available_months
        if month in month_labels
    ]

    table = table.reindex(
        index=countries,
        columns=ordered_columns,
    )

    table = _add_latest_change(
        table,
        "Change",
    )

    table.index.name = "Country"

    table = table.reset_index()

    table.columns = table.columns.map(str)

    return table


def style_country_table(
    table: pd.DataFrame,
    change_column: str,
):

    formatters = {
        column: "{:,.2f}"
        for column in table.columns
        if column != "Country"
        and column != change_column
    }

    formatters[change_column] = (
        lambda value: (
            fmt(value, 1)
            if pd.notna(value)
            else ""
        )
    )

    styled = table.style.format(
        formatters,
        na_rep="",
    )

    if change_column in table.columns:
        styled = style_map(
            styled,
            sign_color,
            subset=[change_column],
        )

    styled = styled.hide(axis="index")

    return usda_table_style(styled)


def render_country_monthly_table(
    df: pd.DataFrame,
    countries: list,
    report_month: int | None = None,
):

    table = prepare_country_monthly_table(
        df,
        countries,
        report_month=report_month,
    )

    if table.empty:
        st.info("No monthly country data available.")
        return

    render_styled_table(
        style_country_table(
            table,
            "Change",
        )
    )


def prepare_country_historical_table(
    df: pd.DataFrame,
    countries: list,
    years: int = 5,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame()

    data = filter_latest_month_offset(df)

    if data.empty:
        return pd.DataFrame()

    data = (
        data
        .sort_values("Report Date")
        .drop_duplicates(
            subset=["country", "crop year"],
            keep="last",
        )
    )

    available_years = sorted(
        data["crop year"].unique()
    )[-years:]

    if not available_years:
        return pd.DataFrame()

    data = data[
        data["crop year"].isin(available_years)
    ]

    table = data.pivot(
        index="country",
        columns="crop year",
        values="Value",
    )

    ordered_year_columns = [
        year
        for year in available_years
    ]

    table = table.reindex(
        index=countries,
        columns=ordered_year_columns,
    )

    table = _add_latest_change(
        table,
        "YoY Change",
    )

    table = table.rename(
        columns={
            year: format_marketing_year(int(year))
            for year in available_years
        }
    )

    table.index.name = "Country"

    table = table.reset_index()

    table.columns = table.columns.map(str)

    return table


def render_country_historical_table(
    df: pd.DataFrame,
    countries: list,
    years: int = 5,
):

    table = prepare_country_historical_table(
        df,
        countries,
        years,
    )

    if table.empty:
        st.info("No historical country data available.")
        return

    render_styled_table(
        style_country_table(
            table,
            "YoY Change",
        )
    )


def render_monthly_change_matrix(
    df: pd.DataFrame,
):

    if df.empty:
        st.info("No monthly revision data available.")
        return

    styled = df.style.format(
        "{:+,.2f}",
        na_rep="-",
    )

    styled = usda_table_style(styled)

    render_styled_table(styled)


def _prepare_current_report_crop_table(
    df: pd.DataFrame,
    crop: str,
    previous_date: pd.Timestamp,
    current_date: pd.Timestamp,
) -> tuple[pd.DataFrame, str | None]:

    data = df[
        df["crop"].astype(str).str.casefold() == crop
    ].copy()

    data = data[
        data["Report Date"].isin(
            [previous_date, current_date]
        )
    ].copy()

    if data.empty:
        return pd.DataFrame(), None

    data["crop year"] = pd.to_numeric(
        data["crop year"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["crop year", "snd_item", "Value"]
    )

    if data.empty:
        return pd.DataFrame(), None

    crop_year = int(
        data.loc[
            data["Report Date"] == current_date,
            "crop year",
        ].max()
    )

    data = data[
        data["crop year"] == crop_year
    ].copy()

    data = (
        data
        .sort_values("Report Date")
        .drop_duplicates(
            subset=["snd_item", "Report Date"],
            keep="last",
        )
    )

    table = data.pivot(
        index="snd_item",
        columns="Report Date",
        values="Value",
    )

    table = table.reindex(
        columns=[previous_date, current_date]
    )

    table.columns = ["Previous", "Current"]

    table["Change"] = (
        table["Current"] - table["Previous"]
    )

    table = _apply_wasde_multiindex(table)

    marketing_year = format_marketing_year(crop_year)

    year_type = (
        "Marketing Year Est."
        if crop == "oc"
        else "Marketing Year Proj."
    )

    marketing_year_label = (
        f"{year_type} ({marketing_year})"
    )

    table.columns = pd.MultiIndex.from_product(
        [
            [marketing_year_label],
            ["Previous", "Current", "Change"],
        ],
        names=["Marketing Year", "Comparison"],
    )

    return table, marketing_year_label


def prepare_current_report_table(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Timestamp | None, pd.Timestamp | None]:

    if df.empty:
        return pd.DataFrame(), None, None

    data = df.copy()

    data["Report Date"] = pd.to_datetime(
        data["Report Date"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["Report Date"]
    )

    report_dates = sorted(
        data["Report Date"].unique()
    )

    if len(report_dates) < 2:
        return pd.DataFrame(), None, None

    previous_date = pd.Timestamp(report_dates[-2])
    current_date = pd.Timestamp(report_dates[-1])

    estimate_table, _ = _prepare_current_report_crop_table(
        data,
        crop="oc",
        previous_date=previous_date,
        current_date=current_date,
    )

    projection_table, _ = _prepare_current_report_crop_table(
        data,
        crop="nc",
        previous_date=previous_date,
        current_date=current_date,
    )

    tables = [
        table
        for table in [estimate_table, projection_table]
        if not table.empty
    ]

    if not tables:
        return pd.DataFrame(), previous_date, current_date

    table = pd.concat(
        tables,
        axis=1,
    )

    return table, previous_date, current_date


def style_current_report_table(
    table: pd.DataFrame,
):

    formatters = {}

    change_columns = []

    for column in table.columns:

        if column[1] == "Change":
            formatters[column] = (
                lambda value: (
                    fmt(value, 1)
                    if pd.notna(value)
                    else ""
                )
            )

            change_columns.append(column)

        else:
            formatters[column] = (
                lambda value: (
                    f"{value:,.2f}"
                    if pd.notna(value)
                    else ""
                )
            )

    styled = table.style.format(
        formatters,
        na_rep="",
    )

    if change_columns:
        styled = style_map(
            styled,
            sign_color,
            subset=change_columns,
        )

    year_groups = table.columns.get_level_values(0).unique()

    if len(year_groups) >= 2:
        projection_columns = [
            column
            for column in table.columns
            if "Proj." in str(column[0])
        ]

        if projection_columns:
            first_projection_column = projection_columns[0]

            styled = styled.set_properties(
                subset=[first_projection_column],
                **{"border-left": "2px solid #9AA4B2"}
            )

            styled = styled.set_table_styles(
                [
                    {
                        "selector": "th.col_heading.level1",
                        "props": [
                            ("border-left", "none"),
                        ],
                    },
                ],
                overwrite=False,
            )

    return usda_table_style(styled)


def render_current_report_table(
    df: pd.DataFrame,
    prepared: tuple | None = None,
):

    if prepared is None:
        prepared = prepare_current_report_table(df)

    table, previous_date, current_date = prepared

    if table.empty:
        st.info(
            "No current report comparison data available."
        )
        return

    st.caption(
        f"Previous WASDE: {previous_date:%d %B %Y}  |  "
        f"Current WASDE: {current_date:%d %B %Y}"
    )

    render_styled_table(
        style_current_report_table(table)
    )
