
import pandas as pd


DATE_COL = "Report_Date_as_YYYY-MM-DD"


def filter_cftc_market(df, market_code):
    return df.loc[
        df["CFTC_Contract_Market_Code"] == market_code
    ].copy()


def filter_cftc_report(df, report_type="Futures Only"):
    return df.loc[
        df["FutOnly_or_Combined"] == report_type
    ].copy()


def filter_cftc_date(df, start_date=None, end_date=None):

    if start_date is not None:
        df = df.loc[
            df[DATE_COL] >= pd.Timestamp(start_date)
        ]

    if end_date is not None:
        df = df.loc[
            df[DATE_COL] <= pd.Timestamp(end_date)
        ]

    return df.copy()


def filter_cftc_contract(df, contract_type="All"):

    if contract_type == "All":
        return df.copy()

    if contract_type == "Old":
        return df.loc[
            df["CFTC_Contract_Market_Code"].notna()
        ].copy()

    if contract_type == "Other":
        return df.loc[
            df["CFTC_Contract_Market_Code"].isna()
        ].copy()

    raise ValueError(
        f"Unknown contract type: {contract_type}"
    )
