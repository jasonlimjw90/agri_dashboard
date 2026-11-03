
import pandas as pd
import streamlit as st

from src.loaders.load_cftc_grains import load_cftc_agri
from src.views.cftc_cot import render_cftc_view


st.title("CFTC Commitment of Traders")

df = load_cftc_agri()

if df.empty:
    st.warning("No CFTC data available.")
    st.stop()

market_col = "Market_and_Exchange_Names"
code_col = "CFTC_Contract_Market_Code"
date_col = "Report_Date_as_YYYY-MM-DD"

required_columns = [
    market_col,
    code_col,
    date_col,
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(f"Missing columns: {missing_columns}")
    st.write("Available columns:")
    st.write(df.columns.tolist())
    st.stop()

market_options = (
    df[[code_col, market_col]]
    .dropna()
    .drop_duplicates()
    .sort_values(market_col)
)

if market_options.empty:
    st.warning("No CFTC markets found.")
    st.stop()

market_names = market_options[market_col].tolist()

filter_columns = st.columns([1, 1, 10], gap="medium")

with filter_columns[0]:
    selected_market = st.selectbox(
        "Market",
        market_names,
    )

with filter_columns[1]:
    trader_group = st.selectbox(
        "Trader Group",
        [
            "Managed Money",
            "Producer/Merchant",
            "Swap Dealer",
            "Other Reportables",
            "Total Reportables",
        ],
    )

market_code = market_options.loc[
    market_options[market_col] == selected_market,
    code_col,
].iloc[0]

df[date_col] = pd.to_datetime(
    df[date_col],
    errors="coerce",
)

render_cftc_view(
    df=df,
    market_code=market_code,
    commodity=selected_market,
    trader_group=trader_group,
)
