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


def cap_score(value):
    # Limiting severity score
    return max(0.0, min(100.0, value))


def value_destruction_severity(spread):
    # Calculating value destruction severity
    if pd.isna(spread) or spread >= 0:
        return 0.0
    return cap_score(abs(spread) / 0.05 * 100)


def ebitda_miss_severity(variance):
    # Calculating EBITDA miss severity
    if pd.isna(variance) or variance >= 0:
        return 0.0
    return cap_score(abs(variance) / 0.15 * 100)


def fcf_deterioration_severity(change):
    # Calculating FCF deterioration severity
    if pd.isna(change) or change >= 0:
        return 0.0
    return cap_score(abs(change) / 0.20 * 100)


def forecast_risk_severity(revenue_variance, ebitda_variance, accuracy):
    # Calculating forecast risk severity
    revenue_risk = 0.0
    ebitda_risk = 0.0
    accuracy_risk = 0.0

    if pd.notna(revenue_variance) and revenue_variance < 0:
        revenue_risk = cap_score(abs(revenue_variance) / 0.10 * 100)

    if pd.notna(ebitda_variance) and ebitda_variance < 0:
        ebitda_risk = cap_score(abs(ebitda_variance) / 0.15 * 100)

    if pd.notna(accuracy) and accuracy < 90:
        accuracy_risk = cap_score((90 - accuracy) / 10 * 100)

    return max(revenue_risk, ebitda_risk, accuracy_risk)


def get_severity(score, hard_critical=False):
    # Creating risk severity
    if hard_critical or score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def get_issue(row):
    # Creating key issue
    if row["roic_wacc_spread"] < 0:
        return "Value destruction"
    if row["ebitda_budget_variance"] <= -0.075:
        return "EBITDA below budget"
    if row["fcf_change_yoy"] <= -0.10:
        return "Free cash flow deterioration"
    if row["forecast_risk_severity"] >= 40:
        return "2026 forecast risk"
    return "Performance stable"


def get_action(row):
    # Creating recommended action
    actions = []

    if row["roic_wacc_spread"] < 0:
        actions.append("Improve margins and capital efficiency before major expansion")

    if row["ebitda_budget_variance"] <= -0.075:
        actions.append("Review cost and margin drivers behind the EBITDA miss")

    if row["fcf_change_yoy"] <= -0.10:
        actions.append("Tighten working capital and review discretionary CAPEX")

    if row["forecast_risk_severity"] >= 40:
        actions.append("Refresh the 2026 plan and prepare downside actions")

    if not actions:
        actions.append("Maintain current plan and monitor performance")

    return "; ".join(actions)


def get_executive_insight(row):
    # Creating executive insight
    return (
        f"{row['business_unit_name']} has ROIC of {row['roic'] * 100:.1f}% versus "
        f"WACC of {row['wacc'] * 100:.1f}% ({row['roic_wacc_spread'] * 100:+.1f}pp spread). "
        f"2025 EBITDA was {row['ebitda_budget_variance'] * 100:+.1f}% versus budget and "
        f"FCF changed {row['fcf_change_yoy'] * 100:+.1f}% year over year. "
        f"The 2026 EBITDA forecast is {row['forecast_ebitda_vs_budget'] * 100:+.1f}% versus budget "
        f"with average forecast accuracy of {row['average_forecast_accuracy']:.1f}%."
    )


