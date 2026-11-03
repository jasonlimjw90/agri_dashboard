
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def get_latest_cftc_file():

    files = list(
        PROCESSED_DIR.glob("cftc_data_*.csv")
    )

    if not files:
        raise FileNotFoundError(
            f"No processed CFTC files found in {PROCESSED_DIR}. "
            "Run process_cftc_files() first."
        )

    return max(
        files,
        key=lambda path: path.stat().st_mtime,
    )


def get_latest_cftc_agri_file():

    files = list(
        PROCESSED_DIR.glob("cftc_agri_*.csv")
    )

    if not files:
        raise FileNotFoundError(
            f"No processed agricultural CFTC files found "
            f"in {PROCESSED_DIR}. "
            "Run process_cftc_files() first."
        )

    return max(
        files,
        key=lambda path: path.stat().st_mtime,
    )


@st.cache_data(show_spinner=False)
def _read_cftc_csv(file_path, modified_time):

    df = pd.read_csv(
        file_path,
        low_memory=False,
        dtype={
            "cftc_contract_market_code": "string",
            "cftc_commodity_code": "string",
        },
    )

    date_col = "report_date_as_yyyy-mm-dd"

    if date_col in df.columns:
        df[date_col] = pd.to_datetime(
            df[date_col],
            errors="coerce",
        )

    return df


#load cftc full set f&o only

def load_processed_cftc():

    latest_file = get_latest_cftc_file()

    return _read_cftc_csv(
        str(latest_file),
        latest_file.stat().st_mtime_ns,
    )

#load cftc agri f&o only

def load_cftc_agri():
   
    latest_file = get_latest_cftc_agri_file()

    return _read_cftc_csv(
        str(latest_file),
        latest_file.stat().st_mtime_ns,
    )
