from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


SERVER = r"NAREN"
DATABASE = "McKinsey_CFO_Intelligence"
DRIVER = "ODBC Driver 18 for SQL Server"

TABLES = {
    "business_units": "dbo.business_units",
    "financial_performance": "dbo.financial_performance",
    "balance_sheet": "dbo.balance_sheet",
    "budget_forecast": "dbo.budget_forecast",
    "capital_projects": "dbo.capital_projects",
    "market_assumptions": "dbo.market_assumptions",
}


def get_engine():
    # Connecting to SQL Server
    if SERVER == "YOUR_SERVER_NAME":
        raise ValueError("Update SERVER at the top of this file with your SQL Server name.")

    connection_string = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )

    connection_url = URL.create(
        "mssql+pyodbc",
        query={"odbc_connect": connection_string},
    )

    return create_engine(connection_url)


def fill_time_series(df, columns):
    # Filling missing values from the same business series
    df = df.sort_values(["business_unit_id", "region", "period_end"]).copy()

    for column in columns:
        df[column] = df.groupby(["business_unit_id", "region"])[column].transform(
            lambda values: values.interpolate(limit_direction="both")
        )
        df[column] = df[column].fillna(
            df.groupby("business_unit_id")[column].transform("median")
        )
        df[column] = df[column].fillna(df[column].median())

    return df


def add_outlier_flag(df, columns):
    # Flagging unusual one-off values without changing them
    df = df.copy()
    df["outlier_flag"] = 0

    for _, indexes in df.groupby(["business_unit_id", "region"]).groups.items():
        part = df.loc[indexes].sort_values("period_end")
        flag = pd.Series(False, index=part.index)

        for column in columns:
            rolling_median = part[column].rolling(5, center=True, min_periods=3).median()
            relative_change = (
                (part[column] - rolling_median).abs()
                / rolling_median.abs().replace(0, np.nan)
            )
            flag = flag | (relative_change > 0.45)

        df.loc[part.index, "outlier_flag"] = flag.astype(int)

    return df


def clean_financial(df):
    # Cleaning financial performance data
    df = df.drop_duplicates().copy()
    df["period_end"] = pd.to_datetime(df["period_end"], errors="coerce")

    numeric_columns = [
        "revenue_usd_m",
        "cogs_usd_m",
        "operating_expense_usd_m",
        "depreciation_amortization_usd_m",
        "capex_usd_m",
        "effective_tax_rate",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in numeric_columns[:-1]:
        df.loc[df[column] < 0, column] = np.nan

    df.loc[~df["effective_tax_rate"].between(0, 1), "effective_tax_rate"] = np.nan
    df = fill_time_series(df, numeric_columns)
    df = add_outlier_flag(df, numeric_columns[:-1])

    return df.sort_values(["period_end", "business_unit_id", "region"]).reset_index(drop=True)


def clean_balance(df):
    # Cleaning balance sheet data
    df = df.drop_duplicates().copy()
    df["period_end"] = pd.to_datetime(df["period_end"], errors="coerce")

    numeric_columns = [
        "cash_usd_m",
        "accounts_receivable_usd_m",
        "inventory_usd_m",
        "accounts_payable_usd_m",
        "net_fixed_assets_usd_m",
        "total_debt_usd_m",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df.loc[df[column] < 0, column] = np.nan

    df = fill_time_series(df, numeric_columns)
    df = add_outlier_flag(df, numeric_columns)

    return df.sort_values(["period_end", "business_unit_id", "region"]).reset_index(drop=True)


def clean_budget(df):
    # Cleaning budget data
    df = df.drop_duplicates().copy()
    df["period_end"] = pd.to_datetime(df["period_end"], errors="coerce")

    numeric_columns = [
        "budget_revenue_usd_m",
        "budget_ebitda_usd_m",
        "budget_da_usd_m",
        "budget_tax_rate",
        "budget_capex_usd_m",
        "budget_change_nwc_usd_m",
        "budget_fcf_usd_m",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    for column in [
        "budget_revenue_usd_m",
        "budget_ebitda_usd_m",
        "budget_da_usd_m",
        "budget_capex_usd_m",
    ]:
        df.loc[df[column] < 0, column] = np.nan

    df.loc[~df["budget_tax_rate"].between(0, 1), "budget_tax_rate"] = np.nan
    df = fill_time_series(df, numeric_columns)

    return df.sort_values(["period_end", "business_unit_id", "region"]).reset_index(drop=True)


def clean_simple(df):
    # Cleaning master data
    return df.drop_duplicates().reset_index(drop=True)


def main():
    # Creating the output folder
    project_root = Path(__file__).resolve().parents[1]
    processed_folder = project_root / "data" / "processed"
    processed_folder.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    # Loading raw SQL tables
    raw = {}
    for name, table in TABLES.items():
        raw[name] = pd.read_sql(f"SELECT * FROM {table}", engine)

    # Cleaning each dataset
    cleaned = {
        "business_units": clean_simple(raw["business_units"]),
        "financial_performance": clean_financial(raw["financial_performance"]),
        "balance_sheet": clean_balance(raw["balance_sheet"]),
        "budget_forecast": clean_budget(raw["budget_forecast"]),
        "capital_projects": clean_simple(raw["capital_projects"]),
        "market_assumptions": clean_simple(raw["market_assumptions"]),
    }

    # Saving cleaned CSV files and SQL tables
    for name, df in cleaned.items():
        csv_path = processed_folder / f"clean_{name}.csv"
        sql_table = f"clean_{name}"

        df.to_csv(csv_path, index=False)
        df.to_sql(sql_table, engine, schema="dbo", if_exists="replace", index=False)

        print(
            f"{name}: {len(raw[name])} raw rows -> {len(df)} clean rows -> {sql_table}"
        )

    print("\nCleaning completed successfully.")
    print(f"Processed files saved to: {processed_folder}")

    engine.dispose()


if __name__ == "__main__":
    main()