def main():
    # Creating the output folder
    project_root = Path(__file__).resolve().parents[1]
    processed_folder = project_root / "data" / "processed"
    processed_folder.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    # Loading SQL data
    features = pd.read_sql("SELECT * FROM dbo.financial_features", engine)
    business_units = pd.read_sql("SELECT * FROM dbo.clean_business_units", engine)
    budget = pd.read_sql("SELECT * FROM dbo.clean_budget_forecast", engine)
    forecast = pd.read_sql("SELECT * FROM dbo.financial_forecast", engine)
    accuracy = pd.read_sql("SELECT * FROM dbo.forecast_accuracy", engine)
    capital_results = pd.read_sql("SELECT * FROM dbo.capital_allocation_results", engine)
    capital_summary = pd.read_sql("SELECT * FROM dbo.capital_allocation_summary", engine)

    features["period_end"] = pd.to_datetime(features["period_end"])
    budget["period_end"] = pd.to_datetime(budget["period_end"])
    forecast["period_end"] = pd.to_datetime(forecast["period_end"])

    # Creating latest value creation metrics
    latest = features[features["period_end"] == features["period_end"].max()].copy()

    value_creation = (
        latest.groupby("business_unit_id", as_index=False)
        .agg(
            ttm_nopat_usd_m=("ttm_nopat_usd_m", "sum"),
            avg_invested_capital_usd_m=("avg_invested_capital_usd_m", "sum"),
            net_debt_usd_m=("net_debt_usd_m", "sum"),
            ttm_ebitda_usd_m=("ttm_ebitda_usd_m", "sum"),
            wacc=("wacc", "max"),
        )
    )

    value_creation["roic"] = value_creation["ttm_nopat_usd_m"] / value_creation["avg_invested_capital_usd_m"]
    value_creation["roic_wacc_spread"] = value_creation["roic"] - value_creation["wacc"]
    value_creation["economic_profit_usd_m"] = (
        value_creation["ttm_nopat_usd_m"]
        - value_creation["avg_invested_capital_usd_m"] * value_creation["wacc"]
    )
    value_creation["net_debt_to_ebitda"] = value_creation["net_debt_usd_m"] / value_creation["ttm_ebitda_usd_m"]

    # Creating annual financial performance
    features["year"] = features["period_end"].dt.year
    annual_actual = (
        features[features["year"].isin([2024, 2025])]
        .groupby(["year", "business_unit_id"], as_index=False)
        .agg(
            revenue_usd_m=("revenue_usd_m", "sum"),
            ebitda_usd_m=("ebitda_usd_m", "sum"),
            free_cash_flow_usd_m=("free_cash_flow_usd_m", "sum"),
        )
    )

    actual_2024 = annual_actual[annual_actual["year"] == 2024][
        ["business_unit_id", "free_cash_flow_usd_m"]
    ].rename(columns={"free_cash_flow_usd_m": "fcf_2024_usd_m"})

    actual_2025 = annual_actual[annual_actual["year"] == 2025][
        ["business_unit_id", "revenue_usd_m", "ebitda_usd_m", "free_cash_flow_usd_m"]
    ].rename(
        columns={
            "revenue_usd_m": "revenue_2025_usd_m",
            "ebitda_usd_m": "ebitda_2025_usd_m",
            "free_cash_flow_usd_m": "fcf_2025_usd_m",
        }
    )

    # Creating 2025 budget performance
    budget_2025 = budget[budget["period_end"].dt.year == 2025].copy()
    budget_2025 = (
        budget_2025.groupby("business_unit_id", as_index=False)
        .agg(
            budget_revenue_2025_usd_m=("budget_revenue_usd_m", "sum"),
            budget_ebitda_2025_usd_m=("budget_ebitda_usd_m", "sum"),
            budget_fcf_2025_usd_m=("budget_fcf_usd_m", "sum"),
        )
    )

    performance = actual_2025.merge(actual_2024, on="business_unit_id", how="left").merge(
        budget_2025,
        on="business_unit_id",
        how="left",
    )

    performance["ebitda_budget_variance"] = (
        performance["ebitda_2025_usd_m"] - performance["budget_ebitda_2025_usd_m"]
    ) / performance["budget_ebitda_2025_usd_m"].abs()

    performance["fcf_change_yoy"] = (
        performance["fcf_2025_usd_m"] - performance["fcf_2024_usd_m"]
    ) / performance["fcf_2024_usd_m"].abs()

    # Creating 2026 forecast metrics
    forecast_2026 = (
        forecast.groupby("business_unit_id", as_index=False)
        .agg(
            forecast_revenue_2026_usd_m=("forecast_revenue_usd_m", "sum"),
            forecast_ebitda_2026_usd_m=("forecast_ebitda_usd_m", "sum"),
            forecast_fcf_2026_usd_m=("forecast_fcf_usd_m", "sum"),
            budget_revenue_2026_usd_m=("budget_revenue_usd_m", "sum"),
            budget_ebitda_2026_usd_m=("budget_ebitda_usd_m", "sum"),
            budget_fcf_2026_usd_m=("budget_fcf_usd_m", "sum"),
        )
    )

    forecast_2026["forecast_revenue_vs_budget"] = (
        forecast_2026["forecast_revenue_2026_usd_m"] - forecast_2026["budget_revenue_2026_usd_m"]
    ) / forecast_2026["budget_revenue_2026_usd_m"].abs()

    forecast_2026["forecast_ebitda_vs_budget"] = (
        forecast_2026["forecast_ebitda_2026_usd_m"] - forecast_2026["budget_ebitda_2026_usd_m"]
    ) / forecast_2026["budget_ebitda_2026_usd_m"].abs()

    # Creating forecast accuracy metrics
    forecast_accuracy = (
        accuracy.groupby("business_unit_id", as_index=False)
        .agg(
            average_forecast_accuracy=("forecast_accuracy", "mean"),
            minimum_forecast_accuracy=("forecast_accuracy", "min"),
        )
    )

    # Creating CFO intelligence table
    intelligence = (
        value_creation.merge(performance, on="business_unit_id", how="left")
        .merge(forecast_2026, on="business_unit_id", how="left")
        .merge(forecast_accuracy, on="business_unit_id", how="left")
        .merge(
            business_units[["business_unit_id", "business_unit_name"]].drop_duplicates(),
            on="business_unit_id",
            how="left",
        )
    )

    # Calculating severity scores
    intelligence["value_destruction_severity"] = intelligence["roic_wacc_spread"].apply(value_destruction_severity)
    intelligence["ebitda_budget_miss_severity"] = intelligence["ebitda_budget_variance"].apply(ebitda_miss_severity)
    intelligence["fcf_deterioration_severity"] = intelligence["fcf_change_yoy"].apply(fcf_deterioration_severity)
    intelligence["forecast_risk_severity"] = intelligence.apply(
        lambda row: forecast_risk_severity(
            row["forecast_revenue_vs_budget"],
            row["forecast_ebitda_vs_budget"],
            row["average_forecast_accuracy"],
        ),
        axis=1,
    )

    # Calculating CFO priority score
    intelligence["cfo_priority_score"] = (
        intelligence["value_destruction_severity"] * 0.35
        + intelligence["ebitda_budget_miss_severity"] * 0.25
        + intelligence["fcf_deterioration_severity"] * 0.20
        + intelligence["forecast_risk_severity"] * 0.20
    )

    # Creating hard critical rule
    intelligence["hard_critical"] = (
        (intelligence["roic_wacc_spread"] < 0)
        & (intelligence["ebitda_budget_variance"] <= -0.15)
    )

    intelligence["risk_severity"] = intelligence.apply(
        lambda row: get_severity(row["cfo_priority_score"], row["hard_critical"]),
        axis=1,
    )

    # Creating executive messages
    intelligence["key_issue"] = intelligence.apply(get_issue, axis=1)
    intelligence["recommended_action"] = intelligence.apply(get_action, axis=1)
    intelligence["executive_insight"] = intelligence.apply(get_executive_insight, axis=1)

    # Creating business unit ranking
    intelligence["cfo_priority_rank"] = (
        intelligence["cfo_priority_score"].rank(method="dense", ascending=False).astype(int)
    )

    # Creating enterprise leverage action
    enterprise_latest = latest.groupby("period_end", as_index=False).agg(
        net_debt_usd_m=("net_debt_usd_m", "sum"),
        ttm_ebitda_usd_m=("ttm_ebitda_usd_m", "sum"),
    )
    enterprise_leverage = (
        enterprise_latest.iloc[0]["net_debt_usd_m"]
        / enterprise_latest.iloc[0]["ttm_ebitda_usd_m"]
    )

    action_rows = []

    # Creating business unit actions
    for _, row in intelligence.iterrows():
        action_rows.append(
            {
                "category": "Business Unit",
                "entity_name": row["business_unit_name"],
                "priority_score": round(row["cfo_priority_score"], 2),
                "severity": row["risk_severity"],
                "headline": row["key_issue"],
                "executive_insight": row["executive_insight"],
                "recommended_action": row["recommended_action"],
            }
        )

    # Creating leverage action
    leverage_score = 65.0 if enterprise_leverage > 3.0 else 25.0
    leverage_severity = "High" if enterprise_leverage > 3.0 else "Low"

    action_rows.append(
        {
            "category": "Enterprise Risk",
            "entity_name": "Apex Global Holdings",
            "priority_score": leverage_score,
            "severity": leverage_severity,
            "headline": "Elevated leverage" if enterprise_leverage > 3.0 else "Leverage stable",
            "executive_insight": f"Enterprise Net Debt / TTM EBITDA is {enterprise_leverage:.2f}x.",
            "recommended_action": (
                "Protect cash generation and limit non-priority debt-funded investment"
                if enterprise_leverage > 3.0
                else "Maintain current leverage discipline"
            ),
        }
    )

    # Creating capital allocation action
    capital = capital_summary.iloc[0]
    funding_gap = float(capital["funding_gap_usd_m"])
    capital_score = 80.0 if funding_gap > 0 else 30.0

    action_rows.append(
        {
            "category": "Capital Allocation",
            "entity_name": "2026 Base Portfolio",
            "priority_score": capital_score,
            "severity": "Critical" if funding_gap > 0 else "Low",
            "headline": "Capital demand exceeds budget" if funding_gap > 0 else "Capital budget sufficient",
            "executive_insight": (
                f"Requested capital is ${capital['requested_capital_usd_m']:,.0f}M versus a "
                f"${capital['capital_budget_usd_m']:,.0f}M budget. The optimized portfolio funds "
                f"{int(capital['funded_projects'])} projects and creates approximately "
                f"${capital['portfolio_npv_usd_m']:,.0f}M of NPV."
            ),
            "recommended_action": (
                "Fund the optimized positive-NPV portfolio and defer lower-value projects"
                if funding_gap > 0
                else "Proceed with approved positive-NPV projects"
            ),
        }
    )

    # Creating top investment opportunities
    top_projects = (
        capital_results[capital_results["portfolio_selection"] == "Fund"]
        .sort_values("npv_usd_m", ascending=False)
        .head(3)
    )

    for _, project in top_projects.iterrows():
        action_rows.append(
            {
                "category": "Investment Opportunity",
                "entity_name": project["project_name"],
                "priority_score": 60.0,
                "severity": "High",
                "headline": "High-value funded project",
                "executive_insight": (
                    f"{project['project_name']} requires ${project['initial_investment_usd_m']:,.0f}M "
                    f"and generates approximately ${project['npv_usd_m']:,.1f}M NPV with "
                    f"{project['irr'] * 100:.1f}% IRR."
                ),
                "recommended_action": "Protect funding and track delivery against the investment case",
            }
        )

    actions = pd.DataFrame(action_rows)

    severity_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    actions["severity_order"] = actions["severity"].map(severity_order)
    actions = actions.sort_values(
        ["severity_order", "priority_score"],
        ascending=[False, False],
    ).drop(columns="severity_order")
    actions["priority_rank"] = range(1, len(actions) + 1)

    # Rounding intelligence values
    decimal_columns = [
        "roic",
        "wacc",
        "roic_wacc_spread",
        "ebitda_budget_variance",
        "fcf_change_yoy",
        "forecast_revenue_vs_budget",
        "forecast_ebitda_vs_budget",
    ]
    intelligence[decimal_columns] = intelligence[decimal_columns].round(4)

    money_columns = [
        "ttm_nopat_usd_m",
        "avg_invested_capital_usd_m",
        "economic_profit_usd_m",
        "net_debt_usd_m",
        "ttm_ebitda_usd_m",
        "revenue_2025_usd_m",
        "ebitda_2025_usd_m",
        "fcf_2025_usd_m",
        "forecast_revenue_2026_usd_m",
        "forecast_ebitda_2026_usd_m",
        "forecast_fcf_2026_usd_m",
    ]
    intelligence[money_columns] = intelligence[money_columns].round(2)

    score_columns = [
        "average_forecast_accuracy",
        "minimum_forecast_accuracy",
        "value_destruction_severity",
        "ebitda_budget_miss_severity",
        "fcf_deterioration_severity",
        "forecast_risk_severity",
        "cfo_priority_score",
    ]
    intelligence[score_columns] = intelligence[score_columns].round(2)

    intelligence = intelligence[
        [
            "business_unit_id",
            "business_unit_name",
            "roic",
            "wacc",
            "roic_wacc_spread",
            "economic_profit_usd_m",
            "net_debt_to_ebitda",
            "ebitda_budget_variance",
            "fcf_change_yoy",
            "forecast_revenue_vs_budget",
            "forecast_ebitda_vs_budget",
            "average_forecast_accuracy",
            "minimum_forecast_accuracy",
            "value_destruction_severity",
            "ebitda_budget_miss_severity",
            "fcf_deterioration_severity",
            "forecast_risk_severity",
            "cfo_priority_score",
            "cfo_priority_rank",
            "risk_severity",
            "key_issue",
            "executive_insight",
            "recommended_action",
        ]
    ].sort_values("cfo_priority_rank")

    actions = actions[
        [
            "priority_rank",
            "category",
            "entity_name",
            "priority_score",
            "severity",
            "headline",
            "executive_insight",
            "recommended_action",
        ]
    ]

    # Saving processed files
    intelligence_path = processed_folder / "cfo_intelligence_results.csv"
    actions_path = processed_folder / "cfo_priority_actions.csv"

    intelligence.to_csv(intelligence_path, index=False)
    actions.to_csv(actions_path, index=False)

    # Saving SQL tables
    intelligence.to_sql(
        "cfo_intelligence_results",
        engine,
        schema="dbo",
        if_exists="replace",
        index=False,
    )

    actions.to_sql(
        "cfo_priority_actions",
        engine,
        schema="dbo",
        if_exists="replace",
        index=False,
    )

    print(f"Business units analyzed: {len(intelligence)}")
    print(f"CFO actions created: {len(actions)}")
    print(f"Intelligence saved to: {intelligence_path}")
    print(f"Actions saved to: {actions_path}")
    print("SQL table saved as: dbo.cfo_intelligence_results")
    print("SQL table saved as: dbo.cfo_priority_actions")

    engine.dispose()


if __name__ == "__main__":
    main()
