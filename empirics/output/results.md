# First-pass results: AI return shocks and EM cost of capital

Events: 133 earnings releases by 8 AI firms, 2022-10-26 to 2026-11-04, on 107 distinct reaction days.

Shock units: `ai_earnings_shock` and `hyperscaler_earnings_shock` are mean two-day abnormal returns (decimal) of the firms reporting that day; `capex_surprise_assets` is the capex surprise scaled by lagged assets (decimal); `ai_ff_resid` is the daily AI-basket residual from the FF5+Mom model (decimal); `ai_minus_mkt` is the basket return minus SPY. Outcomes are in percent (ETF returns) or basis points (OAS). A coefficient of 0.05 on an ETF-return outcome means a 10% AI abnormal return moves the ETF by 0.5%. HAC standard errors.

Prediction of the crowding-out model: positive AI shocks lower EM bond ETF prices (negative coefficient) and raise EM spreads (positive coefficient), beyond what US rates, VIX, the dollar and the market explain. The AI-for-development view predicts the opposite signs; donor politics predicts zero.

## A. Event days (two-day windows around AI earnings releases)

| outcome                                 | shock                      | controls   | coef (se)         |     t |     p |   n |    r2 |
|:----------------------------------------|:---------------------------|:-----------|:------------------|------:|------:|----:|------:|
| EM USD sovereign bond ETF return (%)    | ai_earnings_shock          | no         | 0.095 (0.724)     |  0.13 | 0.896 | 106 | 0     |
| EM USD sovereign bond ETF return (%)    | ai_earnings_shock          | yes        | -0.096 (0.419)    | -0.23 | 0.82  | 106 | 0.816 |
| EM sovereign debt ETF return (%)        | ai_earnings_shock          | no         | 0.033 (1.008)     |  0.03 | 0.974 | 106 | 0     |
| EM sovereign debt ETF return (%)        | ai_earnings_shock          | yes        | -0.318 (0.602)    | -0.53 | 0.598 | 106 | 0.776 |
| EM high-yield bond ETF return (%)       | ai_earnings_shock          | no         | 0.283 (0.614)     |  0.46 | 0.645 | 106 | 0.002 |
| EM high-yield bond ETF return (%)       | ai_earnings_shock          | yes        | -0.115 (0.482)    | -0.24 | 0.812 | 106 | 0.63  |
| EM local-currency bond ETF return (%)   | ai_earnings_shock          | no         | -0.224 (0.745)    | -0.3  | 0.763 | 106 | 0.001 |
| EM local-currency bond ETF return (%)   | ai_earnings_shock          | yes        | -0.230 (0.367)    | -0.63 | 0.531 | 106 | 0.8   |
| EM equity ETF return (%)                | ai_earnings_shock          | no         | 2.763 (1.975)     |  1.4  | 0.162 | 106 | 0.018 |
| EM equity ETF return (%)                | ai_earnings_shock          | yes        | 2.335 (1.385)     |  1.69 | 0.092 | 106 | 0.725 |
| EM public-sector OAS change (bp)        | ai_earnings_shock          | no         | -5.283 (5.430)    | -0.97 | 0.331 |  74 | 0.01  |
| EM public-sector OAS change (bp)        | ai_earnings_shock          | yes        | 0.357 (3.544)     |  0.1  | 0.92  |  74 | 0.785 |
| EM corporate plus USD OAS change (bp)   | ai_earnings_shock          | no         | -6.272 (6.033)    | -1.04 | 0.299 |  74 | 0.011 |
| EM corporate plus USD OAS change (bp)   | ai_earnings_shock          | yes        | 0.502 (4.392)     |  0.11 | 0.909 |  74 | 0.799 |
| EM high-yield USD OAS change (bp)       | ai_earnings_shock          | no         | -11.093 (10.811)  | -1.03 | 0.305 |  74 | 0.01  |
| EM high-yield USD OAS change (bp)       | ai_earnings_shock          | yes        | 4.191 (9.083)     |  0.46 | 0.645 |  74 | 0.73  |
| US high-yield OAS (placebo) change (bp) | ai_earnings_shock          | no         | 3.344 (10.504)    |  0.32 | 0.75  |  74 | 0.001 |
| US high-yield OAS (placebo) change (bp) | ai_earnings_shock          | yes        | 24.091 (9.004)    |  2.68 | 0.007 |  74 | 0.753 |
| EM USD sovereign bond ETF return (%)    | hyperscaler_earnings_shock | no         | -0.728 (0.990)    | -0.73 | 0.462 |  63 | 0.008 |
| EM USD sovereign bond ETF return (%)    | hyperscaler_earnings_shock | yes        | 0.221 (0.405)     |  0.55 | 0.585 |  63 | 0.85  |
| EM sovereign debt ETF return (%)        | hyperscaler_earnings_shock | no         | -1.337 (1.469)    | -0.91 | 0.363 |  63 | 0.017 |
| EM sovereign debt ETF return (%)        | hyperscaler_earnings_shock | yes        | -0.138 (0.736)    | -0.19 | 0.851 |  63 | 0.8   |
| EM high-yield bond ETF return (%)       | hyperscaler_earnings_shock | no         | -0.283 (0.904)    | -0.31 | 0.754 |  63 | 0.002 |
| EM high-yield bond ETF return (%)       | hyperscaler_earnings_shock | yes        | 0.249 (0.543)     |  0.46 | 0.646 |  63 | 0.653 |
| EM local-currency bond ETF return (%)   | hyperscaler_earnings_shock | no         | -0.552 (1.136)    | -0.49 | 0.627 |  63 | 0.004 |
| EM local-currency bond ETF return (%)   | hyperscaler_earnings_shock | yes        | -0.044 (0.506)    | -0.09 | 0.931 |  63 | 0.781 |
| EM equity ETF return (%)                | hyperscaler_earnings_shock | no         | 1.088 (2.694)     |  0.4  | 0.686 |  63 | 0.003 |
| EM equity ETF return (%)                | hyperscaler_earnings_shock | yes        | 1.500 (1.663)     |  0.9  | 0.367 |  63 | 0.767 |
| EM public-sector OAS change (bp)        | hyperscaler_earnings_shock | no         | -15.417 (9.027)   | -1.71 | 0.088 |  44 | 0.063 |
| EM public-sector OAS change (bp)        | hyperscaler_earnings_shock | yes        | -8.898 (4.289)    | -2.07 | 0.038 |  44 | 0.835 |
| EM corporate plus USD OAS change (bp)   | hyperscaler_earnings_shock | no         | -18.096 (10.134)  | -1.79 | 0.074 |  44 | 0.064 |
| EM corporate plus USD OAS change (bp)   | hyperscaler_earnings_shock | yes        | -10.143 (5.459)   | -1.86 | 0.063 |  44 | 0.849 |
| EM high-yield USD OAS change (bp)       | hyperscaler_earnings_shock | no         | -28.038 (18.577)  | -1.51 | 0.131 |  44 | 0.044 |
| EM high-yield USD OAS change (bp)       | hyperscaler_earnings_shock | yes        | -13.512 (12.192)  | -1.11 | 0.268 |  44 | 0.762 |
| US high-yield OAS (placebo) change (bp) | hyperscaler_earnings_shock | no         | -6.581 (18.218)   | -0.36 | 0.718 |  44 | 0.002 |
| US high-yield OAS (placebo) change (bp) | hyperscaler_earnings_shock | yes        | 21.289 (14.282)   |  1.49 | 0.136 |  44 | 0.793 |
| EM USD sovereign bond ETF return (%)    | capex_surprise_assets      | no         | -8.414 (6.135)    | -1.37 | 0.17  |  97 | 0.012 |
| EM USD sovereign bond ETF return (%)    | capex_surprise_assets      | yes        | -4.298 (3.066)    | -1.4  | 0.161 |  97 | 0.848 |
| EM sovereign debt ETF return (%)        | capex_surprise_assets      | no         | -8.637 (7.816)    | -1.11 | 0.269 |  97 | 0.008 |
| EM sovereign debt ETF return (%)        | capex_surprise_assets      | yes        | -3.535 (4.733)    | -0.75 | 0.455 |  97 | 0.807 |
| EM high-yield bond ETF return (%)       | capex_surprise_assets      | no         | -12.392 (5.604)   | -2.21 | 0.027 |  97 | 0.038 |
| EM high-yield bond ETF return (%)       | capex_surprise_assets      | yes        | -7.649 (3.981)    | -1.92 | 0.055 |  97 | 0.681 |
| EM local-currency bond ETF return (%)   | capex_surprise_assets      | no         | -13.148 (6.891)   | -1.91 | 0.056 |  97 | 0.027 |
| EM local-currency bond ETF return (%)   | capex_surprise_assets      | yes        | -8.609 (3.306)    | -2.6  | 0.009 |  97 | 0.819 |
| EM equity ETF return (%)                | capex_surprise_assets      | no         | -35.474 (14.265)  | -2.49 | 0.013 |  97 | 0.033 |
| EM equity ETF return (%)                | capex_surprise_assets      | yes        | -15.462 (7.382)   | -2.09 | 0.036 |  97 | 0.72  |
| EM public-sector OAS change (bp)        | capex_surprise_assets      | no         | 26.054 (72.106)   |  0.36 | 0.718 |  69 | 0.002 |
| EM public-sector OAS change (bp)        | capex_surprise_assets      | yes        | 66.998 (37.952)   |  1.77 | 0.078 |  69 | 0.8   |
| EM corporate plus USD OAS change (bp)   | capex_surprise_assets      | no         | 12.407 (75.695)   |  0.16 | 0.87  |  69 | 0     |
| EM corporate plus USD OAS change (bp)   | capex_surprise_assets      | yes        | 43.260 (38.888)   |  1.11 | 0.266 |  69 | 0.807 |
| EM high-yield USD OAS change (bp)       | capex_surprise_assets      | no         | 46.687 (115.825)  |  0.4  | 0.687 |  69 | 0.002 |
| EM high-yield USD OAS change (bp)       | capex_surprise_assets      | yes        | 56.753 (55.731)   |  1.02 | 0.309 |  69 | 0.728 |
| US high-yield OAS (placebo) change (bp) | capex_surprise_assets      | no         | 183.553 (115.122) |  1.59 | 0.111 |  69 | 0.022 |
| US high-yield OAS (placebo) change (bp) | capex_surprise_assets      | yes        | 148.723 (63.377)  |  2.35 | 0.019 |  69 | 0.729 |

