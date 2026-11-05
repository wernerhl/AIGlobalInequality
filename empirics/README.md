# Empirical pipeline: AI return shocks and the cost of capital for the poor

Implements the measurement strategy of Section IV of the paper with free data.

## Run

```
pip install pandas numpy requests yfinance statsmodels matplotlib tabulate
python fetch_edgar.py     # SEC XBRL financials + 8-K earnings-release dates (cached in data/raw/edgar)
python fetch_prices.py    # Yahoo daily prices + earnings dates / EPS surprises
python fetch_macro.py     # FRED rates, VIX, dollar, ICE BofA EM spreads; Ken French factors
python fetch_finance.py   # OECD ODA/mobilisation, World Bank flows, BIS bank flows & bond issuance, BEA/Census US investment
python build_shocks.py    # event list, abnormal returns, capex surprises, supplier-implied capex shock, daily AI factor
python analysis.py        # price tests: EM spreads/ETFs on AI shocks -> output/results.md
python analysis_flows.py  # quantity tests: who raises money and where it goes -> output/results_flows.md
```

`data/raw/` is not committed (32 MB, re-downloadable). `data/processed/` and `output/` are.

## Data

| File | Source | Content |
|---|---|---|
| `data/processed/edgar_quarterly.csv` | SEC `companyfacts` API | Quarterly capex, revenue, operating income, net income, cash from operations, depreciation, assets, net PP&E for MSFT, GOOGL, AMZN, META, ORCL, NVDA, AVGO, AMD. Year-to-date 10-Q flows are de-cumulated to quarters. |
| `data/processed/edgar_8k_earnings.csv` | SEC `submissions` API | Filing dates of 8-Ks with item 2.02 (results of operations). |
| `data/processed/prices_adjclose.csv`, `returns_daily.csv` | Yahoo Finance | Daily adjusted closes since 2018 for the AI firms, a supply-chain basket (TSM, VRT, ANET, SMCI, MU, ASML), SPY/QQQ, and EM proxies: EMB, PCY (USD sovereign), EMHY, EMLC (local currency), EEM (equity), IEF (Treasury control). |
| `data/processed/yahoo_earnings_dates.csv` | Yahoo Finance | Announcement timestamps, consensus EPS, reported EPS, surprise. |
| `data/processed/fred_daily.csv` | FRED | DGS2, DGS10, DFII10, T10YIE, VIXCLS, DTWEXBGS, SOFR, WTI; ICE BofA EM OAS by issuer type, rating and region, plus US HY/IG OAS as placebos. ICE BofA series are only available from Nov 2023 on FRED. |
| `data/processed/ff_factors_daily.csv` | Ken French | FF5 + momentum, daily (published with a lag of one to two months). |
| `data/processed/oecd_dac1_by_donor.csv` | OECD DAC1 (SDMX) | ODA net disbursements and grant equivalents, bilateral/multilateral, private flows, GNI, by donor, 2018-2025 (2025 preliminary), current and constant prices. |
| `data/processed/oecd_dac5_sector.csv` | OECD DAC5 | Bilateral ODA commitments by purpose sector and donor, 2018-2024. |
| `data/processed/oecd_mobilisation.csv` | OECD | Private finance mobilised by official development finance interventions, by recipient, sector and leveraging mechanism, 2012-2024. |
| `data/processed/wb_flows.csv` | World Bank WDI + IDS | Net ODA received, FDI, portfolio equity, remittances, capital formation, and external-debt flows by creditor type (official, multilateral, bilateral, private, bonds) for low-income, lower-middle-income and other aggregates. |
| `data/processed/bis_lbs_quarterly.csv` | BIS locational banking | Cross-border bank claims on EMDEs (total and by region, all sectors / governments / non-banks): FX- and break-adjusted quarterly flows and stocks, 2010-2026Q2. |
| `data/processed/bis_ids_quarterly.csv` | BIS international debt securities | Gross issues, net issues and amounts outstanding of bonds issued in international markets by residents of EMDEs (all issuers, general government, nonfinancial corporates), by international organisations (IFIs / supranationals), by the US, and world totals, quarterly 2010-2026Q2. |
| `data/processed/fred_us_investment.csv` | FRED (BEA, Fed Z.1, Census) | US private nonresidential fixed investment and components (structures, equipment, info-processing equipment, IPP, R&D), C&I loans, nonfinancial corporate debt securities, construction spending aggregates, core capital goods orders. |
| `data/processed/census_construction_monthly.csv` | Census C30 | Private construction spending by category, monthly, including the data-center line. |
| `data/processed/edgar_quarterly.csv` (extended) | SEC | Now also long-term debt issued/repaid, commercial paper, buybacks, dividends, long-term debt and cash for the AI firms. |

## Constructed series

