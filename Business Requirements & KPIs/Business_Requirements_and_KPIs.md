# Phase 1 — Business Requirements & KPI Blueprint

## Project
**End-to-End McKinsey Enterprise Value Creation, Capital Allocation & AI CFO Intelligence Platform**

## Phase 1 status
**LOCKED / READY FOR PHASE 2**

This document is the master functional blueprint for Phase 1. It defines the business problem, stakeholders, scope, decision questions, analytical requirements, KPI logic, business rules, executive-alert thresholds, implementation ownership, and acceptance criteria.

The detailed machine-friendly KPI catalog is provided separately in `Phase_1_KPI_Catalog.xlsx`.

---

## 1. Executive objective

Build a portfolio-grade CFO decision-support platform that answers one central question:

> **Where is the enterprise creating or destroying economic value, where should the next unit of capital be allocated, what is likely to happen next, and what should the CFO act on first?**

The platform is intentionally narrower than a full ERP, accounting system, or investment-bank valuation workbook. It focuses on the financial decisions most useful for a modern CFO / FP&A / corporate-finance / consulting portfolio project:

1. Enterprise financial performance
2. Economic value creation
3. Budget and forecast steering
4. Capital allocation
5. Scenario-based enterprise valuation
6. AI-enabled CFO prioritization and executive insights

---

## 2. Business problem

A fictional diversified enterprise operates multiple business units and must make decisions using fragmented financial, balance-sheet, budget, project-investment, and market-assumption data.

Management currently lacks a single analytical layer that can:

- distinguish accounting growth from true economic value creation;
- compare ROIC with the cost of capital;
- identify business units that create or destroy value;
- explain budget and margin gaps;
- forecast revenue, EBITDA and free cash flow;
- quantify enterprise-value outcomes under Bear / Base / Bull scenarios;
- rank investment projects using NPV, IRR, ROI, payback, risk and strategic priority;
- recommend a project portfolio under a finite capital budget;
- surface the most important CFO risks and opportunities with transparent evidence.

---

## 3. Primary stakeholders

| Stakeholder | Primary decisions supported |
|---|---|
| Group CFO | Enterprise value, capital allocation, performance steering, risk priorities |
| FP&A Director | Budget variance, forecasting, scenario planning, forecast accuracy |
| Business Unit CFO / Finance Lead | BU profitability, ROIC, working capital, corrective actions |
| Corporate Development / Strategy | Project economics, investment prioritization, enterprise valuation |
| Treasury / Finance Leadership | Net debt, leverage context, WACC assumptions |
| Executive Committee | High-level value creation, scenarios and investment trade-offs |
| Recruiter / Hiring Manager | Traceable demonstration of SQL, Python, Power BI and finance analytics |

---

## 4. In scope

- Monthly enterprise and business-unit financial performance
- Revenue, EBITDA, EBIT, NOPAT and FCF analysis
- Working-capital and invested-capital analysis
- ROIC, WACC, ROIC-WACC spread and Economic Profit
- Simplified DCF enterprise valuation
- Actual vs Budget analysis
- Forward financial forecasting
- Bear / Base / Bull scenarios
- WACC / terminal-growth valuation sensitivity
- Project NPV, IRR, ROI and payback
- Constrained capital-allocation recommendation
- Explainable CFO alerting / prioritization
- Power BI executive dashboards
- Synthetic, reproducible data pipeline using MS SQL + Python

## 5. Explicitly out of scope

To keep the project simple and high quality, the following are **not** required:

- Full statutory accounting or audited financial statements
- Full three-statement financial model with every accounting schedule
- Bank-specific regulatory capital (CET1, RWA, Basel, liquidity ratios)
- Credit underwriting / loan default modelling
- Derivatives, options or complex treasury hedging
- Tax structuring
- M&A purchase accounting
- Full market-beta / peer-comps WACC build
- Real-time streaming architecture
- Mandatory cloud infrastructure
- Mandatory paid LLM/API dependency
- Black-box investment recommendations without traceable financial logic

---

## 6. Five business modules

