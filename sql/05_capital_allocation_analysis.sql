USE McKinsey_CFO_Intelligence;
GO

-- Viewing project pipeline
SELECT
    COUNT(*) AS total_projects,
    ROUND(SUM(initial_investment_usd_m), 2) AS requested_capital_usd_m,
    ROUND(AVG(initial_investment_usd_m), 2) AS average_project_size_usd_m,
    ROUND(AVG(CAST(risk_score AS decimal(10,2))), 2) AS average_risk_score,
    ROUND(AVG(CAST(strategic_priority AS decimal(10,2))), 2) AS average_priority_score
FROM dbo.clean_capital_projects;
GO

-- Viewing 2026 capital gap
SELECT
    ROUND(SUM(p.initial_investment_usd_m), 2) AS requested_capital_usd_m,
    ROUND(MAX(m.capital_budget_usd_m), 2) AS available_capital_usd_m,
    ROUND(
        SUM(p.initial_investment_usd_m) - MAX(m.capital_budget_usd_m),
        2
    ) AS funding_gap_usd_m
FROM dbo.clean_capital_projects p
CROSS JOIN dbo.clean_market_assumptions m
WHERE m.year = 2026
    AND m.scenario = 'Base';
GO

-- Viewing capital by business unit
SELECT
    b.business_unit_name,
    COUNT(*) AS project_count,
    ROUND(SUM(p.initial_investment_usd_m), 2) AS requested_capital_usd_m,
    ROUND(AVG(CAST(p.risk_score AS decimal(10,2))), 2) AS average_risk_score,
    ROUND(AVG(CAST(p.strategic_priority AS decimal(10,2))), 2) AS average_priority_score
FROM dbo.clean_capital_projects p
JOIN dbo.clean_business_units b
    ON p.business_unit_id = b.business_unit_id
GROUP BY b.business_unit_name
ORDER BY requested_capital_usd_m DESC;
GO

-- Viewing project cash flow potential
SELECT
    p.project_id,
    p.project_name,
    b.business_unit_name,
    p.region,
    p.project_type,
    ROUND(p.initial_investment_usd_m, 2) AS initial_investment_usd_m,
    ROUND(
        p.cash_flow_year_1_usd_m
        + p.cash_flow_year_2_usd_m
        + p.cash_flow_year_3_usd_m
        + p.cash_flow_year_4_usd_m
        + p.cash_flow_year_5_usd_m,
        2
    ) AS total_expected_cash_inflow_usd_m,
    p.risk_score,
    p.strategic_priority
FROM dbo.clean_capital_projects p
JOIN dbo.clean_business_units b
    ON p.business_unit_id = b.business_unit_id
ORDER BY p.strategic_priority DESC, p.risk_score, p.initial_investment_usd_m DESC;
GO
