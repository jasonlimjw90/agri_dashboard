import streamlit as st


def render_state_filter(
    df,
    key: str = "state_filter",
    label: str = "State",
    column: str = "State",
):
    if df.empty or column not in df.columns:
        return None

    states = sorted(
        df[column].dropna().unique().tolist(),
        key=lambda state: str(state).casefold(),
    )

    if not states:
        return None

    return st.selectbox(
        label,
        options=states,
        key=key,
        width=200,
    )