### Module A — Enterprise Financial Performance
Answers: **How are we performing?**

Core outputs: Revenue, growth, EBITDA, EBITDA margin, EBIT, NOPAT, FCF, leverage and trend analysis.

### Module B — Enterprise Value Creation
Answers: **Are we earning returns above our cost of capital, and why?**

Core outputs: Invested Capital, ROIC, WACC, ROIC-WACC spread, Economic Profit, ROIC driver tree and creator/destroyer matrix.

### Module C — Planning, Forecasting & Scenario Intelligence
Answers: **Where are we missing plan and what happens next?**

Core outputs: Actual vs Budget, forecast accuracy, Revenue/EBITDA/FCF forecast, Bear/Base/Bull scenarios and DCF sensitivity.

### Module D — Capital Allocation
Answers: **Which projects should receive finite capital?**

Core outputs: NPV, IRR, ROI, Payback, Capital Allocation Score, Invest/Review/Reject labels and constrained portfolio recommendation.

### Module E — AI CFO Intelligence
Answers: **What should management act on first?**

Core outputs: CFO Priority Score, Risk Severity, root-cause evidence and executive action recommendations.

---

## 7. Business requirements traceability

| ID | Business question | KPI(s) | Final module/page |
|---|---|---|---|
| REQ-01 | How is the enterprise performing now? | Revenue; EBITDA; EBITDA Margin; EBIT; NOPAT; FCF | Executive CFO Cockpit |
| REQ-02 | Which business units/regions are driving or dragging growth? | Revenue Growth %; Revenue | Performance Analysis |
| REQ-03 | Is the enterprise creating returns above its cost of capital? | ROIC; WACC; ROIC-WACC Spread; Economic Profit | Value Creation |
| REQ-04 | Why did ROIC improve or deteriorate? | EBITDA Margin; NOPAT; Net Working Capital; Invested Capital; ROIC | Value Creation |
| REQ-05 | Where are material plan misses occurring? | Revenue Budget Variance; EBITDA Budget Variance; FCF Budget Variance | Budget Variance Analysis |
| REQ-06 | What is likely to happen next? | Forecast Accuracy; Revenue/EBITDA/FCF forecasts | Forecast & Scenario Intelligence |
| REQ-07 | How does performance/value change under Bear, Base and Bull cases? | Enterprise Value; WACC; FCF; EBITDA | Forecast & Scenario Intelligence |
| REQ-08 | Which assumptions matter most to enterprise value? | Enterprise Value | Forecast & Scenario Intelligence |
| REQ-09 | Which proposed investments create the most value? | NPV; IRR; ROI; Payback Period | Capital Allocation Optimizer |
| REQ-10 | Which combination of projects should be funded within the available capital budget? | NPV; Capital Allocation Score | Capital Allocation Optimizer |
| REQ-11 | Which projects are attractive but need review due to risk/strategy trade-offs? | Capital Allocation Score; NPV; IRR | Capital Allocation Optimizer |
| REQ-12 | Is balance-sheet leverage becoming a concern? | Net Debt; Net Debt / EBITDA | Executive CFO Cockpit |
| REQ-13 | Where is cash being trapped in operations? | Net Working Capital; FCF | Value Creation / AI CFO |
| REQ-14 | What are the 5-10 issues/opportunities the CFO should act on first? | CFO Priority Score; Risk Severity + supporting KPIs | AI CFO Intelligence |
| REQ-15 | Can a recruiter/analyst trace dashboard numbers back to logic? | All KPIs | All modules |
| REQ-16 | Can the project run without proprietary company systems? | All | End-to-end pipeline |

---

## 8. Locked KPI catalog

Phase 1 contains **27 KPIs / decision metrics**. The Excel workbook contains the full definition, frequency, grain, source, implementation owner and interpretation rule.

