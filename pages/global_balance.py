
import streamlit as st

from src.loaders.load_wasde import load_wasde

from src.filters.filter_market import (
    render_market_filters,
)

from src.filters.filter_country import (
    render_country_filter,
)

from src.transforms.transform_df import (
    prepare_wasde_cards,
)

from src.views.global_snd import (
    render_current_my_view,
    render_global_balance_view,
    render_country_analysis_view,
)


st.title("Global Balance Sheet")

df = load_wasde()

ww_df = df[
    df["table"].astype(str).str.casefold() == "ww"
]

if ww_df.empty:
    st.info("No global WASDE data available.")
    st.stop()

ww_seasonal_df, ww_change_df = prepare_wasde_cards(ww_df)

col1, col2, col3 = st.columns(
    [1, 1, 10],
    gap="small",
)

commodity, crop = render_market_filters(
    ww_seasonal_df,
    key_prefix="global_snd",
    commodity_col=col1,
    crop_col=col2,
)

if commodity is None or crop is None:
    st.stop()

market_filter = (
    ww_seasonal_df["commodity"].astype(str).str.casefold()
    == commodity.casefold()
) & (
    ww_seasonal_df["crop"].astype(str).str.casefold()
    == crop.casefold()
)

change_filter = (
    ww_change_df["commodity"].astype(str).str.casefold()
    == commodity.casefold()
) & (
    ww_change_df["crop"].astype(str).str.casefold()
    == crop.casefold()
)

market_df = ww_seasonal_df[market_filter]
change_df = ww_change_df[change_filter]

if market_df.empty:
    st.info(
        "No data available for the selected commodity and crop."
    )
    st.stop()

world_df = market_df[
    market_df["country"].astype(str).str.casefold() == "world"
]

country_df = market_df[
    market_df["country"].astype(str).str.casefold() != "world"
]

country_change_df = change_df[
    change_df["country"].astype(str).str.casefold() != "world"
]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "WASDE Revisions",
    "World",
    "Exporters",
    "Importers",
    "Country",
])

with tab1:

    selected_country = render_country_filter(
        market_df,
        key="wasde_revision_country",
        label="Country",
        default="World",
    )

    if selected_country is not None:

        revision_df = market_df[
            market_df["country"].astype(str).str.casefold()
            == selected_country.casefold()
        ]

        if revision_df.empty:
            st.info(
                "No WASDE revision data available for this country."
            )
        else:
            render_current_my_view(
                df=revision_df,
                seasonal_df=revision_df,
                commodity=commodity,
                cols=2,
            )

with tab2:

    if world_df.empty:
        st.info("No World-level WASDE data available.")
    else:
        render_global_balance_view(
            market_df=world_df,
            seasonal_df=world_df,
            commodity=commodity,
            years=5,
            cols=4,
            key_prefix="world_historical",
            card_prefix="world_balance",
            label_prefix="World",
        )

with tab3:
    render_country_analysis_view(
        country_df=country_df,
        country_change_df=country_change_df,
        commodity=commodity,
        years=5,
        ranking_item="exports",
        key_prefix="exporters",
    )

with tab4:
    render_country_analysis_view(
        country_df=country_df,
        country_change_df=country_change_df,
        commodity=commodity,
        years=5,
        ranking_item="imports",
        key_prefix="importers",
    )

with tab5:

    col1, col2 = st.columns(
        [1, 10],
        gap="small",
        vertical_alignment="bottom",
    )

    with col1:
        selected_country = render_country_filter(
            country_df,
            key="country_balance_country",
            label="Country",
        )

    if selected_country is not None:

        selected_country_df = country_df[
            country_df["country"].astype(str).str.casefold()
            == selected_country.casefold()
        ]

        render_global_balance_view(
            market_df=selected_country_df,
            seasonal_df=selected_country_df,
            commodity=commodity,
            years=5,
            cols=4,
            key_prefix="country_balance",
            card_prefix="country_balance",
            label_prefix=selected_country,
        )
