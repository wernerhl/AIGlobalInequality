# Empirical pipeline: AI return shocks and the cost of capital for the poor

Implements the measurement strategy of Section IV of the paper with free data.

## Run

```
pip install pandas numpy requests yfinance statsmodels matplotlib tabulate
python fetch_edgar.py     # SEC XBRL financials + 8-K earnings-release dates (cached in data/raw/edgar)
python fetch_prices.py    # Yahoo daily prices + earnings dates / EPS surprises
python fetch_macro.py     # FRED rates, VIX, dollar, ICE BofA EM spreads; Ken French factors
python build_shocks.py    # event list, abnormal returns, capex surprises, daily AI factor
python analysis.py        # regressions and figures -> output/
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

## Constructed series

- `events.csv`: 133 earnings releases by the 8 AI firms, Oct 2022 - Nov 2026. For each: reaction day (first session after the release), two-day cumulative abnormal return from an FF5+Mom model estimated over days [-250, -21] (market model on SPY when factors are not yet published), EPS surprise, and the capex surprise of the quarter being reported. 92% of events match an 8-K item 2.02 filing within three days.
- Capex surprise: realized quarterly capex minus a seasonal random walk with drift (capex four quarters earlier plus the mean year-on-year change over the previous four quarters), scaled by lagged assets. One standard deviation is about 1% of assets for the hyperscalers. This substitutes for consensus capex forecasts (I/B/E/S or Visible Alpha), which are not free; with those, the surprise should be guidance minus consensus at the announcement.
- `shocks_daily.csv`: daily series of (i) the mean two-day CAR of the AI firms reporting that day, (ii) the same for hyperscalers only, (iii) the mean capex surprise of reporting firms, (iv) the AI basket return minus SPY and (v) its residual from the FF5+Mom model.
- `capex_quarterly_with_surprises.csv`: quarterly panel with surprises, YoY growth, capex/CFO and capex/depreciation.

## First-pass results (`output/results.md`)

Hyperscaler capex on a trailing-four-quarter basis rose from USD 154 bn (2023Q4) to USD 691 bn (2026Q3).

Event-day regressions of EM outcomes on the AI shocks, with controls for the 2y Treasury, VIX, the dollar, SPY and IEF:

- Stock-price shocks (two-day abnormal returns of reporting firms) show no EM spread widening. If anything, hyperscaler earnings surprises are associated with slightly tighter EM public-sector spreads (-9 bp per unit CAR, i.e. about -0.9 bp for a 10% abnormal return, t = -2.1, n = 44).
- Capex surprises go the direction the crowding-out model predicts: a one-standard-deviation positive surprise is associated with lower EM bond ETF prices (EMLC -0.09%, t = -2.6; EMHY -0.08%, t = -1.9), lower EM equity, and a wider EM public-sector spread (+0.7 bp, t = 1.8). The effects are economically small, and US high-yield spreads widen too, so the response is a general rise in required returns rather than something specific to emerging markets. In the model that is what a higher common hurdle rate looks like, but it means the test cannot yet separate the crowding-out channel from generic risk-premium news.
- On all trading days, the daily AI factor co-moves positively with EM assets (risk-on), and the co-movement disappears once SPY and the other controls are included.

Caveats: the shocks mix capex and earnings news within the same announcement; the capex surprise is realized capex, not guidance; the ICE BofA sample is short; ETF returns embed duration and liquidity. The next steps that would sharpen the test are consensus capex guidance (to isolate the forward-looking capex surprise), sovereign-level spread data for low-income countries (frontier sub-indices), and a Campbell-Shiller split of the AI returns into cash-flow and discount-rate news.
