from pathlib import Path

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

EXPECTED_ROWS = {
    "business_units": 5,
    "financial_performance": 1206,
    "balance_sheet": 1204,
    "budget_forecast": 723,
    "capital_projects": 40,
    "market_assumptions": 20,
}

EXPECTED_DUPLICATES = {
    "business_units": 0,
    "financial_performance": 6,
    "balance_sheet": 4,
    "budget_forecast": 3,
    "capital_projects": 0,
    "market_assumptions": 0,
}

EXPECTED_MISSING = {
    "business_units": 0,
    "financial_performance": 10,
    "balance_sheet": 8,
    "budget_forecast": 6,
    "capital_projects": 0,
    "market_assumptions": 0,
}

VALID_REGIONS = {"North America", "Europe", "Asia Pacific", "Latin America"}


def get_engine():
    # Connecting to SQL Server
    if SERVER == "YOUR_SERVER_NAME":
        raise ValueError("Update SERVER at the top of this file.")

    connection_string = (
        f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};"
        "Trusted_Connection=yes;TrustServerCertificate=yes;"
    )
    url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
    return create_engine(url)


def check(report, name, passed, details):
    status = "PASS" if passed else "CHECK"
    report.append(f"[{status}] {name}: {details}")


def main():
    # Creating the output folder
    project_root = Path(__file__).resolve().parents[1]
    processed_folder = project_root / "data" / "processed"
    processed_folder.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    # Loading raw tables
    data = {
        name: pd.read_sql(f"SELECT * FROM {table}", engine)
        for name, table in TABLES.items()
    }

    report = ["McKinsey CFO Intelligence - Data Validation Report", "=" * 52]

    # Checking basic quality
    for name, df in data.items():
        check(report, f"{name} rows", len(df) == EXPECTED_ROWS[name],
              f"{len(df)} / expected {EXPECTED_ROWS[name]}")
        check(report, f"{name} duplicates", int(df.duplicated().sum()) == EXPECTED_DUPLICATES[name],
              f"{int(df.duplicated().sum())} / expected {EXPECTED_DUPLICATES[name]}")
        check(report, f"{name} missing", int(df.isna().sum().sum()) == EXPECTED_MISSING[name],
              f"{int(df.isna().sum().sum())} / expected {EXPECTED_MISSING[name]}")

    valid_bu = set(data["business_units"]["business_unit_id"])

    # Checking keys and regions
    for name in ["financial_performance", "balance_sheet", "budget_forecast", "capital_projects"]:
        df = data[name]
        bad_bu = int((~df["business_unit_id"].isin(valid_bu)).sum())
        bad_region = int((~df["region"].isin(VALID_REGIONS)).sum())
        check(report, f"{name} business units", bad_bu == 0, f"invalid rows {bad_bu}")
        check(report, f"{name} regions", bad_region == 0, f"invalid rows {bad_region}")

    # Checking currency and dates
    for name in ["financial_performance", "balance_sheet", "budget_forecast"]:
        df = data[name]
        currencies = set(df["currency_code"].dropna())
        dates = pd.to_datetime(df["period_end"], errors="coerce")
        check(report, f"{name} currency", currencies == {"USD"}, f"values {sorted(currencies)}")
        check(report, f"{name} dates", dates.notna().all(), f"invalid dates {int(dates.isna().sum())}")
        report.append(f"    Date range: {dates.min().date()} to {dates.max().date()}")

    # Checking financial rules
    financial = data["financial_performance"].copy()
    financial_cols = ["revenue_usd_m", "cogs_usd_m", "operating_expense_usd_m",
                      "depreciation_amortization_usd_m", "capex_usd_m", "effective_tax_rate"]
    for col in financial_cols:
        financial[col] = pd.to_numeric(financial[col], errors="coerce")

    complete = financial.dropna(subset=financial_cols)
    ebitda = complete["revenue_usd_m"] - complete["cogs_usd_m"] - complete["operating_expense_usd_m"]
    check(report, "positive revenue", bool((complete["revenue_usd_m"] > 0).all()), "checking complete rows")
    check(report, "positive EBITDA", bool((ebitda > 0).all()), "checking complete rows")
    check(report, "tax rates", bool(complete["effective_tax_rate"].between(0, 1).all()), "expected 0 to 1")

    # Checking financial and balance grain
    fp = data["financial_performance"].drop_duplicates()
    bs = data["balance_sheet"].drop_duplicates()
    keys = ["period_end", "business_unit_id", "region"]
    fp_keys = set(map(tuple, fp[keys].astype(str).values))
    bs_keys = set(map(tuple, bs[keys].astype(str).values))
    check(report, "financial vs balance grain", fp_keys == bs_keys,
          f"financial {len(fp_keys)}, balance {len(bs_keys)}")

    # Checking budget FCF
    budget = data["budget_forecast"].copy()
    budget_cols = ["budget_ebitda_usd_m", "budget_da_usd_m", "budget_tax_rate",
                   "budget_capex_usd_m", "budget_change_nwc_usd_m", "budget_fcf_usd_m"]
    for col in budget_cols:
        budget[col] = pd.to_numeric(budget[col], errors="coerce")

    budget = budget.dropna(subset=budget_cols)
    budget_ebit = budget["budget_ebitda_usd_m"] - budget["budget_da_usd_m"]
    budget_nopat = budget_ebit * (1 - budget["budget_tax_rate"])
    expected_fcf = budget_nopat + budget["budget_da_usd_m"] - budget["budget_capex_usd_m"] - budget["budget_change_nwc_usd_m"]
    max_diff = float((expected_fcf - budget["budget_fcf_usd_m"]).abs().max())
    check(report, "budget FCF", max_diff <= 0.02, f"maximum difference {max_diff:.4f}")

    # Checking assumptions and capital budget
    assumptions = data["market_assumptions"].copy()
    for col in ["wacc", "terminal_growth_rate", "capital_budget_usd_m"]:
        assumptions[col] = pd.to_numeric(assumptions[col], errors="coerce")

    check(report, "WACC > terminal growth",
          bool((assumptions["wacc"] > assumptions["terminal_growth_rate"]).all()),
          "checking all scenario rows")

    projects = data["capital_projects"].copy()
    projects["initial_investment_usd_m"] = pd.to_numeric(projects["initial_investment_usd_m"], errors="coerce")
    requested = projects["initial_investment_usd_m"].sum()
    available = assumptions.loc[(assumptions["year"] == 2026) & (assumptions["scenario"] == "Base"),
                                "capital_budget_usd_m"].iloc[0]
    check(report, "capital constraint", requested > available,
          f"requested ${requested:,.2f}M, available ${available:,.2f}M")

    # Saving the report
    report_path = processed_folder / "data_validation_report.txt"
    report_path.write_text("\n".join(report), encoding="utf-8")

    print("\n".join(report))
    print(f"\nSaved: {report_path}")
    engine.dispose()


if __name__ == "__main__":
    main()
