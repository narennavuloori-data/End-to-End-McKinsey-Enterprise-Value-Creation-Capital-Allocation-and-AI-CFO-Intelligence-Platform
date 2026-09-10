USE McKinsey_CFO_Intelligence;
GO

-- Viewing annual company performance
WITH annual_company AS
(
    SELECT
        YEAR(period_end) AS year,
        SUM(revenue_usd_m) AS revenue_usd_m,
        SUM(ebitda_usd_m) AS ebitda_usd_m,
        SUM(nopat_usd_m) AS nopat_usd_m,
        SUM(free_cash_flow_usd_m) AS free_cash_flow_usd_m
    FROM dbo.financial_features
    GROUP BY YEAR(period_end)
)
SELECT
    year,
    ROUND(revenue_usd_m, 2) AS revenue_usd_m,
    ROUND(ebitda_usd_m, 2) AS ebitda_usd_m,
    ROUND(ebitda_usd_m / NULLIF(revenue_usd_m, 0) * 100, 2) AS ebitda_margin_pct,
    ROUND(nopat_usd_m, 2) AS nopat_usd_m,
    ROUND(free_cash_flow_usd_m, 2) AS free_cash_flow_usd_m,
    ROUND(
        (revenue_usd_m - LAG(revenue_usd_m) OVER (ORDER BY year))
        / NULLIF(LAG(revenue_usd_m) OVER (ORDER BY year), 0) * 100,
        2
    ) AS revenue_growth_pct
FROM annual_company
ORDER BY year;
GO

-- Viewing business unit performance
SELECT
    YEAR(f.period_end) AS year,
    b.business_unit_name,
    ROUND(SUM(f.revenue_usd_m), 2) AS revenue_usd_m,
    ROUND(SUM(f.ebitda_usd_m), 2) AS ebitda_usd_m,
    ROUND(SUM(f.ebitda_usd_m) / NULLIF(SUM(f.revenue_usd_m), 0) * 100, 2) AS ebitda_margin_pct,
    ROUND(SUM(f.nopat_usd_m), 2) AS nopat_usd_m,
    ROUND(SUM(f.free_cash_flow_usd_m), 2) AS free_cash_flow_usd_m
FROM dbo.financial_features f
JOIN dbo.clean_business_units b
    ON f.business_unit_id = b.business_unit_id
GROUP BY YEAR(f.period_end), b.business_unit_name
ORDER BY year, revenue_usd_m DESC;
GO

-- Viewing 2025 regional performance
SELECT
    region,
    ROUND(SUM(revenue_usd_m), 2) AS revenue_usd_m,
    ROUND(SUM(ebitda_usd_m), 2) AS ebitda_usd_m,
    ROUND(SUM(ebitda_usd_m) / NULLIF(SUM(revenue_usd_m), 0) * 100, 2) AS ebitda_margin_pct,
    ROUND(SUM(free_cash_flow_usd_m), 2) AS free_cash_flow_usd_m
FROM dbo.financial_features
WHERE YEAR(period_end) = 2025
GROUP BY region
ORDER BY revenue_usd_m DESC;
GO

-- Viewing monthly trend
SELECT
    period_end,
    ROUND(SUM(revenue_usd_m), 2) AS revenue_usd_m,
    ROUND(SUM(ebitda_usd_m), 2) AS ebitda_usd_m
FROM dbo.financial_features
GROUP BY period_end
ORDER BY period_end;
GO