| KPI ID | Category | KPI | Locked formula / definition | Unit |
|---|---|---|---|---|
| KPI-01 | Financial Performance | Revenue | SUM(revenue) | Currency |
| KPI-02 | Financial Performance | Revenue Growth % | (Current Revenue - Prior Comparable Revenue) / ABS(Prior Comparable Revenue) | % |
| KPI-03 | Financial Performance | EBITDA | Revenue - COGS - Operating Expenses excluding D&A | Currency |
| KPI-04 | Financial Performance | EBITDA Margin % | EBITDA / Revenue | % |
| KPI-05 | Financial Performance | EBIT | EBITDA - Depreciation & Amortization | Currency |
| KPI-06 | Financial Performance | NOPAT | EBIT * (1 - Effective Tax Rate) | Currency |
| KPI-07 | Financial Performance | Free Cash Flow | NOPAT + D&A - CAPEX - Change in Net Working Capital | Currency |
| KPI-08 | Value Creation | Invested Capital | Net Working Capital + Net Fixed Assets | Currency |
| KPI-09 | Value Creation | ROIC % | TTM NOPAT / Average Invested Capital | % |
| KPI-10 | Value Creation | WACC % | Scenario / market assumption supplied by period | % |
| KPI-11 | Value Creation | ROIC-WACC Spread (pp) | ROIC % - WACC % | Percentage points |
| KPI-12 | Value Creation | Economic Profit | NOPAT - (Average Invested Capital * WACC) | Currency |
| KPI-13 | Value Creation | Enterprise Value | PV(Forecast FCFs) + PV(Terminal Value); Terminal Value = FCF_n*(1+g)/(WACC-g) | Currency |
| KPI-14 | Capital Efficiency | Net Working Capital | Receivables + Inventory - Payables | Currency |
| KPI-15 | Capital Efficiency | Net Debt | Total Debt - Cash | Currency |
| KPI-16 | Capital Efficiency | Net Debt / EBITDA | Net Debt / TTM EBITDA | Multiple (x) |
| KPI-17 | Planning & Forecasting | Revenue Budget Variance % | (Actual Revenue - Budget Revenue) / ABS(Budget Revenue) | % |
| KPI-18 | Planning & Forecasting | EBITDA Budget Variance % | (Actual EBITDA - Budget EBITDA) / ABS(Budget EBITDA) | % |
| KPI-19 | Planning & Forecasting | FCF Budget Variance % | (Actual FCF - Budget FCF) / ABS(Budget FCF) | % |
| KPI-20 | Planning & Forecasting | Forecast Accuracy % | MAX(0, 100% - MAPE); MAPE = AVG(ABS((Actual-Forecast)/Actual)) | % |
| KPI-21 | Capital Allocation | NPV | SUM(CF_t / (1+WACC)^t) - Initial Investment | Currency |
| KPI-22 | Capital Allocation | IRR % | IRR(Project Cash Flow Series) | % |
| KPI-23 | Capital Allocation | ROI % | (Total Expected Inflows - Initial Investment) / Initial Investment | % |
| KPI-24 | Capital Allocation | Payback Period | First point where cumulative undiscounted cash flow >= Initial Investment, with fractional period interpolation | Years |
| KPI-25 | Capital Allocation | Capital Allocation Score | 35% NPV score + 20% IRR score + 10% ROI score + 10% Payback score + 15% Strategic Priority score + 10% Inverse Risk score | Score 0-100 |
| KPI-26 | AI CFO Intelligence | CFO Priority Score | 35% Value-Destruction Severity + 25% EBITDA Budget-Miss Severity + 20% FCF Deterioration Severity + 20% Forecast-Risk Severity | Score 0-100 |
| KPI-27 | AI CFO Intelligence | Risk Severity | Critical if priority>=80 or hard critical rule; High 60-79; Medium 40-59; Low <40 | Category |

---

## 9. Critical finance definitions

### 9.1 NOPAT
`NOPAT = EBIT × (1 - Effective Tax Rate)`

Purpose: isolate after-tax operating profit before financing effects.

### 9.2 Net Working Capital
`NWC = Receivables + Inventory - Payables`

Purpose: quantify operating cash tied up in the business.

### 9.3 Invested Capital
`Invested Capital = Net Working Capital + Net Fixed Assets`

