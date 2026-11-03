from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"


@st.cache_data(show_spinner=False)
def load_wasde():

    file_path = DATA_DIR / "wasde_processed_all_historicals.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"WASDE processed file not found: {file_path}"
        )

    return pd.read_csv(file_path)