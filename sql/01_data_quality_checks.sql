USE McKinsey_CFO_Intelligence;
GO

-- Checking table rows
SELECT 'business_units' AS table_name, COUNT(*) AS row_count
FROM dbo.business_units
UNION ALL
SELECT 'financial_performance', COUNT(*) FROM dbo.financial_performance
UNION ALL
SELECT 'balance_sheet', COUNT(*) FROM dbo.balance_sheet
UNION ALL
SELECT 'budget_forecast', COUNT(*) FROM dbo.budget_forecast
UNION ALL
SELECT 'capital_projects', COUNT(*) FROM dbo.capital_projects
UNION ALL
SELECT 'market_assumptions', COUNT(*) FROM dbo.market_assumptions;
GO

-- Checking raw duplicates
SELECT performance_id, COUNT(*) AS duplicate_count
FROM dbo.financial_performance
GROUP BY performance_id
HAVING COUNT(*) > 1;

SELECT balance_id, COUNT(*) AS duplicate_count
FROM dbo.balance_sheet
GROUP BY balance_id
HAVING COUNT(*) > 1;

SELECT plan_id, COUNT(*) AS duplicate_count
FROM dbo.budget_forecast
GROUP BY plan_id
HAVING COUNT(*) > 1;
GO

-- Checking raw missing values
SELECT
    SUM(CASE WHEN revenue_usd_m IS NULL THEN 1 ELSE 0 END) AS revenue_missing,
    SUM(CASE WHEN cogs_usd_m IS NULL THEN 1 ELSE 0 END) AS cogs_missing,
    SUM(CASE WHEN operating_expense_usd_m IS NULL THEN 1 ELSE 0 END) AS opex_missing,
    SUM(CASE WHEN effective_tax_rate IS NULL THEN 1 ELSE 0 END) AS tax_missing
FROM dbo.financial_performance;

SELECT
    SUM(CASE WHEN accounts_receivable_usd_m IS NULL THEN 1 ELSE 0 END) AS receivables_missing,
    SUM(CASE WHEN inventory_usd_m IS NULL THEN 1 ELSE 0 END) AS inventory_missing,
    SUM(CASE WHEN accounts_payable_usd_m IS NULL THEN 1 ELSE 0 END) AS payables_missing
FROM dbo.balance_sheet;

SELECT
    SUM(CASE WHEN budget_revenue_usd_m IS NULL THEN 1 ELSE 0 END) AS revenue_missing,
    SUM(CASE WHEN budget_ebitda_usd_m IS NULL THEN 1 ELSE 0 END) AS ebitda_missing,
    SUM(CASE WHEN budget_tax_rate IS NULL THEN 1 ELSE 0 END) AS tax_missing,
    SUM(CASE WHEN budget_change_nwc_usd_m IS NULL THEN 1 ELSE 0 END) AS nwc_missing
FROM dbo.budget_forecast;
GO

-- Checking clean rows
SELECT 'clean_financial_performance' AS table_name, COUNT(*) AS row_count
FROM dbo.clean_financial_performance
UNION ALL
SELECT 'clean_balance_sheet', COUNT(*) FROM dbo.clean_balance_sheet
UNION ALL
SELECT 'clean_budget_forecast', COUNT(*) FROM dbo.clean_budget_forecast
UNION ALL
SELECT 'financial_features', COUNT(*) FROM dbo.financial_features;
GO

-- Checking clean missing values
SELECT
    SUM(CASE WHEN revenue_usd_m IS NULL THEN 1 ELSE 0 END) AS revenue_missing,
    SUM(CASE WHEN cogs_usd_m IS NULL THEN 1 ELSE 0 END) AS cogs_missing,
    SUM(CASE WHEN operating_expense_usd_m IS NULL THEN 1 ELSE 0 END) AS opex_missing,
    SUM(CASE WHEN effective_tax_rate IS NULL THEN 1 ELSE 0 END) AS tax_missing
FROM dbo.clean_financial_performance;
GO

-- Checking business unit links
SELECT DISTINCT f.business_unit_id
FROM dbo.clean_financial_performance f
LEFT JOIN dbo.clean_business_units b
    ON f.business_unit_id = b.business_unit_id
WHERE b.business_unit_id IS NULL;
GO