This is the project's deliberately simplified **operating invested-capital** definition. It is chosen because it works cleanly at both enterprise and business-unit level.

### 9.4 ROIC
`ROIC = TTM NOPAT / Average Invested Capital`

Use average invested capital rather than a single ending balance.

### 9.5 ROIC-WACC Spread
`ROIC-WACC Spread = ROIC - WACC`

Locked interpretation:

- **Strong Creator:** >= +5.0 percentage points
- **Creator:** >= 0.0 and < +5.0 percentage points
- **Value Destroyer:** < 0.0 percentage points

### 9.6 Economic Profit
`Economic Profit = NOPAT - (Average Invested Capital × WACC)`

Positive = value created after the capital charge.  
Negative = value destroyed under the project definition.

### 9.7 Free Cash Flow
`FCF = NOPAT + D&A - CAPEX - Change in Net Working Capital`

### 9.8 Enterprise Value
Use a simplified DCF:

`EV = PV(Forecast FCFs) + PV(Terminal Value)`

`Terminal Value = FCF_n × (1 + g) / (WACC - g)`

Hard guardrail: **WACC must be greater than terminal growth in every scenario.**

---

## 10. Capital-allocation decision framework

NPV remains the primary economic measure.

### 10.1 Project decision metrics
- NPV
- IRR
- ROI
- Payback Period
- Strategic Priority
- Risk Score
- Capital Allocation Score

### 10.2 Locked 0–100 Capital Allocation Score
- NPV normalized score: **35%**
- IRR normalized score: **20%**
- ROI normalized score: **10%**
- Payback normalized score: **10%**
- Strategic Priority score: **15%**
- Inverse Risk score: **10%**

The score is a **ranking aid**, not a replacement for NPV.

### 10.3 Project recommendation logic

**Strong Invest**
- NPV > 0
- IRR >= WACC + 5 percentage points
- Capital Allocation Score >= 80
- Risk score not in the highest-risk category

**Invest**
- NPV > 0
- IRR > WACC
- Capital Allocation Score >= 65

**Review**
- Positive NPV but weaker score / elevated risk / marginal hurdle spread

**Reject**
- NPV <= 0, or project does not clear the WACC hurdle without a documented strategic exception

### 10.4 Portfolio recommendation
Phase 8 must recommend a set of projects that:

1. does not exceed available capital;
2. maximizes total positive NPV under that capital constraint;
3. exposes projects excluded because of capital scarcity;
4. explains the recommendation using NPV, hurdle rate, score, risk and strategic priority.

---

## 11. CFO alert framework

### 11.1 CFO Priority Score
A deterministic 0–100 score:

- Value-destruction severity: **35%**
- EBITDA budget-miss severity: **25%**
- FCF deterioration severity: **20%**
- Forecast-risk severity: **20%**

### 11.2 Risk Severity
- **Critical:** 80–100 or a hard critical rule
- **High:** 60–79
- **Medium:** 40–59
- **Low:** <40

### 11.3 Initial hard-rule thresholds
These are project decision rules, not universal corporate covenants:

- ROIC-WACC spread < 0pp → value-destruction alert
- Revenue budget variance <= -5% → warning; <= -10% → critical
- EBITDA budget variance <= -7.5% → warning; <= -15% → critical
- FCF budget variance <= -10% → warning; <= -20% → critical
- Forecast accuracy < 90% → watch; <80% → weak
- Net Debt / EBITDA > 3.0x → elevated leverage
- Project NPV <= 0 → reject-path alert
- Project IRR <= WACC → hurdle-rate alert

---

## 12. AI CFO design rule

The platform must remain fully usable without a paid external LLM.

The core AI CFO layer will combine:

1. validated financial KPIs;
2. forecasting;
3. anomaly / deterioration detection;
4. deterministic business rules;
5. CFO Priority Score;
6. project recommendation logic;
7. templated executive narratives that state the numbers, issue, likely driver and recommended action.

An external LLM can be added later only as an **optional narrative enhancement**. It must never be the source of truth for financial calculations.

This preserves reproducibility, auditability and GitHub usability.

