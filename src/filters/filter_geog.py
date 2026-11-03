import streamlit as st


def render_geography_filter(
    key: str = "geography_filter",
    label: str = "Geography",
    options: list[str] | None = None,
    default: str = "National",
):
    if options is None:
        options = ["National", "State"]

    if not options:
        return None

    index = (
        options.index(default)
        if default in options
        else 0
    )

    return st.radio(
        label,
        options=options,
        index=index,
        horizontal=True,
        key=key,
    )