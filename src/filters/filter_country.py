
import streamlit as st


def render_country_filter(
    df,
    key: str = "country_filter",
    label: str = "Country",
    default: str = "World",
):
    if df.empty:
        return None

    countries = sorted(
        df["country"].dropna().unique().tolist(),
        key=lambda country: (
            str(country).casefold() != "world",
            str(country).casefold(),
        ),
    )

    if not countries:
        return None

    default_country = next(
        (
            country
            for country in countries
            if str(country).casefold() == default.casefold()
        ),
        countries[0],
    )

    return st.selectbox(
        label,
        options=countries,
        index=countries.index(default_country),
        key=key,
        width = 200,
    )
