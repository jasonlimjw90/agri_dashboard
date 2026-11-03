
import streamlit as st

from src.config.labels import CROP_LABELS


def render_market_filters(
    df,
    key_prefix="market",
    commodity_col=None,
    crop_col=None,
    default_commodity="corn",
    extra_commodities=None,
):
    commodities = sorted(
        df["commodity"].dropna().unique().tolist(),
        key=lambda x: str(x).casefold(),
    )

    for item in extra_commodities or []:
        if item.casefold() not in [
            str(value).casefold() for value in commodities
        ]:
            commodities.append(item)

    commodities = sorted(
        commodities,
        key=lambda x: str(x).casefold(),
    )

    if not commodities:
        st.info("No commodities available.")
        return None, None

    commodity_lookup = {
        str(value).casefold(): value
        for value in commodities
    }

    default_value = commodity_lookup.get(
        default_commodity.casefold(),
        commodities[0],
    )

    with commodity_col if commodity_col is not None else st.container():
        commodity = st.selectbox(
            "Commodity",
            options=commodities,
            index=commodities.index(default_value),
            format_func=lambda x: str(x).title(),
            key=f"{key_prefix}_commodity",
            width=200,
        )

    with crop_col if crop_col is not None else st.container():
        crop = st.selectbox(
            "Crop",
            options=list(CROP_LABELS.keys()),
            format_func=lambda x: CROP_LABELS[x],
            key=f"{key_prefix}_crop",
            width=200,
        )

    return commodity, crop
