
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "wasde"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

MASTER_FILE = PROCESSED_DIR / "wasde_processed_all_historicals.csv"


def append_wasde():

    if not MASTER_FILE.exists():
        raise FileNotFoundError(MASTER_FILE)

    files = sorted(RAW_DIR.glob("wasde_processed_*.csv"))

    if not files:
        print("No weekly WASDE files to process.")
        return

    historical = pd.read_csv(MASTER_FILE)

    if historical.columns.duplicated().any():
        raise ValueError("Duplicate columns in historical file.")

    if "Report Date" not in historical.columns:
        raise ValueError("Report Date column missing.")

    if "Value" not in historical.columns:
        raise ValueError("Value column missing.")

    key_columns = [
        column
        for column in historical.columns
        if column != "Value"
    ]

    historical["Report Date"] = pd.to_datetime(
        historical["Report Date"],
        format="mixed",
        errors="raise",
    )

    datasets = [historical]

    for file in files:

        weekly = pd.read_csv(file)

        if weekly.columns.duplicated().any():
            raise ValueError(
                f"Duplicate columns in {file.name}"
            )

        if set(weekly.columns) != set(historical.columns):
            raise ValueError(
                f"Column mismatch in {file.name}"
            )

        weekly = weekly[historical.columns]

        weekly["Report Date"] = pd.to_datetime(
            weekly["Report Date"],
            format="mixed",
            errors="raise",
        )

        datasets.append(weekly)

        print(f"Loaded {file.name}: {len(weekly):,} rows")

    combined = pd.concat(
        datasets,
        ignore_index=True,
    )

    combined = combined.drop_duplicates(
        subset=key_columns,
        keep="last",
    )

    combined = combined.sort_values(
        "Report Date",
        kind="stable",
    ).reset_index(drop=True)

    temp_file = MASTER_FILE.with_name(
        MASTER_FILE.stem + ".tmp.csv"
    )

    try:

        combined.to_csv(
            temp_file,
            index=False,
            date_format="%Y-%m-%d",
        )

        temp_file.replace(MASTER_FILE)

    except Exception:

        if temp_file.exists():
            temp_file.unlink()

        raise

    new_rows = len(combined) - len(historical)

    print("\nWASDE update completed.")
    print(f"Previous rows: {len(historical):,}")
    print(f"Updated rows: {len(combined):,}")
    print(f"Net new rows: {new_rows:,}")

    for file in files:

        file.unlink()

        print(f"Deleted: {file.name}")

    print("\nAll processed weekly files deleted.")


if __name__ == "__main__":
    append_wasde()
