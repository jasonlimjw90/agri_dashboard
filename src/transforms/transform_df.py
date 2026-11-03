
import numpy as np
import pandas as pd

from src.components.format_years import format_marketing_year
from src.config.theme import MONTH_TICK_TEXT


def filter_latest_month_offset(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return df.copy()

    if "month offset" not in df.columns or "crop year" not in df.columns:
        return df.copy()

    data = df.copy()

    offsets = (
        data["month offset"]
        .astype("string")
        .str.strip()
        .str.extract(r"^(\d+)[_-](\d+)$")
    )

    data["_offset_year"] = pd.to_numeric(
        offsets[0],
        errors="coerce",
    )

    data["_offset_month"] = pd.to_numeric(
        offsets[1],
        errors="coerce",
    )

    data = data.dropna(
        subset=["_offset_year", "_offset_month"],
    )

    if data.empty:
        return df.iloc[0:0].copy()

    latest_offsets = (
        data[
            ["crop year", "_offset_year", "_offset_month"]
        ]
        .drop_duplicates()
        .sort_values(
            ["crop year", "_offset_year", "_offset_month"]
        )
        .drop_duplicates(
            subset=["crop year"],
            keep="last",
        )
    )

    data = data.merge(
        latest_offsets,
        on=["crop year", "_offset_year", "_offset_month"],
        how="inner",
    )

    return data.drop(
        columns=["_offset_year", "_offset_month"],
    )


def prepare_wasde_cards(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    data = df.copy()

    data["Report Date"] = pd.to_datetime(
        data["Report Date"],
        errors="coerce",
    )

    data["Value"] = pd.to_numeric(
        data["Value"],
        errors="coerce",
    )

    data["crop year"] = pd.to_numeric(
        data["crop year"],
        errors="coerce",
    )

    data["snd_item"] = (
        data["snd_item"]
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    data["country"] = (
        data["country"]
        .astype(str)
        .str.strip()
    )

    data = data.dropna(
        subset=[
            "Report Date",
            "Value",
            "crop year",
            "snd_item",
        ],
    ).copy()

    data = data[
        data["snd_item"].ne("")
        & data["snd_item"].ne("nan")
    ].copy()

    data["crop year"] = data["crop year"].astype(int)

    data["season_month"] = (
        (data["Report Date"].dt.month - 5) % 12
    ) + 1

    data["crop_year_key"] = data["crop year"]

    data = data.sort_values(
        [
            "commodity",
            "country",
            "table",
            "crop",
            "snd_item",
            "crop_year_key",
            "Report Date",
        ]
    ).reset_index(drop=True)

    seasonal_df = data.copy()

    group_columns = [
        "commodity",
        "country",
        "table",
        "crop",
        "snd_item",
        "crop_year_key",
    ]

    change_df = data.copy()

    if "wheat_class" in change_df.columns:
        change_df["_wheat_class_key"] = (
            change_df["wheat_class"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.casefold()
        )

        group_columns.append("_wheat_class_key")

    change_df["Previous Value"] = (
        change_df
        .groupby(group_columns)["Value"]
        .shift(1)
    )

    change_df["Change"] = (
        change_df["Value"] - change_df["Previous Value"]
    )

    if "_wheat_class_key" in change_df.columns:
        change_df = change_df.drop(
            columns="_wheat_class_key"
        )

    return seasonal_df, change_df


def prepare_card_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame()

    return df


def prepare_seasonal_series(
    df: pd.DataFrame,
) -> dict[int, np.ndarray]:

    if df.empty:
        return {}

    data = (
        df.sort_values("Report Date")
        .drop_duplicates(
            subset=["crop_year_key", "season_month"],
            keep="last",
        )
    )

    series = {}

    for year, group in data.groupby("crop_year_key"):

        monthly = (
            group.set_index("season_month")["Value"]
            .reindex(range(1, 13))
        )

        series[int(year)] = monthly.to_numpy(dtype=float)

    return series


def prepare_history_data(
    df: pd.DataFrame,
    years: int | None = 5,
) -> tuple[np.ndarray, list[int]]:

    if df.empty:
        return np.array([]), []

    latest = (
        df.sort_values("Report Date")
        .drop_duplicates(
            subset=["crop_year_key"],
            keep="last",
        )
        .sort_values("crop_year_key")
    )

    if years is not None:
        latest = latest.tail(years)

    values = latest["Value"].to_numpy(dtype=float)

    crop_years = (
        latest["crop_year_key"]
        .astype(int)
        .tolist()
    )

    return values, crop_years


def prepare_monthly_change_matrix(
    df: pd.DataFrame,
    years: int = 5,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame()

    data = (
        df.sort_values("Report Date")
        .drop_duplicates(
            subset=["Report Date"],
            keep="last",
        )
        .copy()
    )

    data["Change"] = data["Value"].diff()

    available_years = sorted(
        data["crop_year_key"].unique()
    )

    if years:
        available_years = available_years[-years:]

    data = data[
        data["crop_year_key"].isin(available_years)
    ]

    change_matrix = (
        data.pivot(
            index="season_month",
            columns="crop_year_key",
            values="Change",
        )
        .reindex(
            index=range(1, 13),
            columns=available_years,
        )
    )

    change_matrix.index = MONTH_TICK_TEXT

    change_matrix.columns = [
        format_marketing_year(int(year))
        for year in change_matrix.columns
    ]

    change_matrix.index.name = "Month"

    return change_matrix


def prepare_monthly_change_data(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame()

    data = (
        df.sort_values("Report Date")
        .drop_duplicates(
            subset=["Report Date"],
            keep="last",
        )
        .copy()
    )

    if "Change" not in data.columns:
        data["Change"] = data["Value"].diff()

    return data.reset_index(drop=True)
