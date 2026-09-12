from pathlib import Path

import numpy as np
import numpy_financial as npf
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


def calculate_npv(cash_flows, discount_rate):
    # Calculating NPV
    return sum(
        cash_flow / ((1 + discount_rate) ** year)
        for year, cash_flow in enumerate(cash_flows)
    )


def calculate_payback(initial_investment, yearly_cash_flows):
    # Calculating payback period
    cumulative_cash = 0.0

    for year, cash_flow in enumerate(yearly_cash_flows, start=1):
        previous_cash = cumulative_cash
        cumulative_cash += cash_flow

        if cumulative_cash >= initial_investment:
            remaining = initial_investment - previous_cash

            if cash_flow <= 0:
                return float(year)

            fraction = remaining / cash_flow
            return (year - 1) + fraction

    return np.nan


def normalize(series, higher_is_better=True):
    # Normalizing project values
    series = pd.to_numeric(series, errors="coerce")

    minimum = series.min()
    maximum = series.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(0.0, index=series.index)

    if maximum == minimum:
        return pd.Series(100.0, index=series.index)

    score = (series - minimum) / (maximum - minimum) * 100

    if not higher_is_better:
        score = 100 - score

    return score


def optimize_portfolio(projects, capital_budget):
    # Selecting the highest NPV portfolio
    eligible = projects[
        (projects["npv_usd_m"] > 0)
        & (projects["irr"] > projects["wacc_used"])
    ].copy()

    if eligible.empty:
        return []

    budget = int(round(capital_budget))

    dp = [0.0] * (budget + 1)
    selected = [[] for _ in range(budget + 1)]

    for _, project in eligible.iterrows():
        cost = int(round(project["initial_investment_usd_m"]))
        value = float(project["npv_usd_m"])
        project_id = project["project_id"]

        for current_budget in range(budget, cost - 1, -1):
            new_value = dp[current_budget - cost] + value

            if new_value > dp[current_budget]:
                dp[current_budget] = new_value
                selected[current_budget] = (
                    selected[current_budget - cost] + [project_id]
                )

    best_budget = max(range(budget + 1), key=lambda x: dp[x])

    return selected[best_budget]


