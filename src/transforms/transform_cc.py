import re

import pandas as pd


CROP_TYPE_MAP = {
    "CORN": "Corn",
    "SOYBEANS": "Soybeans",
    "WHEAT, WINTER": "Winter Wheat",
    "WHEAT, SPRING, DURUM": "Spring Durum Wheat",
    "WHEAT, SPRING, (EXCL DURUM)": "Spring Wheat (Excl. Durum)",
}

CONDITION_ORDER = [
    "Very Poor",
    "Poor",
    "Fair",
    "Good",
    "Excellent",
]


def is_five_year_average(df: pd.DataFrame) -> pd.Series:
    return df["Data Item"].astype("string").str.contains(
        r"5[\s-]*YEAR[\s-]*AVG",
        case=False,
        na=False,
    )


def latest_condition_observations(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return df.copy()

    group_columns = [
        column
        for column in [
            "Year",
            "Week",
            "State",
            "Condition",
        ]
        if column in df.columns
    ]

    return (
        df.sort_values(
            "Week Ending",
            kind="stable",
        )
        .drop_duplicates(
            subset=group_columns,
            keep="last",
        )
        .copy()
    )


def prepare_cc_base_data(df: pd.DataFrame) -> pd.DataFrame:

    data = df.copy()

    data["Data Item"] = (
        data["Data Item"]
        .astype("string")
        .str.strip()
    )

    data["Year"] = pd.to_numeric(
        data["Year"],
        errors="coerce",
    ).astype("Int64")

    data["Week Ending"] = pd.to_datetime(
        data["Week Ending"],
        errors="coerce",
    )

    data["Week"] = pd.to_numeric(
        data["Period"]
        .astype("string")
        .str.extract(
            r"WEEK\s*#?\s*(\d+)",
            flags=re.IGNORECASE,
            expand=False,
        ),
        errors="coerce",
    ).astype("Int64")

    data["Value"] = pd.to_numeric(
        data["Value"],
        errors="coerce",
    )

    if "CV (%)" in data.columns:
        data["CV (%)"] = pd.to_numeric(
            data["CV (%)"],
            errors="coerce",
        )

    data["Commodity"] = (
        data["Commodity"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    data["Geo Level"] = (
        data["Geo Level"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    data["Crop Type Raw"] = (
        data["Data Item"]
        .str.extract(
            r"^(.*?)\s+-\s+CONDITION",
            flags=re.IGNORECASE,
            expand=False,
        )
        .str.strip()
        .str.upper()
    )

    data["Crop Type"] = data["Crop Type Raw"].map(
        CROP_TYPE_MAP
    )

    data["Condition"] = (
        data["Data Item"]
        .str.extract(
            r"MEASURED IN PCT\s+(VERY POOR|POOR|FAIR|GOOD|EXCELLENT)",
            flags=re.IGNORECASE,
            expand=False,
        )
        .str.strip()
        .str.upper()
        .str.title()
    )

    data["Condition"] = pd.Categorical(
        data["Condition"],
        categories=CONDITION_ORDER,
        ordered=True,
    )

    return data


def prepare_national_cc_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    data = df.loc[
        df["Geo Level"].eq("NATIONAL")
    ].copy()

    return data.sort_values(
        [
            "Commodity",
            "Crop Type",
            "Condition",
            "Year",
            "Week",
            "Week Ending",
        ],
        kind="stable",
    ).reset_index(drop=True)


def prepare_state_cc_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    data = df.loc[
        df["Geo Level"].eq("STATE")
    ].copy()

    return data.sort_values(
        [
            "Commodity",
            "Crop Type",
            "State",
            "Condition",
            "Year",
            "Week",
            "Week Ending",
        ],
        kind="stable",
    ).reset_index(drop=True)


def prepare_state_table_cc_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    return prepare_state_cc_data(df)


def prepare_seasonal_cc_data(
    df: pd.DataFrame,
    commodity: str,
    crop_type: str,
    condition: str,
    state: str | None = None,
    geo_level: str = "NATIONAL",
) -> dict:

    data = df.loc[
        (df["Commodity"] == commodity.upper())
        & (df["Crop Type"] == crop_type)
        & (df["Condition"] == condition.title())
        & (df["Geo Level"] == geo_level.upper())
    ].copy()

    if state is not None:
        data = data.loc[
            data["State"].astype("string").str.upper()
            == state.upper()
        ]

    data = data.dropna(
        subset=["Year", "Week"]
    )

    data = data.sort_values(
        ["Year", "Week", "Week Ending"],
        kind="stable",
    )

    seasonal_data = {}

    for year, year_data in data.groupby(
        "Year",
        sort=True,
    ):
        seasonal_data[int(year)] = (
            year_data[
                ["Week", "Week Ending", "Value"]
            ]
            .reset_index(drop=True)
        )

    return seasonal_data


def prepare_cc_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    base_data = prepare_cc_base_data(df)

    national_df = prepare_national_cc_data(base_data)
    state_df = prepare_state_cc_data(base_data)

    return national_df, state_df, state_df