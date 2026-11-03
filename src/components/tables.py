
import streamlit as st

from src.config.theme import (
    UPC,
    DNC,
    UP_RGB,
    DN_RGB,
)


def fmt(value: float, decimals: int = 1) -> str:

    sign = "+" if value >= 0 else "−"

    return sign + f"{abs(value):.{decimals}f}"


def colored(
    value: float,
    decimals: int = 1,
    label: str = "",
) -> str:

    color = "green" if value >= 0 else "red"

    return f":{color}[{fmt(value, decimals)}] {label}".strip()


def heat(value: float, maximum: float) -> str:

    if maximum == 0:
        return ""

    alpha = min(abs(value) / maximum, 1) * 0.38

    rgb = UP_RGB if value >= 0 else DN_RGB

    return f"background-color: rgba({rgb},{alpha:.2f})"


def sign_color(value: float) -> str:

    color = UPC if value >= 0 else DNC

    return f"color:{color}"


def style_map(styler, function, subset):

    if hasattr(styler, "map"):
        return styler.map(function, subset=subset)

    return styler.applymap(function, subset=subset)


def usda_table_style(styler):

    return styler.set_table_styles(
        [
            {
                "selector": "table",
                "props": [
                    ("border-collapse", "collapse"),
                    ("border", "none"),
                    ("font-family", "Arial, sans-serif"),
                    ("font-size", "13px"),
                    ("width", "100%"),
                ],
            },
            {
                "selector": "thead th",
                "props": [
                    ("background-color", "#FFFFFF"),
                    ("color", "#002D72"),
                    ("font-weight", "700"),
                    ("border", "none"),
                    ("border-bottom", "2px solid #002D72"),
                    ("padding", "8px 12px"),
                    ("text-align", "right"),
                ],
            },
            {
                "selector": "thead th:first-child",
                "props": [
                    ("text-align", "left"),
                ],
            },
            {
                "selector": "tbody th",
                "props": [
                    ("font-weight", "700"),
                    ("color", "#222222"),
                    ("background-color", "#FFFFFF"),
                    ("border", "none"),
                    ("padding", "7px 12px"),
                    ("text-align", "left"),
                ],
            },
            {
                "selector": "tbody td",
                "props": [
                    ("background-color", "#FFFFFF"),
                    ("color", "#222222"),
                    ("border", "none"),
                    ("padding", "7px 12px"),
                    ("text-align", "right"),
                ],
            },
        ],
        overwrite=True,
    )


def render_styled_table(styled):

    st.markdown(
        styled.to_html(),
        unsafe_allow_html=True,
    )
