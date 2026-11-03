import pandas as pd


CROP_TYPE_MAP = {
    "CORN": "Corn",
    "CORN, GRAIN": "Corn, Grain",
    "CORN, SILAGE": "Corn, Silage",
    "SOYBEANS": "Soybeans",
    "WHEAT, WINTER": "Winter Wheat",
    "WHEAT, SPRING, DURUM": "Spring Durum Wheat",
    "WHEAT, SPRING, (EXCL DURUM)": "Spring Wheat (Excl. Durum)",
}


def is_five_year_average(
    df: pd.DataFrame,
) -> pd.Series:

    return (
        df["Data Item"]
        .astype("string")
        .str.contains(
            r"5[\s-]*YEAR[\s-]*AVG",
            case=False,
            na=False,
        )
    )


def get_chronological_measure_order(
    df: pd.DataFrame,
) -> list[str]:

    if df.empty:
        return []

    return (
        df.dropna(
            subset=["Measure", "Week"]
        )
        .groupby("Measure")["Week"]
        .min()
        .sort_values(kind="stable")
        .index
        .tolist()
    )


def prepare_cp_base_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    data = df.copy()

    data["Week Ending"] = pd.to_datetime(
        data["Week Ending"],
        errors="coerce",
    )

    data["Week"] = pd.to_numeric(
        data["Period"]
        .astype("string")
        .str.extract(
            r"WEEK\s*#?\s*(\d+)",
            expand=False,
        ),
        errors="coerce",
    ).astype("Int64")

    crop_prefix = (
        data["Data Item"]
        .astype("string")
        .str.extract(
            r"^(.*?)\s*-\s*PROGRESS",
            flags=2,
            expand=False,
        )
        .str.strip()
        .str.upper()
    )

    data["Crop Type"] = (
        crop_prefix
        .map(CROP_TYPE_MAP)
        .fillna(crop_prefix.str.title())
    )

    data["Measure"] = (
        data["Data Item"]
        .astype("string")
        .str.extract(
            r"MEASURED IN PCT\s+(.+)$",
            flags=2,
            expand=False,
        )
        .str.strip()
        .str.title()
    )

    data["Year"] = pd.to_numeric(
        data["Year"],
        errors="coerce",
    )

    data["Value"] = pd.to_numeric(
        data["Value"],
        errors="coerce",
    )

    data["Geo Level"] = (
        data["Geo Level"]
        .astype("string")
        .str.upper()
    )

    return data


def prepare_national_cp_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    data = df.loc[
        df["Geo Level"] == "NATIONAL"
    ].copy()

    return (
        data.dropna(
            subset=[
                "Year",
                "Week",
                "Value",
                "Measure",
                "Crop Type",
            ]
        )
        .sort_values(
            [
                "Commodity",
                "Crop Type",
                "Measure",
                "Year",
                "Week",
                "Week Ending",
            ]
        )
        .reset_index(drop=True)
    )


def prepare_state_cp_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    data = df.loc[
        df["Geo Level"] == "STATE"
    ].copy()

    return (
        data.dropna(
            subset=[
                "Year",
                "Week",
                "Value",
                "Measure",
                "Crop Type",
                "State",
            ]
        )
        .sort_values(
            [
                "Commodity",
                "Crop Type",
                "Measure",
                "Year",
                "State",
                "Week",
                "Week Ending",
            ]
        )
        .reset_index(drop=True)
    )


def prepare_state_table_cp_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    data = df.loc[
        df["Geo Level"] == "STATE"
    ].copy()

    return (
        data.dropna(
            subset=[
                "Year",
                "Week",
                "Value",
                "Measure",
                "Crop Type",
                "State",
            ]
        )
        .sort_values(
            [
                "Commodity",
                "Crop Type",
                "Measure",
                "Year",
                "State",
                "Week",
                "Week Ending",
            ]
        )
        .reset_index(drop=True)
    )


def prepare_seasonal_data(
    df: pd.DataFrame,
    crop_type: str,
    geography: str = "NATIONAL",
    state: str | None = None,
) -> dict[str, dict[int, pd.DataFrame]]:

    data = df.loc[
        (df["Geo Level"] == geography.upper())
        & (df["Crop Type"] == crop_type)
    ].copy()

    data = data.loc[
        ~is_five_year_average(data)
    ]

    if state is not None:
        data = data.loc[
            data["State"] == state
        ]

    if data.empty:
        return {}

    data = data.sort_values(
        [
            "Measure",
            "Year",
            "Week",
            "Week Ending",
        ]
    )

    stage_order = get_chronological_measure_order(
        data
    )

    seasonal_data = {}

    for measure in stage_order:

        measure_data = data.loc[
            data["Measure"] == measure
        ]

        year_data_dict = {}

        for year, year_data in measure_data.groupby(
            "Year",
            sort=True,
        ):

            weekly_data = (
                year_data[
                    [
                        "Week",
                        "Week Ending",
                        "Value",
                    ]
                ]
                .sort_values(
                    [
                        "Week",
                        "Week Ending",
                    ]
                )
                .reset_index(drop=True)
            )

            year_data_dict[int(year)] = weekly_data

        if year_data_dict:
            seasonal_data[measure] = year_data_dict

    return seasonal_data


def prepare_cp_data(
    df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:

    data = prepare_cp_base_data(df)

    return {
        "national": prepare_national_cp_data(data),
        "state": prepare_state_cp_data(data),
        "state_table": prepare_state_table_cp_data(data),
    }


def prepare_weekly_comparison_data(
    df: pd.DataFrame,
    crop_type: str,
    measure: str,
    week: int,
) -> tuple[pd.DataFrame, float | None]:

    data = df.loc[
        (df["Geo Level"] == "NATIONAL")
        & (df["Crop Type"] == crop_type)
        & (df["Measure"] == measure)
        & (df["Week"] == week)
    ].copy()

    if data.empty:
        return pd.DataFrame(), None

    average_mask = is_five_year_average(data)

    average_data = data.loc[
        average_mask
    ].copy()

    actual_data = data.loc[
        ~average_mask
    ].copy()

    actual_data = (
        actual_data
        .dropna(
            subset=[
                "Year",
                "Value",
            ]
        )
        .sort_values(
            [
                "Year",
                "Week Ending",
            ]
        )
        .reset_index(drop=True)
    )

    average_value = None

    if not average_data.empty:

        latest_average_year = average_data["Year"].max()

        latest_average = average_data.loc[
            average_data["Year"] == latest_average_year
        ]

        if not latest_average.empty:

            average_value = float(
                latest_average.sort_values(
                    "Week Ending"
                )["Value"].iloc[-1]
            )

    return (
        actual_data[
            [
                "Year",
                "Week",
                "Week Ending",
                "Value",
            ]
        ].reset_index(drop=True),
        average_value,
    )