---

## 13. Locked business rules

| Rule | Topic | Locked rule |
|---|---|---|
| BR-01 | Currency consistency | All enterprise financial amounts must use one reporting currency in the analytics layer. Raw synthetic data may include only that reporting currency to keep Phase 1-2 simple. |
| BR-02 | Sign convention | Revenue/profit/cash inflows are positive; costs, investment outflows and financing outflows follow explicitly documented sign conventions. Project cash-flow series starts with a negative initial investment. |
| BR-03 | Time grain | Core financial performance and budget data must support monthly analysis; quarterly, YTD, annual and TTM outputs are derived from monthly records. |
| BR-04 | Comparable growth | Monthly growth shown to executives should default to year-over-year comparison to reduce seasonality distortion. |
| BR-05 | NOPAT | NOPAT uses EBIT multiplied by (1 - effective tax rate). Financing costs do not enter NOPAT. |
| BR-06 | Invested capital | Use simplified operating invested capital = Net Working Capital + Net Fixed Assets. Use average invested capital for ROIC. |
| BR-07 | ROIC timing | ROIC should use TTM/annualized NOPAT divided by average invested capital, avoiding monthly profit divided by a balance-sheet snapshot. |
| BR-08 | WACC | WACC is an assumption by scenario/period. The project will not build a full beta/capital-markets WACC model in Phase 1-13. |
| BR-09 | DCF guardrail | Terminal growth must be lower than WACC in every scenario. DCF output is decision-support, not a fairness opinion or audited valuation. |
| BR-10 | Economic profit | Economic Profit = NOPAT - (Average Invested Capital × WACC). Positive values represent value creation under the project definition. |
| BR-11 | Budget variance | For revenue, EBITDA and FCF, variance = Actual - Budget; positive is favorable. Percentage variance uses absolute budget as denominator. |
| BR-12 | Forecast accuracy | Use MAPE-derived accuracy with safeguards for zero/near-zero actuals; cap reported accuracy between 0% and 100%. |
| BR-13 | Capital allocation hierarchy | NPV and economic value creation are primary. IRR, ROI, payback, strategic priority and risk are supporting metrics. |
| BR-14 | Project selection | Recommended portfolio must stay within available capital. Phase 8 should maximize total positive NPV under the capital limit, then explain trade-offs using the ranking score. |
| BR-15 | AI CFO design | The core AI CFO intelligence layer must work without a paid external LLM/API. It will combine forecasting/anomaly analytics, deterministic rules, priorities and generated executive narratives. Any LLM layer is optional. |
| BR-16 | Explainability | Every alert/recommendation must expose the KPI values and rules that triggered it. No opaque recommendation without supporting numbers. |
| BR-17 | Synthetic-data disclosure | All project data is synthetic and must be labelled as such in README, report and LinkedIn/GitHub materials. |
| BR-18 | McKinsey disclaimer | The project is an independent portfolio project inspired by public corporate-finance practices and is not affiliated with, endorsed by or commissioned by McKinsey & Company. |

---

## 14. Data requirements Phase 2 must satisfy

The six future datasets must collectively support:

1. stable primary keys and foreign keys;
2. monthly time series;
3. multiple business units and regions;
4. realistic revenue, cost, D&A, CAPEX and tax relationships;
5. balance-sheet components needed for NWC, invested capital, net debt and leverage;
6. actual and budget values at matching grains;
7. project-level investment amounts and multi-period cash flows;
8. WACC and scenario assumptions;
9. Bear / Base / Bull scenarios;
10. enough history for forecasting and back-testing;
11. intentional but limited data-quality issues for validation/cleaning;
12. deterministic relationships so finance formulas reconcile.

Recommended minimum analytical history for Phase 2: **at least 48 monthly periods**, plus current budget/forecast and a forward scenario horizon. Exact dates will be locked in Phase 2.

---

## 15. Non-functional requirements

### Explainability
Every KPI and CFO recommendation must be traceable to formula and input data.

### Reproducibility
The project must run from synthetic files without proprietary systems.

