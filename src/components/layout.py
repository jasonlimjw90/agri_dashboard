import streamlit as st


def page_header(
    title: str,
    description: str = None,
):

    st.subheader(title)

    if description:
        st.caption(description)


def section_header(
    title: str,
    description: str = None,
):

    st.markdown("---")

    st.subheader(title)

    if description:
        st.caption(description)


def filter_section():

    return st.container()


def two_column_layout(ratio=(1, 1)):

    return st.columns(
        ratio,
        gap="medium",
    )


def three_column_layout():

    return st.columns(
        3,
        gap="medium",
    )


def source_caption(
    source: str = None,
    updated: str = None,
):

    parts = []

    if source:
        parts.append(f"Source: {source}")

    if updated:
        parts.append(f"Updated: {updated}")

    if parts:
        st.caption(" | ".join(parts))