from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


SERVER = r"NAREN"
DATABASE = "McKinsey_CFO_Intelligence"
DRIVER = "ODBC Driver 18 for SQL Server"


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


def main():
    # Creating the output folder
    project_root = Path(__file__).resolve().parents[1]
    processed_folder = project_root / "data" / "processed"
    processed_folder.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    # Loading cleaned SQL tables
    financial = pd.read_sql("SELECT * FROM dbo.clean_financial_performance", engine)
    balance = pd.read_sql("SELECT * FROM dbo.clean_balance_sheet", engine)
    assumptions = pd.read_sql("SELECT * FROM dbo.clean_market_assumptions", engine)

    financial["period_end"] = pd.to_datetime(financial["period_end"])
    balance["period_end"] = pd.to_datetime(balance["period_end"])

    financial = financial.rename(columns={"outlier_flag": "financial_outlier_flag"})
    balance = balance.rename(columns={"outlier_flag": "balance_outlier_flag"})

    keys = ["period_end", "business_unit_id", "region", "currency_code"]

    # Combining financial and balance data
    features = financial.merge(
        balance,
        on=keys,
        how="inner",
        validate="one_to_one",
    )

    features = features.sort_values(
        ["business_unit_id", "region", "period_end"]
    ).reset_index(drop=True)

    features["year"] = features["period_end"].dt.year

    # Calculating operating performance
    features["ebitda_usd_m"] = (
        features["revenue_usd_m"]
        - features["cogs_usd_m"]
        - features["operating_expense_usd_m"]
    )
    features["ebitda_margin"] = (
        features["ebitda_usd_m"] / features["revenue_usd_m"]
    )
    features["ebit_usd_m"] = (
        features["ebitda_usd_m"]
        - features["depreciation_amortization_usd_m"]
    )
    features["nopat_usd_m"] = (
        features["ebit_usd_m"] * (1 - features["effective_tax_rate"])
    )

    # Calculating capital efficiency
    features["net_working_capital_usd_m"] = (
        features["accounts_receivable_usd_m"]
        + features["inventory_usd_m"]
        - features["accounts_payable_usd_m"]
    )
    features["invested_capital_usd_m"] = (
        features["net_working_capital_usd_m"]
        + features["net_fixed_assets_usd_m"]
    )
    features["net_debt_usd_m"] = (
        features["total_debt_usd_m"] - features["cash_usd_m"]
    )

    group_columns = ["business_unit_id", "region"]

    # Calculating cash flow and growth
    features["change_nwc_usd_m"] = (
        features.groupby(group_columns)["net_working_capital_usd_m"]
        .diff()
        .fillna(0)
    )
    features["free_cash_flow_usd_m"] = (
        features["nopat_usd_m"]
        + features["depreciation_amortization_usd_m"]
        - features["capex_usd_m"]
        - features["change_nwc_usd_m"]
    )
    features["revenue_growth_yoy"] = (
        features.groupby(group_columns)["revenue_usd_m"]
        .pct_change(periods=12, fill_method=None)
    )

    # Calculating trailing twelve-month metrics
    features["ttm_nopat_usd_m"] = (
        features.groupby(group_columns)["nopat_usd_m"]
        .transform(lambda values: values.rolling(12, min_periods=12).sum())
    )
    features["ttm_ebitda_usd_m"] = (
        features.groupby(group_columns)["ebitda_usd_m"]
        .transform(lambda values: values.rolling(12, min_periods=12).sum())
    )
    features["avg_invested_capital_usd_m"] = (
        features.groupby(group_columns)["invested_capital_usd_m"]
        .transform(lambda values: values.rolling(12, min_periods=12).mean())
    )

    # Loading historical Base WACC
    assumptions["year"] = pd.to_numeric(assumptions["year"])
    assumptions["wacc"] = pd.to_numeric(assumptions["wacc"])

    base_wacc = (
        assumptions[assumptions["scenario"] == "Base"][["year", "wacc"]]
        .drop_duplicates(subset=["year"])
    )

    features = features.merge(base_wacc, on="year", how="left")

    # Calculating value creation metrics
    features["roic"] = (
        features["ttm_nopat_usd_m"]
        / features["avg_invested_capital_usd_m"]
    )
    features["roic_wacc_spread"] = features["roic"] - features["wacc"]
    features["economic_profit_usd_m"] = (
        features["ttm_nopat_usd_m"]
        - features["avg_invested_capital_usd_m"] * features["wacc"]
    )
    features["net_debt_to_ebitda"] = (
        features["net_debt_usd_m"] / features["ttm_ebitda_usd_m"]
    )

    # Creating value creation labels
    features["value_creation_flag"] = np.select(
        [
            features["roic_wacc_spread"] >= 0.05,
            features["roic_wacc_spread"] >= 0,
            features["roic_wacc_spread"] < 0,
        ],
        ["Strong Creator", "Creator", "Value Destroyer"],
        default="Not Available",
    )

    # Saving engineered features
    output_path = processed_folder / "financial_features.csv"
    features.to_csv(output_path, index=False)
    features.to_sql(
        "financial_features",
        engine,
        schema="dbo",
        if_exists="replace",
        index=False,
    )

    print(f"Feature rows created: {len(features)}")
    print(f"Feature columns created: {len(features.columns)}")
    print(f"CSV saved to: {output_path}")
    print("SQL table saved as: dbo.financial_features")

    engine.dispose()


if __name__ == "__main__":
    main()