def main():
    # Creating the output folder
    project_root = Path(__file__).resolve().parents[1]
    processed_folder = project_root / "data" / "processed"
    processed_folder.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    # Loading SQL data
    projects = pd.read_sql(
        "SELECT * FROM dbo.clean_capital_projects",
        engine,
    )

    assumptions = pd.read_sql(
        "SELECT * FROM dbo.clean_market_assumptions",
        engine,
    )

    business_units = pd.read_sql(
        "SELECT * FROM dbo.clean_business_units",
        engine,
    )

    # Loading 2026 Base assumptions
    base_2026 = assumptions[
        (assumptions["year"] == 2026)
        & (assumptions["scenario"] == "Base")
    ].copy()

    if len(base_2026) != 1:
        raise ValueError("Expected exactly one 2026 Base market assumption row.")

    wacc = float(base_2026.iloc[0]["wacc"])
    capital_budget = float(base_2026.iloc[0]["capital_budget_usd_m"])

    results = []

    # Calculating project economics
    for _, project in projects.iterrows():
        investment = float(project["initial_investment_usd_m"])

        yearly_cash_flows = [
            float(project["cash_flow_year_1_usd_m"]),
            float(project["cash_flow_year_2_usd_m"]),
            float(project["cash_flow_year_3_usd_m"]),
            float(project["cash_flow_year_4_usd_m"]),
            float(project["cash_flow_year_5_usd_m"]),
        ]

        cash_flows = [-investment] + yearly_cash_flows

        npv = calculate_npv(cash_flows, wacc)
        irr = npf.irr(cash_flows)

        if np.iscomplexobj(irr):
            irr = np.nan
        elif pd.notna(irr):
            irr = float(irr)

        total_inflows = sum(yearly_cash_flows)
        roi = (total_inflows - investment) / investment
        payback = calculate_payback(investment, yearly_cash_flows)

        results.append(
            {
                "project_id": project["project_id"],
                "project_name": project["project_name"],
                "business_unit_id": project["business_unit_id"],
                "region": project["region"],
                "project_type": project["project_type"],
                "strategic_theme": project["strategic_theme"],
                "initial_investment_usd_m": investment,
                "risk_score": int(project["risk_score"]),
                "strategic_priority": int(project["strategic_priority"]),
                "npv_usd_m": npv,
                "irr": irr,
                "roi": roi,
                "payback_years": payback,
                "wacc_used": wacc,
            }
        )

    results = pd.DataFrame(results)

    # Creating score components
    results["npv_score"] = normalize(results["npv_usd_m"])
    results["irr_score"] = normalize(results["irr"].fillna(results["irr"].min()))
    results["roi_score"] = normalize(results["roi"])

    payback_for_score = results["payback_years"].copy()
    payback_fill = payback_for_score.max()

    if pd.isna(payback_fill):
        payback_fill = 5.0

    payback_for_score = payback_for_score.fillna(payback_fill + 1)
    results["payback_score"] = normalize(
        payback_for_score,
        higher_is_better=False,
    )

    results["strategic_priority_score"] = (
        (results["strategic_priority"] - 1) / 4 * 100
    )

    results["risk_score_component"] = (
        (5 - results["risk_score"]) / 4 * 100
    )

    # Calculating capital allocation score
    results["capital_allocation_score"] = (
        results["npv_score"] * 0.35
        + results["irr_score"] * 0.20
        + results["roi_score"] * 0.10
        + results["payback_score"] * 0.10
        + results["strategic_priority_score"] * 0.15
        + results["risk_score_component"] * 0.10
    )

    # Creating recommendation labels
    conditions = [
        (
            (results["npv_usd_m"] > 0)
            & (results["irr"] >= wacc + 0.05)
            & (results["capital_allocation_score"] >= 80)
            & (results["risk_score"] < 5)
        ),
        (
            (results["npv_usd_m"] > 0)
            & (results["irr"] > wacc)
            & (results["capital_allocation_score"] >= 65)
        ),
        (
            (results["npv_usd_m"] > 0)
            & (results["irr"] > wacc)
        ),
    ]

    choices = [
        "Strong Invest",
        "Invest",
        "Review",
    ]

    results["investment_recommendation"] = np.select(
        conditions,
        choices,
        default="Reject",
    )

    # Selecting the best portfolio
    selected_projects = optimize_portfolio(
        results,
        capital_budget,
    )

    results["portfolio_selection"] = np.where(
        results["project_id"].isin(selected_projects),
        "Fund",
        "Do Not Fund",
    )

    # Adding business unit names
    names = business_units[
        ["business_unit_id", "business_unit_name"]
    ].drop_duplicates()

    results = results.merge(
        names,
        on="business_unit_id",
        how="left",
    )

    # Calculating project ranking
    results["capital_allocation_rank"] = (
        results["capital_allocation_score"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )

    # Rounding values
    money_columns = [
        "initial_investment_usd_m",
        "npv_usd_m",
    ]

    results[money_columns] = results[money_columns].round(2)

    score_columns = [
        "npv_score",
        "irr_score",
        "roi_score",
        "payback_score",
        "strategic_priority_score",
        "risk_score_component",
        "capital_allocation_score",
    ]

    results[score_columns] = results[score_columns].round(2)
    results["payback_years"] = results["payback_years"].round(2)

    # Creating portfolio summary
    funded = results[results["portfolio_selection"] == "Fund"].copy()

    total_requested = results["initial_investment_usd_m"].sum()
    funded_capital = funded["initial_investment_usd_m"].sum()
    funded_npv = funded["npv_usd_m"].sum()

    summary = pd.DataFrame(
        [
            {
                "scenario": "2026 Base",
                "wacc": wacc,
                "capital_budget_usd_m": round(capital_budget, 2),
                "requested_capital_usd_m": round(total_requested, 2),
                "funding_gap_usd_m": round(
                    total_requested - capital_budget,
                    2,
                ),
                "funded_projects": len(funded),
                "funded_capital_usd_m": round(funded_capital, 2),
                "unused_capital_usd_m": round(
                    capital_budget - funded_capital,
                    2,
                ),
                "portfolio_npv_usd_m": round(funded_npv, 2),
            }
        ]
    )

    # Ordering result columns
    # Ordering final results
    results["selection_order"] = np.where(
        results["portfolio_selection"] == "Fund",
        0,
        1,
    )

    results = results.sort_values(
        ["selection_order", "capital_allocation_rank"]
    )

    results = results[
        [
            "project_id",
            "project_name",
            "business_unit_id",
            "business_unit_name",
            "region",
            "project_type",
            "strategic_theme",
            "initial_investment_usd_m",
            "risk_score",
            "strategic_priority",
            "wacc_used",
            "npv_usd_m",
            "irr",
            "roi",
            "payback_years",
            "capital_allocation_score",
            "capital_allocation_rank",
            "investment_recommendation",
            "portfolio_selection",
        ]
    ]

    # Saving processed files
    results_path = processed_folder / "capital_allocation_results.csv"
    summary_path = processed_folder / "capital_allocation_summary.csv"

    results.to_csv(results_path, index=False)
    summary.to_csv(summary_path, index=False)

    # Saving SQL tables
    results.to_sql(
        "capital_allocation_results",
        engine,
        schema="dbo",
        if_exists="replace",
        index=False,
    )

    summary.to_sql(
        "capital_allocation_summary",
        engine,
        schema="dbo",
        if_exists="replace",
        index=False,
    )

    print(f"Projects analyzed: {len(results)}")
    print(f"Projects funded: {len(funded)}")
    print(f"Capital budget: ${capital_budget:,.2f}M")
    print(f"Funded capital: ${funded_capital:,.2f}M")
    print(f"Portfolio NPV: ${funded_npv:,.2f}M")
    print(f"Results saved to: {results_path}")
    print(f"Summary saved to: {summary_path}")
    print("SQL table saved as: dbo.capital_allocation_results")
    print("SQL table saved as: dbo.capital_allocation_summary")

    engine.dispose()


if __name__ == "__main__":
    main()
