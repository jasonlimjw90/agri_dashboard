
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT_DIR / "data" / "raw" / "nass"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

CP_OUTPUT_PATH = PROCESSED_DIR / "cp_processed.csv"
CC_OUTPUT_PATH = PROCESSED_DIR / "cc_processed.csv"


def get_input_files(
    prefix: str,
) -> list[Path]:

    return sorted(
        file_path
        for file_path in RAW_DIR.iterdir()
        if file_path.is_file()
        and file_path.suffix.lower() == ".csv"
        and file_path.name.lower().startswith(prefix.lower())
    )


def process_files(
    file_paths: list[Path],
    output_path: Path,
) -> pd.DataFrame:

    if not file_paths:
        raise FileNotFoundError(
            f"No input files found for {output_path.name}."
        )

    dataframes = []

    for file_path in file_paths:

        data = pd.read_csv(
            file_path,
            low_memory=False,
        )

        dataframes.append(data)

    data = pd.concat(
        dataframes,
        ignore_index=True,
    )

    data["Year"] = pd.to_numeric(
        data["Year"],
        errors="coerce",
    ).astype("Int64")

    data["Week Ending"] = pd.to_datetime(
        data["Week Ending"],
        errors="coerce",
    )

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

    data["Data Item"] = (
        data["Data Item"]
        .astype("string")
        .str.strip()
    )

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        output_path,
        index=False,
    )

    return data


def process_cp() -> pd.DataFrame:

    return process_files(
        get_input_files("cp"),
        CP_OUTPUT_PATH,
    )


def process_cc() -> pd.DataFrame:

    return process_files(
        get_input_files("cc"),
        CC_OUTPUT_PATH,
    )


if __name__ == "__main__":

    cp_df = process_cp()
    cp_files = get_input_files("cp")

    print("\nCROP PROGRESS")
    print(f"Processed file: {CP_OUTPUT_PATH}")
    print(f"Shape: {cp_df.shape}")
    print(f"Files combined: {len(cp_files)}")
    print([file.name for file in cp_files])

    cc_df = process_cc()
    cc_files = get_input_files("cc")

    print("\nCROP CONDITION")
    print(f"Processed file: {CC_OUTPUT_PATH}")
    print(f"Shape: {cc_df.shape}")
    print(f"Files combined: {len(cc_files)}")
    print([file.name for file in cc_files])