### Simplicity
No technology or model is added unless it improves a defined business requirement.

### Data quality
SQL/Python must detect nulls, duplicates, invalid dates, impossible financial values and broken key relationships.

### Consistency
The same KPI definition must be used in SQL, Python and Power BI.

### Performance
The synthetic dataset should remain lightweight enough for local MS SQL Server, VS Code and Power BI.

### Presentation quality
Dashboards must be executive-oriented: limited KPIs, clear hierarchy, strong business narrative and no clutter.

---

## 16. Phase-to-requirement ownership

| Future phase | Main responsibility |
|---|---|
| Phase 2 | Design six datasets that can calculate every Phase 1 KPI |
| Phase 3 | Generate realistic synthetic data that follows Phase 1 business rules |
| Phase 4 | Create MS SQL database, tables, constraints and load raw data |
| Phase 5 | Validate, clean and engineer finance-ready fields |
| Phase 6 | Implement SQL financial analytics and CFO views |
| Phase 7 | Build forecasting, accuracy and scenarios |
| Phase 8 | Calculate project economics and constrained capital allocation |
| Phase 9 | Generate explainable CFO priorities and executive narratives |
| Phase 10 | Visualize requirements in five Power BI pages |
| Phase 11 | Save portfolio-ready screenshots |
| Phase 12 | Document methodology, outcomes and GitHub project |
| Phase 13 | Convert project into LinkedIn and resume evidence |

---

## 17. Phase 1 acceptance criteria

Phase 1 is complete only if all of the following are true:

- [x] Project objective is defined.
- [x] Business problem is defined.
- [x] Stakeholders are identified.
- [x] In-scope and out-of-scope boundaries are locked.
- [x] Five analytical modules are defined.
- [x] Core business questions are mapped to outputs.
- [x] All KPI formulas are defined.
- [x] ROIC / invested-capital convention is locked.
- [x] WACC and DCF guardrails are locked.
- [x] Budget variance conventions are locked.
- [x] Capital-allocation hierarchy and score are locked.
- [x] Capital-budget constraint requirement is locked.
- [x] CFO priority and severity logic are locked.
- [x] AI CFO explainability / no-mandatory-API rule is locked.
- [x] Phase 2 data requirements are defined.
- [x] Synthetic-data and McKinsey disclaimers are defined.
- [x] KPI catalog is implementation-ready for SQL/Python/Power BI.

**Phase 1 decision:** COMPLETE. Proceed to Phase 2 — Dataset Design.

---

## 18. Public design references

These sources support the high-level project design; the exact formulas, scoring weights and alert thresholds above are project-specific implementation choices.

| Source | Relevance | URL |
|---|---|---|
| McKinsey - What matters most to investors in 2026 | ROIC discipline and clear capital-allocation frameworks remain central investor expectations. | https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/what-matters-most-to-investors-in-2026-and-what-it-means-for-companies |
| McKinsey - Selecting P&L-linked KPIs with a ROIC driver tree | Supports ROIC as a value-steering metric and decomposition into profitability and capital efficiency. | https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/selecting-p-and-l-linked-kpis-for-industrial-transformations |
| McKinsey - How AI agents can help FP&A better steer the business | Supports continuous forecasting, earlier risk detection, scenario evaluation and finance decision support. | https://www.mckinsey.com/capabilities/operations/our-insights/how-ai-agents-can-help-fp-and-a-better-steer-the-business |
| McKinsey - CFO and Finance Excellence | Supports the project themes of enterprise value, capital allocation, performance steering and AI-enabled finance. | https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/how-we-help-clients/cfo-and-finance-excellence |
| McKinsey - A guide to Gen AI for CFOs | Supports prioritizing the largest value-creating opportunities while preserving foundational finance discipline. | https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/gen-ai-a-guide-for-cfos |

---

## 19. Portfolio disclaimer

This is an **independent synthetic portfolio project** created for learning and demonstration. It is not affiliated with, endorsed by, commissioned by, or representative of confidential work performed by McKinsey & Company. All enterprise data used in the project will be synthetic.
