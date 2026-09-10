USE McKinsey_CFO_Intelligence;
GO

-- Viewing 2025 value creation
WITH value_creation AS
(
    SELECT
        f.business_unit_id,
        b.business_unit_name,
        SUM(f.ttm_nopat_usd_m) AS ttm_nopat_usd_m,
        SUM(f.avg_invested_capital_usd_m) AS avg_invested_capital_usd_m,
        MAX(f.wacc) AS wacc
    FROM dbo.financial_features f
    JOIN dbo.clean_business_units b
        ON f.business_unit_id = b.business_unit_id
    WHERE f.period_end = '2025-12-31'
    GROUP BY f.business_unit_id, b.business_unit_name
)
SELECT
    business_unit_id,
    business_unit_name,
    ROUND(ttm_nopat_usd_m, 2) AS ttm_nopat_usd_m,
    ROUND(avg_invested_capital_usd_m, 2) AS avg_invested_capital_usd_m,
    ROUND(ttm_nopat_usd_m / NULLIF(avg_invested_capital_usd_m, 0) * 100, 2) AS roic_pct,
    ROUND(wacc * 100, 2) AS wacc_pct,
    ROUND(
        (ttm_nopat_usd_m / NULLIF(avg_invested_capital_usd_m, 0) - wacc) * 100,
        2
    ) AS roic_wacc_spread_pp,
    ROUND(
        ttm_nopat_usd_m - (avg_invested_capital_usd_m * wacc),
        2
    ) AS economic_profit_usd_m,
    CASE
        WHEN ttm_nopat_usd_m / NULLIF(avg_invested_capital_usd_m, 0) - wacc >= 0.05
            THEN 'Strong Creator'
        WHEN ttm_nopat_usd_m / NULLIF(avg_invested_capital_usd_m, 0) - wacc >= 0
            THEN 'Creator'
        ELSE 'Value Destroyer'
    END AS value_creation_status
FROM value_creation
ORDER BY roic_wacc_spread_pp DESC;
GO

-- Viewing enterprise value creation
WITH enterprise_value_creation AS
(
    SELECT
        SUM(ttm_nopat_usd_m) AS ttm_nopat_usd_m,
        SUM(avg_invested_capital_usd_m) AS avg_invested_capital_usd_m,
        MAX(wacc) AS wacc
    FROM dbo.financial_features
    WHERE period_end = '2025-12-31'
)
SELECT
    ROUND(ttm_nopat_usd_m, 2) AS ttm_nopat_usd_m,
    ROUND(avg_invested_capital_usd_m, 2) AS avg_invested_capital_usd_m,
    ROUND(ttm_nopat_usd_m / NULLIF(avg_invested_capital_usd_m, 0) * 100, 2) AS roic_pct,
    ROUND(wacc * 100, 2) AS wacc_pct,
    ROUND(
        (ttm_nopat_usd_m / NULLIF(avg_invested_capital_usd_m, 0) - wacc) * 100,
        2
    ) AS roic_wacc_spread_pp,
    ROUND(
        ttm_nopat_usd_m - (avg_invested_capital_usd_m * wacc),
        2
    ) AS economic_profit_usd_m
FROM enterprise_value_creation;
GO
