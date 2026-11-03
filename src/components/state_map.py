
import pandas as pd
import plotly.graph_objects as go

from src.config.theme import (
    MU,
    BLACK,
    UPC,
    DNC,
)


STATE_ABBREVIATIONS = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District Of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}


STATE_LOOKUP = {
    name.upper(): abbreviation
    for name, abbreviation in STATE_ABBREVIATIONS.items()
}

VALID_STATE_CODES = set(STATE_ABBREVIATIONS.values())


def _get_state_code(state):
    state = str(state).strip()

    if state.upper() in VALID_STATE_CODES:
        return state.upper()

    return STATE_LOOKUP.get(state.upper())


def state_comparison_map(
    df: pd.DataFrame,
    year: int,
    value_label: str = "Value",
    title: str | None = None,
) -> go.Figure:

    fig = go.Figure()

    current_column = str(year)

    if df.empty or current_column not in df.columns:
        return fig

    data = df.copy()

    data["Value"] = pd.to_numeric(
        data[current_column],
        errors="coerce",
    )

    if "5-Year Avg" in data.columns:
        data["5-Year Avg"] = pd.to_numeric(
            data["5-Year Avg"],
            errors="coerce",
        )
    else:
        data["5-Year Avg"] = float("nan")

    data = data.dropna(
        subset=["State", "Value"],
    ).copy()

    data["State Code"] = data["State"].apply(
        _get_state_code,
    )

    data = data.dropna(
        subset=["State Code"],
    )

    if data.empty:
        return fig

    data = data.drop_duplicates(
        subset=["State Code"],
        keep="last",
    ).copy()

    data["Difference"] = (
        data["Value"] - data["5-Year Avg"]
    )

    data["Comparison"] = "—"
    data["Symbol Color"] = MU

    above_average = data["Difference"] > 0
    below_average = data["Difference"] < 0
    equal_average = data["Difference"] == 0

    data.loc[above_average, "Comparison"] = "▲"
    data.loc[below_average, "Comparison"] = "▼"
    data.loc[equal_average, "Comparison"] = "="

    data.loc[above_average, "Symbol Color"] = UPC
    data.loc[below_average, "Symbol Color"] = DNC

    data["Map Label"] = data.apply(
        lambda row: (
            f"{row['State Code']}<br>"
            f"{row['Value']:.1f}% "
            f"<span style='color:{row['Symbol Color']}'>"
            f"<b>{row['Comparison']}</b></span><br>"
            f"<span style='font-size:9px;color:{BLACK}'>"
            f"5Y: {row['5-Year Avg']:.1f}%"
            f"</span>"
            if pd.notna(row["5-Year Avg"])
            else f"{row['State Code']}<br>{row['Value']:.1f}%"
        ),
        axis=1,
    )

    customdata = data[
        [
            "State",
            "5-Year Avg",
            "Difference",
            "Comparison",
        ]
    ].to_numpy()

    fig.add_trace(
        go.Choropleth(
            locations=data["State Code"],
            z=data["Value"],
            locationmode="USA-states",
            customdata=customdata,
            colorscale=[
                [0, "#FFFDE7"],
                [0.25, "#FFF59D"],
                [0.5, "#FFEB3B"],
                [0.75, "#FDD835"],
                [1, "#F9A825"],
            ],
            zmin=0,
            zmax=100,
            marker_line_color="white",
            marker_line_width=0.7,
            colorbar=dict(
                title=dict(text=value_label),
                ticksuffix="%",
                thickness=15,
                len=0.75,
            ),
            hovertemplate=(
                "%{customdata[0]}<br>"
                f"{year} {value_label}: %{{z:.1f}}%<br>"
                "5-Year Avg: %{customdata[1]:.1f}%<br>"
                "Difference: %{customdata[2]:+.1f} pp<br>"
                "Comparison: %{customdata[3]}"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scattergeo(
            locations=data["State Code"],
            locationmode="USA-states",
            text=data["Map Label"],
            mode="text",
            textfont=dict(
                family="Arial Black",
                size=10,
                color=BLACK,
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        title=title,
        height=700,
        autosize=True,
        margin=dict(
            l=10,
            r=10,
            t=55,
            b=10,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(
            scope="usa",
            projection=dict(type="albers usa"),
            showland=True,
            landcolor="#F5F5F5",
            showlakes=True,
            lakecolor="white",
            showcoastlines=False,
            showcountries=False,
            bgcolor="rgba(0,0,0,0)",
        ),
        font=dict(color=MU),
    )

    return fig
