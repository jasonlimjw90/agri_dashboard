
from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = ROOT_DIR / "data" / "processed"

CP_DATA_PATH = PROCESSED_DIR / "cp_processed.csv"
CC_DATA_PATH = PROCESSED_DIR / "cc_processed.csv"


@st.cache_data
def load_cp() -> pd.DataFrame:
    return pd.read_csv(
        CP_DATA_PATH,
        low_memory=False,
        parse_dates=["Week Ending"],
    )


@st.cache_data
def load_cc() -> pd.DataFrame:
    return pd.read_csv(
        CC_DATA_PATH,
        low_memory=False,
        parse_dates=["Week Ending"],
    )