## B. All trading days since October 2022 (daily AI factor)

| outcome                                 | shock        | controls   | coef (se)         |     t |     p |    n |    r2 |
|:----------------------------------------|:-------------|:-----------|:------------------|------:|------:|-----:|------:|
| EM USD sovereign bond ETF return (%)    | ai_ff_resid  | no         | 4.122 (1.647)     |  2.5  | 0.012 | 1002 | 0.007 |
| EM USD sovereign bond ETF return (%)    | ai_ff_resid  | yes        | -0.138 (0.926)    | -0.15 | 0.881 | 1002 | 0.791 |
| EM sovereign debt ETF return (%)        | ai_ff_resid  | no         | 5.795 (2.243)     |  2.58 | 0.01  | 1002 | 0.007 |
| EM sovereign debt ETF return (%)        | ai_ff_resid  | yes        | -0.420 (1.365)    | -0.31 | 0.758 | 1002 | 0.752 |
| EM high-yield bond ETF return (%)       | ai_ff_resid  | no         | 5.489 (1.544)     |  3.56 | 0     | 1002 | 0.014 |
| EM high-yield bond ETF return (%)       | ai_ff_resid  | yes        | -0.111 (0.957)    | -0.12 | 0.908 | 1002 | 0.688 |
| EM local-currency bond ETF return (%)   | ai_ff_resid  | no         | 5.260 (1.607)     |  3.27 | 0.001 | 1002 | 0.012 |
| EM local-currency bond ETF return (%)   | ai_ff_resid  | yes        | 0.726 (0.851)     |  0.85 | 0.394 | 1002 | 0.727 |
| EM equity ETF return (%)                | ai_ff_resid  | no         | 42.272 (4.551)    |  9.29 | 0     | 1002 | 0.137 |
| EM equity ETF return (%)                | ai_ff_resid  | yes        | 24.608 (3.524)    |  6.98 | 0     | 1002 | 0.608 |
| EM public-sector OAS change (bp)        | ai_ff_resid  | no         | -39.275 (10.263)  | -3.83 | 0     |  726 | 0.019 |
| EM public-sector OAS change (bp)        | ai_ff_resid  | yes        | -4.600 (8.453)    | -0.54 | 0.586 |  726 | 0.545 |
| EM corporate plus USD OAS change (bp)   | ai_ff_resid  | no         | -43.761 (12.078)  | -3.62 | 0     |  726 | 0.02  |
| EM corporate plus USD OAS change (bp)   | ai_ff_resid  | yes        | -2.828 (10.319)   | -0.27 | 0.784 |  726 | 0.528 |
| EM high-yield USD OAS change (bp)       | ai_ff_resid  | no         | -82.497 (23.237)  | -3.55 | 0     |  726 | 0.024 |
| EM high-yield USD OAS change (bp)       | ai_ff_resid  | yes        | -4.167 (22.605)   | -0.18 | 0.854 |  726 | 0.372 |
| US high-yield OAS (placebo) change (bp) | ai_ff_resid  | no         | -133.575 (23.513) | -5.68 | 0     |  726 | 0.046 |
| US high-yield OAS (placebo) change (bp) | ai_ff_resid  | yes        | 19.664 (18.511)   |  1.06 | 0.288 |  726 | 0.522 |
| EM USD sovereign bond ETF return (%)    | ai_minus_mkt | no         | 8.666 (1.469)     |  5.9  | 0     | 1027 | 0.052 |
| EM USD sovereign bond ETF return (%)    | ai_minus_mkt | yes        | -0.616 (0.713)    | -0.86 | 0.388 | 1027 | 0.791 |
| EM sovereign debt ETF return (%)        | ai_minus_mkt | no         | 11.522 (2.053)    |  5.61 | 0     | 1027 | 0.05  |
| EM sovereign debt ETF return (%)        | ai_minus_mkt | yes        | -1.598 (1.062)    | -1.5  | 0.132 | 1027 | 0.752 |
| EM high-yield bond ETF return (%)       | ai_minus_mkt | no         | 9.807 (1.365)     |  7.18 | 0     | 1027 | 0.08  |
| EM high-yield bond ETF return (%)       | ai_minus_mkt | yes        | -0.663 (0.753)    | -0.88 | 0.378 | 1027 | 0.686 |
| EM local-currency bond ETF return (%)   | ai_minus_mkt | no         | 8.001 (1.240)     |  6.45 | 0     | 1027 | 0.051 |
| EM local-currency bond ETF return (%)   | ai_minus_mkt | yes        | 0.228 (0.740)     |  0.31 | 0.758 | 1027 | 0.724 |
| EM equity ETF return (%)                | ai_minus_mkt | no         | 46.283 (3.470)    | 13.34 | 0     | 1027 | 0.291 |
| EM equity ETF return (%)                | ai_minus_mkt | yes        | 22.382 (2.942)    |  7.61 | 0     | 1027 | 0.612 |
| EM public-sector OAS change (bp)        | ai_minus_mkt | no         | -34.144 (8.436)   | -4.05 | 0     |  751 | 0.025 |
| EM public-sector OAS change (bp)        | ai_minus_mkt | yes        | -6.860 (8.858)    | -0.77 | 0.439 |  751 | 0.549 |
| EM corporate plus USD OAS change (bp)   | ai_minus_mkt | no         | -41.672 (9.754)   | -4.27 | 0     |  751 | 0.032 |
| EM corporate plus USD OAS change (bp)   | ai_minus_mkt | yes        | -7.006 (10.853)   | -0.65 | 0.519 |  751 | 0.536 |
| EM high-yield USD OAS change (bp)       | ai_minus_mkt | no         | -89.509 (17.676)  | -5.06 | 0     |  751 | 0.05  |
| EM high-yield USD OAS change (bp)       | ai_minus_mkt | yes        | -12.110 (22.467)  | -0.54 | 0.59  |  751 | 0.382 |
| US high-yield OAS (placebo) change (bp) | ai_minus_mkt | no         | -171.028 (20.781) | -8.23 | 0     |  751 | 0.134 |
| US high-yield OAS (placebo) change (bp) | ai_minus_mkt | yes        | 9.053 (20.177)    |  0.45 | 0.654 |  751 | 0.526 |

## Hyperscaler capex (USD bn, trailing four quarters)

| cq     |   capex_ttm_bn |
|:-------|---------------:|
| 2023Q4 |          154.2 |
| 2024Q1 |          163.6 |
| 2024Q2 |          183.9 |
| 2024Q3 |          206.8 |
| 2024Q4 |          239.1 |
| 2025Q1 |          270.9 |
| 2025Q2 |          312.6 |
| 2025Q3 |          357.2 |
| 2025Q4 |          411.5 |
| 2026Q1 |          482.1 |
| 2026Q2 |          566.4 |
| 2026Q3 |          691   |

Figures: `fig_capex.png`, `fig_ai_factor_vs_em.png`.