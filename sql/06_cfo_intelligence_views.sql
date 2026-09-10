USE McKinsey_CFO_Intelligence;
GO

-- Creating financial summary view
CREATE OR ALTER VIEW dbo.vw_cfo_financial_summary
AS
SELECT
    f.period_end,
    f.business_unit_id,
    b.business_unit_name,
    f.region,
    f.revenue_usd_m,
    f.ebitda_usd_m,
    f.ebitda_margin,
    f.nopat_usd_m,
    f.free_cash_flow_usd_m,
    f.net_debt_usd_m,
    f.net_debt_to_ebitda
FROM dbo.financial_features f
JOIN dbo.clean_business_units b
    ON f.business_unit_id = b.business_unit_id;
GO

-- Creating value creation view
CREATE OR ALTER VIEW dbo.vw_cfo_value_creation
AS
SELECT
    f.period_end,
    f.business_unit_id,
    b.business_unit_name,
    f.region,
    f.ttm_nopat_usd_m,
    f.avg_invested_capital_usd_m,
    f.roic,
    f.wacc,
    f.roic_wacc_spread,
    f.economic_profit_usd_m,
    f.value_creation_flag
FROM dbo.financial_features f
JOIN dbo.clean_business_units b
    ON f.business_unit_id = b.business_unit_id
WHERE f.ttm_nopat_usd_m IS NOT NULL;
GO

-- Creating budget alert view
CREATE OR ALTER VIEW dbo.vw_cfo_budget_alerts
AS
SELECT
    f.period_end,
    f.business_unit_id,
    b.business_unit_name,
    f.region,
    (f.revenue_usd_m - p.budget_revenue_usd_m)
        / NULLIF(p.budget_revenue_usd_m, 0) AS revenue_variance,
    (f.ebitda_usd_m - p.budget_ebitda_usd_m)
        / NULLIF(p.budget_ebitda_usd_m, 0) AS ebitda_variance,
    (f.free_cash_flow_usd_m - p.budget_fcf_usd_m)
        / NULLIF(ABS(p.budget_fcf_usd_m), 0) AS fcf_variance,
    CASE
        WHEN
            (f.revenue_usd_m - p.budget_revenue_usd_m)
            / NULLIF(p.budget_revenue_usd_m, 0) <= -0.10
            OR
            (f.ebitda_usd_m - p.budget_ebitda_usd_m)
            / NULLIF(p.budget_ebitda_usd_m, 0) <= -0.15
            OR
            (f.free_cash_flow_usd_m - p.budget_fcf_usd_m)
            / NULLIF(ABS(p.budget_fcf_usd_m), 0) <= -0.20
            THEN 'Critical'
        WHEN
            (f.revenue_usd_m - p.budget_revenue_usd_m)
            / NULLIF(p.budget_revenue_usd_m, 0) <= -0.05
            OR
            (f.ebitda_usd_m - p.budget_ebitda_usd_m)
            / NULLIF(p.budget_ebitda_usd_m, 0) <= -0.075
            OR
            (f.free_cash_flow_usd_m - p.budget_fcf_usd_m)
            / NULLIF(ABS(p.budget_fcf_usd_m), 0) <= -0.10
            THEN 'Warning'
        ELSE 'Normal'
    END AS budget_status
FROM dbo.financial_features f
JOIN dbo.clean_budget_forecast p
    ON f.period_end = p.period_end
    AND f.business_unit_id = p.business_unit_id
    AND f.region = p.region
JOIN dbo.clean_business_units b
    ON f.business_unit_id = b.business_unit_id;
GO

-- Creating project pipeline view
CREATE OR ALTER VIEW dbo.vw_cfo_project_pipeline
AS
SELECT
    p.project_id,
    p.project_name,
    p.business_unit_id,
    b.business_unit_name,
    p.region,
    p.project_type,
    p.strategic_theme,
    p.initial_investment_usd_m,
    p.risk_score,
    p.strategic_priority,
    p.status
FROM dbo.clean_capital_projects p
JOIN dbo.clean_business_units b
    ON p.business_unit_id = b.business_unit_id;
GO

-- Checking the views
SELECT TOP 10 *
FROM dbo.vw_cfo_financial_summary
ORDER BY period_end DESC;

SELECT TOP 10 *
FROM dbo.vw_cfo_value_creation
ORDER BY period_end DESC;

SELECT TOP 10 *
FROM dbo.vw_cfo_budget_alerts
ORDER BY period_end DESC;

SELECT TOP 10 *
FROM dbo.vw_cfo_project_pipeline
ORDER BY strategic_priority DESC, risk_score;
GO
