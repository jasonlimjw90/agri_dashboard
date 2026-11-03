
import streamlit as st

from src.config.theme import COMMODITIES


st.set_page_config(
    page_title="Agri Research",
    page_icon="🌾",
    layout="wide",
)

pages = [
    st.Page(
        "pages/global_balance.py",
        title="Global Balance",
    ),
    st.Page(
        "pages/us_balance.py",
        title="US Balance",
    ),
    st.Page(
        "pages/us_supply.py",
        title="US Supply",
    ),
    st.Page(
        "pages/us_demand.py",
        title="US Demand",
    ),
    st.Page(
        "pages/cftc_positioning.py",
        title="CFTC COT",
    ),
    st.Page(
        "pages/estimates.py",
        title="Estimates",
    ),
]


pg = st.navigation(
    pages,
    position="hidden",
)


st.sidebar.markdown(
    """
    <div style="padding: 10px 0 15px 0;">
        <div style="font-size:20px; font-weight:700;">
            🌾 AGRI RESEARCH
        </div>
        <div style="font-size:11px; color:grey; letter-spacing:1px;">
            AGRICULTURAL MARKET INTELLIGENCE
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.divider()

st.sidebar.page_link(
    pages[0],
    label="Global Balance",
    icon=":material/public:",
)

st.sidebar.page_link(
    pages[1],
    label="US Balance",
    icon=":material/location_on:",
)

st.sidebar.page_link(
    pages[2],
    label="US Supply",
    icon=":material/agriculture:",
)

st.sidebar.page_link(
    pages[3],
    label="US Demand",
    icon=":material/trending_up:",
)

st.sidebar.page_link(
    pages[4],
    label="CFTC COT",
    icon=":material/bar_chart:",
)

st.sidebar.page_link(
    pages[5],
    label="Estimates",
    icon=":material/edit_note:",
)

pg.run()