- `events.csv`: 133 earnings releases by the 8 AI firms, Oct 2022 - Nov 2026. For each: reaction day (first session after the release), two-day cumulative abnormal return from an FF5+Mom model estimated over days [-250, -21] (market model on SPY when factors are not yet published), EPS surprise, and the capex surprise of the quarter being reported. 92% of events match an 8-K item 2.02 filing within three days.
- Capex surprise: realized quarterly capex minus a seasonal random walk with drift (capex four quarters earlier plus the mean year-on-year change over the previous four quarters), scaled by lagged assets. One standard deviation is about 1% of assets for the hyperscalers. This substitutes for consensus capex forecasts (I/B/E/S or Visible Alpha), which are not free; with those, the surprise should be guidance minus consensus at the announcement.
- Supplier-implied capex shock: on each hyperscaler announcement day, the two-day abnormal return of the AI supply-chain basket (NVDA, AVGO, AMD, TSM, VRT, ANET, SMCI, MU, ASML; suppliers reporting the same day excluded). Hyperscaler capex guidance moves the suppliers' expected revenues, so this is a forward-looking, market-based proxy for the capex-guidance surprise that consensus data would measure directly. It is essentially uncorrelated with the realized capex surprise (correlation -0.08), which says the realized surprise is not what the market treats as capex news.
- `shocks_daily.csv`: daily series of (i) the mean two-day CAR of the AI firms reporting that day, (ii) the same for hyperscalers only, (iii) the mean capex surprise of reporting firms, (iv) the supplier-implied capex shock, (v) the AI basket return minus SPY and (vi) its residual from the FF5+Mom model.
- `capex_quarterly_with_surprises.csv`: quarterly panel with surprises, YoY growth, capex/CFO and capex/depreciation.

## First-pass results (`output/results.md`)

Hyperscaler capex on a trailing-four-quarter basis rose from USD 154 bn (2023Q4) to USD 691 bn (2026Q3).

Event-day regressions of EM outcomes on the AI shocks, with controls for the 2y Treasury, VIX, the dollar, SPY and IEF:

- Stock-price shocks (two-day abnormal returns of reporting firms) show no EM spread widening. If anything, hyperscaler earnings surprises are associated with slightly tighter EM public-sector spreads (-9 bp per unit CAR, i.e. about -0.9 bp for a 10% abnormal return, t = -2.1, n = 44).
- Capex surprises go the direction the crowding-out model predicts: a one-standard-deviation positive surprise is associated with lower EM bond ETF prices (EMLC -0.09%, t = -2.6; EMHY -0.08%, t = -1.9), lower EM equity, and a wider EM public-sector spread (+0.7 bp, t = 1.8). The effects are economically small, and US high-yield spreads widen too, so the response is a general rise in required returns rather than something specific to emerging markets. In the model that is what a higher common hurdle rate looks like, but it means the test cannot yet separate the crowding-out channel from generic risk-premium news.
- On all trading days, the daily AI factor co-moves positively with EM assets (risk-on), and the co-movement disappears once SPY and the other controls are included.

## Quantities (`output/results_flows.md`)

Pre = 2019Q1-2022Q3 average vs post = 2023Q1-latest average, quarterly USD bn.

- Bond markets. IFIs / supranationals raised 44% more gross (USD 129 bn to 186 bn per quarter) and 73% more net after the AI boom began; their share of world international issuance rose from about 7-8% to 9%. EMDE residents' gross issuance rose 26% and governments' 27%, but EMDE nonfinancial corporates' net issuance fell 58% and Africa & Middle East governments' net issuance fell 16%. The hyperscalers moved from funding capex out of cash flow to issuing USD 45-80 bn of long-term debt per quarter from 2025Q4 while cutting buybacks from about USD 30 bn to 5 bn per quarter; their 2026 year-to-date debt issuance (USD 143 bn) is of the same order as the IFIs' (USD 504 bn) and EMDE governments' (USD 218 bn).
- Development finance. DAC net ODA fell from USD 212 bn (2024) to 163 bn (2025) in constant prices, -23%, with the US accounting for USD 37 bn of the 49 bn decline; ex-US ODA fell 8%. Sector commitments 2022-2024 fell most in health (-44%), water (-31%), energy (-24%) and humanitarian aid (-19%) and rose in education (+9%) and environment (+9%), so the capital-intensity composition is mixed. Mobilised private finance kept rising to USD 297 bn in 2024, concentrated in banking/financial services and energy. Cross-border bank flows to EMDEs are far higher post-2023 (USD 66 bn vs 9 bn per quarter), but so are flows to the US (237 bn vs 104 bn).
- United States. Data-center construction rose 330% (USD 2.5 bn to 10.6 bn per quarter) against 45% for other nonresidential construction; hyperscaler capex is now about 15% of US private nonresidential fixed investment, and investment net of hyperscaler capex still grew 31%.
- Quarterly regressions (n = 33-34) of EMDE and IFI financing quantities on the quarterly AI factor give positive, not negative, coefficients: quarters with high AI abnormal returns are quarters in which IFIs and EMDE sovereigns issue more. At quarterly frequency the risk-on co-movement dominates any crowding-out, so the quantity test needs either longer samples or the cross-sectional (donor exposure, sector capital intensity) designs.

Caveats: the shocks mix capex and earnings news within the same announcement; the capex surprise is realized capex, not guidance; the ICE BofA sample is short; ETF returns embed duration and liquidity. Remaining gaps: consensus capex guidance (I/B/E/S or Visible Alpha) to replace the supplier-implied proxy, sovereign-level spreads for low-income countries (frontier sub-indices), a Campbell-Shiller split of AI returns into cash-flow and discount-rate news, donor-level AI exposure for the cross-section in `output/donor_cross_section_2025.csv`, and IFI-level (IBRD, IDA, IFC, AfDB, AsDB, IDB, EIB) issuance, which BIS only publishes as a supranational aggregate.
