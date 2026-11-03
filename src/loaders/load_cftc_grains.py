
from pathlib import Path

import pandas as pd
import streamlit as st

from src.transforms.transform_cftc import clean_cftc_data


ROOT = Path(__file__).resolve().parents[2]

CFTC_FILE = (
    ROOT
    / "data"
    / "processed"
    / "cftc_grains_oilseeds.csv"
)


@st.cache_data(show_spinner=False)
def load_cftc_agri():

    if not CFTC_FILE.exists():
        raise FileNotFoundError(
            f"CFTC data not found: {CFTC_FILE}"
        )

    df = pd.read_csv(
        CFTC_FILE,
        dtype={
            "CFTC_Contract_Market_Code": "string",
            "CFTC_Market_Code": "string",
            "CFTC_Commodity_Code": "string",
        },
        low_memory=False,
    )

    return clean_cftc_data(df)
