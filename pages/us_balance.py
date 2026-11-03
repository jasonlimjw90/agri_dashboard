
import streamlit as st

from src.loaders.load_wasde import load_wasde

from src.filters.filter_market import render_market_filters

from src.transforms.transform_df import prepare_wasde_cards

from src.views.snd_us import (
    render_current_my_view,
    render_us_balance_view,
    render_us_monthly_change_view,
)


st.title("US Balance Sheet")

df = load_wasde()

us_df = df[
    df["table"].astype(str).str.casefold().isin(["us", "bc"])
].copy()

if us_df.empty:
    st.info("No US WASDE data available.")
    st.stop()

us_seasonal_df, us_change_df = prepare_wasde_cards(us_df)

col1, col2, col3 = st.columns(
    [1, 1, 10],
    gap="small",
)

commodity, crop = render_market_filters(
    us_seasonal_df,
    key_prefix="us_snd",
    commodity_col=col1,
    crop_col=col2,
    extra_commodities=["Wheat BC"],
)

if commodity is None or crop is None:
    st.stop()

if commodity.casefold() == "wheat bc":
    selected_commodity = "Wheat"
    selected_table = "bc"
else:
    selected_commodity = commodity
    selected_table = "us"

market_filter = (
    us_seasonal_df["commodity"].astype(str).str.casefold()
    == selected_commodity.casefold()
) & (
    us_seasonal_df["table"].astype(str).str.casefold()
    == selected_table.casefold()
) & (
    us_seasonal_df["crop"].astype(str).str.casefold()
    == crop.casefold()
)

change_filter = (
    us_change_df["commodity"].astype(str).str.casefold()
    == selected_commodity.casefold()
) & (
    us_change_df["table"].astype(str).str.casefold()
    == selected_table.casefold()
) & (
    us_change_df["crop"].astype(str).str.casefold()
    == crop.casefold()
)

selected_df = us_seasonal_df[market_filter].copy()
selected_change_df = us_change_df[change_filter].copy()

current_report_filter = (
    us_df["commodity"].astype(str).str.casefold()
    == selected_commodity.casefold()
) & (
    us_df["table"].astype(str).str.casefold()
    == selected_table.casefold()
)

current_report_df = us_df[current_report_filter].copy()

if selected_df.empty:
    st.info(
        "No balance sheet data available for the selected filters."
    )
    st.stop()

label_prefix = "US"
key_prefix = "us_balance"

if commodity.casefold() == "wheat bc":

    wheat_classes = sorted(
        selected_df["wheat_class"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if not wheat_classes:
        st.info("No wheat-class data available.")
        st.stop()

    with col3:
        selected_wheat_class = st.segmented_control(
            "Wheat Class",
            options=wheat_classes,
            default=wheat_classes[0],
            key="us_wheat_class_filter",
            width="stretch",
        )

    if selected_wheat_class is None:
        st.stop()

    seasonal_class_filter = (
        selected_df["wheat_class"].astype(str).str.casefold()
        == selected_wheat_class.casefold()
    )

    change_class_filter = (
        selected_change_df["wheat_class"].astype(str).str.casefold()
        == selected_wheat_class.casefold()
    )

    selected_df = selected_df[seasonal_class_filter].copy()
    selected_change_df = selected_change_df[change_class_filter].copy()

    current_report_df = current_report_df[
        current_report_df["wheat_class"].astype(str).str.casefold()
        == selected_wheat_class.casefold()
    ].copy()

    label_prefix = f"US Wheat {selected_wheat_class}"
    key_prefix = f"us_wheat_bc_{selected_wheat_class}"

if selected_df.empty:
    st.info(
        "No balance sheet data available for the selected filters."
    )
    st.stop()


tab1, tab2, tab3 = st.tabs([
    "WASDE Revisions",
    "US Balance Sheet",
    "Annual MoM Change",
])


with tab1:

    render_current_my_view(
        df=selected_change_df,
        seasonal_df=selected_df,
        commodity=selected_commodity,
        current_report_df=current_report_df,
        cols=2,
        label_prefix=label_prefix,
        key_prefix=f"{key_prefix}_revisions",
    )


with tab2:

    render_us_balance_view(
        market_df=selected_df,
        seasonal_df=selected_df,
        commodity=selected_commodity,
        years=5,
        cols=4,
        key_prefix=f"{key_prefix}_balance",
        card_prefix=f"{key_prefix}_cards",
        label_prefix=label_prefix,
    )


with tab3:

    render_us_monthly_change_view(
        change_df=selected_change_df,
        key_prefix=f"{key_prefix}_monthly_change",
        label_prefix=label_prefix,
    )
