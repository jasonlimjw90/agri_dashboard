
import pandas as pd


DATE_COL = "Report_Date_as_YYYY-MM-DD"

CODE_COLUMNS = [
    "CFTC_Contract_Market_Code",
    "CFTC_Market_Code",
    "CFTC_Region_Code",
    "CFTC_Commodity_Code",
    "CFTC_SubGroup_Code",
    "CFTC_Contract_Market_Code_Quotes",
    "CFTC_Market_Code_Quotes",
    "CFTC_Commodity_Code_Quotes",
]

TRADER_GROUPS = {
    "Producer/Merchant": {
        "long": ["Prod_Merc_Positions_Long_All"],
        "short": ["Prod_Merc_Positions_Short_All"],
        "spreading": ["Prod_Merc_Positions_Spread_All"],
    },
    "Swap Dealer": {
        "long": [
            "Swap__Positions_Long_All",
            "Swap_Positions_Long_All",
        ],
        "short": [
            "Swap__Positions_Short_All",
            "Swap_Positions_Short_All",
        ],
        "spreading": [
            "Swap__Positions_Spread_All",
            "Swap_Positions_Spread_All",
        ],
    },
    "Managed Money": {
        "long": ["M_Money_Positions_Long_All"],
        "short": ["M_Money_Positions_Short_All"],
        "spreading": ["M_Money_Positions_Spread_All"],
    },
    "Other Reportables": {
        "long": ["Other_Rept_Positions_Long_All"],
        "short": ["Other_Rept_Positions_Short_All"],
        "spreading": ["Other_Rept_Positions_Spread_All"],
    },
    "Total Reportables": {
        "long": ["Tot_Rept_Positions_Long_All"],
        "short": ["Tot_Rept_Positions_Short_All"],
        "spreading": [],
    },
}


def get_position_column(df, candidates):

    for column in candidates:
        if column in df.columns:
            return column

    return None


def clean_cftc_data(df):

    df = df.copy()
    df.columns = df.columns.str.strip()

    text_columns = df.select_dtypes(
        include=["object", "string"]
    ).columns

    for col in text_columns:
        df[col] = df[col].str.strip()

    for col in CODE_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype("string")

    if "As_of_Date_In_Form_YYMMDD" in df.columns:
        df["As_of_Date_In_Form_YYMMDD"] = pd.to_datetime(
            df["As_of_Date_In_Form_YYMMDD"].astype("string"),
            format="%y%m%d",
            errors="coerce",
        )

    if DATE_COL in df.columns:
        df[DATE_COL] = pd.to_datetime(
            df[DATE_COL],
            errors="coerce",
        )

    excluded = (
        set(CODE_COLUMNS)
        | {
            DATE_COL,
            "As_of_Date_In_Form_YYMMDD",
            "Market_and_Exchange_Names",
            "Contract_Units",
            "FutOnly_or_Combined",
        }
    )

    for col in df.columns:
        if col not in excluded:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

    return df.reset_index(drop=True)


def calculate_net_position(df, long_col, short_col):

    return df[long_col] - df[short_col]


def calculate_percent_oi(
    df,
    position_col,
    oi_col="Open_Interest_All",
):

    return (
        df[position_col]
        .div(df[oi_col].where(df[oi_col] != 0))
        .mul(100)
    )


def calculate_weekly_change(
    df,
    value_col,
    group_col="CFTC_Contract_Market_Code",
):

    df = df.sort_values(DATE_COL)

    if group_col in df.columns:
        return df.groupby(group_col)[value_col].diff()

    return df[value_col].diff()


def prepare_trader_positions(
    df,
    trader_group="Managed Money",
):

    if trader_group not in TRADER_GROUPS:
        raise ValueError(
            f"Unknown trader group: {trader_group}"
        )

    columns = TRADER_GROUPS[trader_group]

    long_col = get_position_column(
        df,
        columns["long"],
    )

    short_col = get_position_column(
        df,
        columns["short"],
    )

    spreading_col = get_position_column(
        df,
        columns["spreading"],
    )

    required = [
        DATE_COL,
        "Open_Interest_All",
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if long_col is None:
        missing.append(columns["long"])

    if short_col is None:
        missing.append(columns["short"])

    if missing:
        raise KeyError(
            f"Missing CFTC columns: {missing}"
        )

    selected_columns = [
        DATE_COL,
        "Market_and_Exchange_Names",
        "CFTC_Contract_Market_Code",
        long_col,
        short_col,
        spreading_col,
        "Open_Interest_All",
    ]

    result = df[
        [
            col for col in selected_columns
            if col is not None and col in df.columns
        ]
    ].copy()

    result = result.sort_values(DATE_COL)

    result["Long"] = result[long_col]
    result["Short"] = result[short_col]

    result["Spreading"] = (
        result[spreading_col]
        if spreading_col is not None
        else 0
    )

    result["Open Interest"] = result["Open_Interest_All"]

    result["Net"] = (
        result["Long"] - result["Short"]
    )

    result["Long % OI"] = calculate_percent_oi(
        result,
        "Long",
    )

    result["Short % OI"] = calculate_percent_oi(
        result,
        "Short",
    )

    result["Net % OI"] = calculate_percent_oi(
        result,
        "Net",
    )

    result["Net Change"] = calculate_weekly_change(
        result,
        "Net",
    )

    return result.reset_index(drop=True)


def prepare_all_trader_positions(df):

    frames = []

    required = [
        DATE_COL,
        "Market_and_Exchange_Names",
        "CFTC_Contract_Market_Code",
    ]

    if any(col not in df.columns for col in required):
        return pd.DataFrame()

    for trader_group, columns in TRADER_GROUPS.items():

        long_col = get_position_column(
            df,
            columns["long"],
        )

        short_col = get_position_column(
            df,
            columns["short"],
        )

        spreading_col = get_position_column(
            df,
            columns["spreading"],
        )

        if long_col is None or short_col is None:
            continue

        selected_columns = [
            DATE_COL,
            "Market_and_Exchange_Names",
            "CFTC_Contract_Market_Code",
            long_col,
            short_col,
            spreading_col,
        ]

        result = df[
            [
                col for col in selected_columns
                if col is not None and col in df.columns
            ]
        ].copy()

        result["Trader Group"] = trader_group
        result["Long"] = result[long_col]
        result["Short"] = result[short_col]

        result["Spreading"] = (
            result[spreading_col]
            if spreading_col is not None
            else 0
        )

        result["Net"] = (
            result["Long"] - result["Short"]
        )

        frames.append(
            result[
                [
                    DATE_COL,
                    "Market_and_Exchange_Names",
                    "CFTC_Contract_Market_Code",
                    "Trader Group",
                    "Long",
                    "Short",
                    "Spreading",
                    "Net",
                ]
            ]
        )

    if not frames:
        return pd.DataFrame()

    return pd.concat(
        frames,
        ignore_index=True,
    )


def prepare_cftc_seasonal_positions(df):

    if df.empty:
        return df.copy()

    result = df.copy()

    result[DATE_COL] = pd.to_datetime(
        result[DATE_COL],
        errors="coerce",
    )

    result = result.dropna(
        subset=[DATE_COL, "Net", "Net % OI"]
    )

    result["Calendar Year"] = (
        result[DATE_COL].dt.year
    )

    result["Season Date"] = pd.to_datetime(
        {
            "year": 2000,
            "month": result[DATE_COL].dt.month,
            "day": result[DATE_COL].dt.day,
        },
        errors="coerce",
    )

    return result.sort_values(
        DATE_COL
    ).reset_index(drop=True)
