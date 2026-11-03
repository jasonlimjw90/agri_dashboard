
import pandas as pd


def prepare_wasde_data(dataframe):
    """Standardize WASDE column names, data types and month offsets."""

    data = dataframe.copy()

    data.columns = (
        data.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    required_columns = [
        "report_date",
        "value",
        "crop_year",
        "month_offset",
        "commodity",
        "country",
        "snd_item",
    ]

    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Convert data types.
    data["report_date"] = pd.to_datetime(
        data["report_date"], errors="coerce"
    )
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    data["crop_year"] = pd.to_numeric(
        data["crop_year"], errors="coerce"
    )

    # Normalize text fields.
    text_columns = [
        "commodity",
        "country",
        "snd_item",
        "wheat_class",
        "crop",
        "table",
    ]

    for col in text_columns:
        if col in data.columns:
            data[col] = (
                data[col].astype("string").str.strip().str.lower()
            )

    # Parse offsets such as 1_10 into year_off=1 and month_num=10.
    offset_parts = (
        data["month_offset"]
        .astype("string")
        .str.strip()
        .str.extract(r"^(\d+)_(\d{1,2})$")
    )

    data["year_off"] = pd.to_numeric(
        offset_parts[0], errors="coerce"
    )
    data["month_num"] = pd.to_numeric(
        offset_parts[1], errors="coerce"
    )

    data = data.dropna(
        subset=[
            "report_date",
            "value",
            "crop_year",
            "year_off",
            "month_num",
        ]
    ).copy()

    # Validate month numbers.
    data = data[data["month_num"].between(1, 12)].copy()

    for col in ["crop_year", "year_off", "month_num"]:
        data[col] = data[col].astype(int)

    data["month_offset"] = (
        data["year_off"].astype(str)
        + "_"
        + data["month_num"].astype(str).str.zfill(2)
    )

    return data


def filter_wasde_data(
    dataframe: pd.DataFrame,
    commodity: str | None = None,
    country: str | None = None,
    table: str | None = None,
    wheat_class: str | None = None,
    crop_status: str | None = None,
    crop_year: int | None = None,
    snd_items: list[str] | None = None,
) -> pd.DataFrame:
    """Filter prepared WASDE data by the requested dimensions."""

    data = dataframe.copy()

    filters = {
        "commodity": commodity,
        "country": country,
        "table": table,
        "wheat_class": wheat_class,
        "crop": crop_status,
    }

    for column, value in filters.items():
        if value is not None and column in data.columns:
            data = data[
                data[column].eq(str(value).strip().lower()).fillna(False)
            ]

    if crop_year is not None:
        data = data[data["crop_year"].eq(int(crop_year))]

    if snd_items is not None:
        items = [item.strip().lower() for item in snd_items]
        data = data[data["snd_item"].isin(items)]

    return data.copy()


def filter_wasde_offset(
    dataframe: pd.DataFrame,
    month_offset: str,
) -> pd.DataFrame:
    """Select a specific WASDE offset, e.g. '1_10'."""

    offset = str(month_offset).strip()

    parts = offset.split("_")
    if len(parts) != 2:
        raise ValueError(
            "month_offset must use 'year_month' format, e.g. '1_10'."
        )

    try:
        year_off, month_num = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise ValueError(
            "month_offset must contain numeric year and month values."
        ) from exc

    if year_off < 1 or not 1 <= month_num <= 12:
        raise ValueError(f"Invalid month_offset: {month_offset}")

    normalized_offset = f"{year_off}_{month_num:02d}"

    return dataframe[
        dataframe["month_offset"].eq(normalized_offset)
    ].copy()
