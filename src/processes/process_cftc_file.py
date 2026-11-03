
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "data" / "raw" / "cftc" / "historicals"
OUTPUT_DIR = ROOT / "data" / "processed" / "cftc"

AGRI_CODES = [
    # Grains & Oilseeds
    "005602", "026603", "007601", "002602",
    "001602", "001612", "001626", "004603", "039601",
]


def process_cftc_agri():

    files = sorted(RAW_DIR.glob("c_year*.txt"))

    if not files:
        raise FileNotFoundError(f"No CFTC TXT files found in {RAW_DIR}")

    # Read and append all historical files
    df = pd.concat(
        [
            pd.read_csv(
                file,
                dtype={
                    "CFTC_Contract_Market_Code": "string",
                    "CFTC_Market_Code": "string",
                    "CFTC_Commodity_Code": "string",
                },
                low_memory=False,
            )
            for file in files
        ],
        ignore_index=True,
    )

    print(f"Total rows appended: {len(df):,}")

    # Keep grains and oilseeds only
    df = df.loc[
        df["CFTC_Contract_Market_Code"].isin(AGRI_CODES)
    ].copy()

    if df.empty:
        raise ValueError("No grains and oilseeds records found.")

    print(f"Filtered rows: {len(df):,}")
    print(f"Markets: {df['CFTC_Contract_Market_Code'].nunique()}")

    # Sort by market and report date
    df["Report_Date_as_YYYY-MM-DD"] = pd.to_datetime(
        df["Report_Date_as_YYYY-MM-DD"],
        errors="coerce",
    )

    df = df.sort_values(
        [
            "CFTC_Contract_Market_Code",
            "Report_Date_as_YYYY-MM-DD",
        ]
    ).reset_index(drop=True)

    # Save processed data
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / "cftc_grains_oilseeds.csv"
    temp_file = OUTPUT_DIR / "cftc_grains_oilseeds.tmp.csv"

    df.to_csv(temp_file, index=False)
    temp_file.replace(output_file)

    if not output_file.exists() or output_file.stat().st_size == 0:
        raise RuntimeError("Output CSV was not saved successfully.")

    print(f"Saved: {output_file}")

    # Delete raw files only after successful save
    for file in files:
        file.unlink()

    print(f"Deleted {len(files)} raw TXT files.")

    return df


if __name__ == "__main__":
    process_cftc_agri()