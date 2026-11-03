
import streamlit as st

from src.loaders.load_nass import (
    load_cp,
    load_cc,
)

from src.transforms.transform_cp import prepare_cp_data

from src.views.cp_us import (
    render_national,
    render_state,
)

from src.views.cc_us import render_cc_us


st.title("US Crop Supply")


tab_planted, tab_harvested, tab_progress, tab_condition, tab_weather = st.tabs(
    [
        "Planted Area",
        "Harvested Area",
        "Crop Progress",
        "Crop Condition",
        "Weather",
    ]
)


with tab_planted:
    st.info("Planted Area")


with tab_harvested:
    st.info("Harvested Area")


with tab_progress:

    df = load_cp()
    cp_data = prepare_cp_data(df)

    national_tab, state_tab = st.tabs(
        [
            "National",
            "State",
        ]
    )

    with national_tab:
        render_national(
            national_df=cp_data["national"],
        )

    with state_tab:
        render_state(
            state_df=cp_data["state"],
            state_table_df=cp_data["state_table"],
        )


with tab_condition:

    cc_df = load_cc()

    render_cc_us(cc_df)


with tab_weather:
    st.info("Weather")
