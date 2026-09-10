USE McKinsey_CFO_Intelligence;
GO

-- Viewing annual budget variance
SELECT
    YEAR(f.period_end) AS year,
    b.business_unit_name,
    ROUND(SUM(f.revenue_usd_m), 2) AS actual_revenue_usd_m,
    ROUND(SUM(p.budget_revenue_usd_m), 2) AS budget_revenue_usd_m,
    ROUND(
        (SUM(f.revenue_usd_m) - SUM(p.budget_revenue_usd_m))
        / NULLIF(SUM(p.budget_revenue_usd_m), 0) * 100,
        2
    ) AS revenue_variance_pct,
    ROUND(SUM(f.ebitda_usd_m), 2) AS actual_ebitda_usd_m,
    ROUND(SUM(p.budget_ebitda_usd_m), 2) AS budget_ebitda_usd_m,
    ROUND(
        (SUM(f.ebitda_usd_m) - SUM(p.budget_ebitda_usd_m))
        / NULLIF(SUM(p.budget_ebitda_usd_m), 0) * 100,
        2
    ) AS ebitda_variance_pct,
    ROUND(SUM(f.free_cash_flow_usd_m), 2) AS actual_fcf_usd_m,
    ROUND(SUM(p.budget_fcf_usd_m), 2) AS budget_fcf_usd_m,
    ROUND(
        (SUM(f.free_cash_flow_usd_m) - SUM(p.budget_fcf_usd_m))
        / NULLIF(ABS(SUM(p.budget_fcf_usd_m)), 0) * 100,
        2
    ) AS fcf_variance_pct
FROM dbo.financial_features f
JOIN dbo.clean_budget_forecast p
    ON f.period_end = p.period_end
    AND f.business_unit_id = p.business_unit_id
    AND f.region = p.region
JOIN dbo.clean_business_units b
    ON f.business_unit_id = b.business_unit_id
WHERE YEAR(f.period_end) IN (2024, 2025)
GROUP BY YEAR(f.period_end), b.business_unit_name
ORDER BY year, revenue_variance_pct;
GO

-- Viewing 2025 budget alerts
SELECT
    f.period_end,
    b.business_unit_name,
    f.region,
    ROUND(
        (f.revenue_usd_m - p.budget_revenue_usd_m)
        / NULLIF(p.budget_revenue_usd_m, 0) * 100,
        2
    ) AS revenue_variance_pct,
    ROUND(
        (f.ebitda_usd_m - p.budget_ebitda_usd_m)
        / NULLIF(p.budget_ebitda_usd_m, 0) * 100,
        2
    ) AS ebitda_variance_pct,
    ROUND(
        (f.free_cash_flow_usd_m - p.budget_fcf_usd_m)
        / NULLIF(ABS(p.budget_fcf_usd_m), 0) * 100,
        2
    ) AS fcf_variance_pct,
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
    ON f.business_unit_id = b.business_unit_id
WHERE YEAR(f.period_end) = 2025
ORDER BY f.period_end, b.business_unit_name, f.region;
GO

-- Viewing Industrial Europe 2025
SELECT
    f.period_end,
    ROUND(f.revenue_usd_m, 2) AS actual_revenue_usd_m,
    ROUND(p.budget_revenue_usd_m, 2) AS budget_revenue_usd_m,
    ROUND(
        (f.revenue_usd_m - p.budget_revenue_usd_m)
        / NULLIF(p.budget_revenue_usd_m, 0) * 100,
        2
    ) AS revenue_variance_pct,
    ROUND(
        (f.ebitda_usd_m - p.budget_ebitda_usd_m)
        / NULLIF(p.budget_ebitda_usd_m, 0) * 100,
        2
    ) AS ebitda_variance_pct
FROM dbo.financial_features f
JOIN dbo.clean_budget_forecast p
    ON f.period_end = p.period_end
    AND f.business_unit_id = p.business_unit_id
    AND f.region = p.region
WHERE f.business_unit_id = 'BU04'
    AND f.region = 'Europe'
    AND YEAR(f.period_end) = 2025
ORDER BY f.period_end;
GO
