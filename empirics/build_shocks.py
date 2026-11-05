"""Construct AI return shocks from stock prices and earnings data.

Three measures, as described in Section IV of the paper:

1. Earnings-announcement shocks (data/processed/events.csv): for each AI firm and
   earnings release since 2022Q4, the cumulative abnormal return over the two trading
   days [0, +1] starting with the first session that can react to the release
   (releases come after the close), using a Fama-French 5-factor + momentum model
   estimated over trading days [-250, -21]. The same table carries the EPS surprise
   from Yahoo and the capex surprise from EDGAR.

2. Capex surprises: realized quarterly capex minus a seasonal-random-walk-with-drift
   forecast (capex four quarters earlier plus the mean year-on-year change over the
   previous four quarters), scaled by lagged total assets. This is the SUE analogue for
   capital expenditure and substitutes for consensus capex forecasts, which are not
   freely available.

3. Daily AI factor (data/processed/ai_factor_daily.csv): equal-weighted return of an
   AI basket (hyperscalers, chip suppliers, data-centre supply chain) in excess of the
   market, and its residual from a regression on the Fama-French factors.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import AI_FIRMS, AI_SUPPLY_CHAIN_EXTRA, OUT, PROC

EVENT_START = "2022-10-01"   # first earnings season after ChatGPT (30 Nov 2022) is 2023Q1;
                             # start one season earlier for a pre-period.
EST_WINDOW = (-250, -21)
EVENT_WINDOW = (0, 1)


def load():
    ret = pd.read_csv(PROC / "returns_daily.csv", index_col=0, parse_dates=True)
    ff = pd.read_csv(PROC / "ff_factors_daily.csv", index_col=0, parse_dates=True)
    q = pd.read_csv(PROC / "edgar_quarterly.csv", parse_dates=["period_end"])
    e = pd.read_csv(PROC / "yahoo_earnings_dates.csv")
    e["earnings_date"] = pd.to_datetime(e["earnings_date"], utc=True).dt.tz_convert("America/New_York")
    k8 = pd.read_csv(PROC / "edgar_8k_earnings.csv", parse_dates=["filingDate"])
    return ret, ff, q, e, k8


def reaction_day(ts, trading_days):
    """First trading session whose close can reflect a release at timestamp ts."""
    d = pd.Timestamp(ts.date())
    if ts.hour >= 16 or (ts.hour == 15 and ts.minute >= 55):
        pos = trading_days.searchsorted(d, side="right")
    else:
        pos = trading_days.searchsorted(d, side="left")
    return trading_days[min(pos, len(trading_days) - 1)]


def abnormal_returns(ret, ff, ticker, day):
    """CAR over EVENT_WINDOW and the two daily abnormal returns, FF5+Mom model."""
    r = ret[ticker].dropna()
    days = r.index
    i = days.get_loc(day)
    est = r.iloc[i + EST_WINDOW[0]: i + EST_WINDOW[1] + 1]
    ev = r.iloc[i + EVENT_WINDOW[0]: i + EVENT_WINDOW[1] + 1]
    fcols = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]
    X = ff.reindex(est.index)[fcols]
    y = est - ff.reindex(est.index)["RF"]
    ok = X.notna().all(axis=1) & y.notna()
    Xe = ff.reindex(ev.index)[fcols]
    if ok.sum() >= 120 and not Xe.isna().any().any():
        b = sm.OLS(y[ok], sm.add_constant(X[ok])).fit().params
        pred = b["const"] + (Xe * b.drop("const")).sum(axis=1) + ff.reindex(ev.index)["RF"]
        ar = ev - pred
    else:
        # French factors are published with a lag; use a market model on SPY instead.
        spy = ret["SPY"].reindex(ev.index)
        est_spy = ret["SPY"].reindex(est.index)
        bb = sm.OLS(est, sm.add_constant(est_spy), missing="drop").fit().params
        ar = ev - (bb.iloc[0] + bb.iloc[1] * spy)
    return ar.sum(), ar.iloc[0], ar.iloc[-1] if len(ar) > 1 else np.nan


def capex_surprise(q):
    """Seasonal random walk with drift, scaled by lagged assets; also YoY growth."""
    out = []
    for t, g in q.sort_values("period_end").groupby("ticker"):
        g = g.copy()
        c = g["capex"]
        yoy = c - c.shift(4)
        drift = yoy.shift(1).rolling(4).mean()
        g["capex_forecast"] = c.shift(4) + drift
        g["capex_surprise"] = c - g["capex_forecast"]
        g["capex_surprise_assets"] = g["capex_surprise"] / g["assets"].shift(1)
        g["capex_yoy_growth"] = c / c.shift(4) - 1
        g["capex_to_cfo"] = c / g["cfo"]
        g["capex_to_dep"] = c / g["dep"]
        out.append(g)
    return pd.concat(out)


def build_events(ret, ff, q, e, k8):
    days = ret.index
    e = e[e["reported_eps"].notna() & (e["earnings_date"] >= EVENT_START)].copy()
    e["event_day"] = [reaction_day(ts, days) for ts in e["earnings_date"]]
    e = e.drop_duplicates(subset=["ticker", "event_day"])
    # Cross-check with the 8-K item 2.02 filing date (should be within a day).
    k8s = k8[["ticker", "filingDate"]].sort_values("filingDate")
    e = e.sort_values("event_day")
    e = pd.merge_asof(e, k8s.rename(columns={"filingDate": "filing_8k"}), left_on="event_day",
                      right_on="filing_8k", by="ticker", tolerance=pd.Timedelta("3D"),
                      direction="nearest")
    # Attach the quarter whose results are being released: last period end before the event.
    qs = capex_surprise(q)
    qs = qs.sort_values("period_end")
    e = pd.merge_asof(e, qs, left_on="event_day", right_on="period_end", by="ticker",
                      tolerance=pd.Timedelta("75D"), direction="backward")
    cars = [abnormal_returns(ret, ff, t, d) for t, d in zip(e["ticker"], e["event_day"])]
    e[["car_0_1", "ar_0", "ar_1"]] = pd.DataFrame(cars, index=e.index)
    e["raw_ret_0_1"] = [ret[t].loc[d:].iloc[:2].sum() for t, d in zip(e["ticker"], e["event_day"])]
    e["spy_ret_0_1"] = [ret["SPY"].loc[d:].iloc[:2].sum() for d in e["event_day"]]
    e["is_hyperscaler"] = e["ticker"].isin(["MSFT", "GOOGL", "AMZN", "META", "ORCL"])
    cols = ["ticker", "is_hyperscaler", "earnings_date", "event_day", "filing_8k", "period_end",
            "eps_estimate", "reported_eps", "surprisepct", "capex", "capex_forecast",
            "capex_surprise", "capex_surprise_assets", "capex_yoy_growth", "capex_to_cfo",
            "capex_to_dep", "revenue", "op_income", "car_0_1", "ar_0", "ar_1", "raw_ret_0_1",
            "spy_ret_0_1"]
    return e[cols].sort_values(["event_day", "ticker"]).reset_index(drop=True), qs


def build_ai_factor(ret, ff):
    basket = [t for t in list(AI_FIRMS) + AI_SUPPLY_CHAIN_EXTRA if t in ret]
    ai = ret[basket].mean(axis=1)
    f = pd.DataFrame({"ai_basket": ai, "spy": ret["SPY"]})
    f["ai_minus_mkt"] = f["ai_basket"] - f["spy"]
    X = ff[["Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom"]].reindex(f.index)
    y = f["ai_basket"] - ff["RF"].reindex(f.index)
    ok = X.notna().all(axis=1) & y.notna()
    m = sm.OLS(y[ok], sm.add_constant(X[ok])).fit()
    f["ai_ff_resid"] = np.nan
    f.loc[ok, "ai_ff_resid"] = m.resid
    print("AI basket on FF5+Mom: alpha(daily)=%.5f  beta_mkt=%.2f  R2=%.2f  n=%d" %
          (m.params["const"], m.params["Mkt-RF"], m.rsquared, int(ok.sum())))
    return f


def main():
    ret, ff, q, e, k8 = load()
    events, qs = build_events(ret, ff, q, e, k8)
    events.to_csv(PROC / "events.csv", index=False)
    qs.to_csv(PROC / "capex_quarterly_with_surprises.csv", index=False)
    print(f"events: {len(events)} releases, {events['ticker'].nunique()} firms, "
          f"{events['event_day'].min().date()} -> {events['event_day'].max().date()}")
    print("8-K date matched within 3 days:", events["filing_8k"].notna().mean().round(2))
    print(events.groupby("ticker")["car_0_1"].agg(["count", "mean", "std"]).round(4))

    f = build_ai_factor(ret, ff)
    f.to_csv(PROC / "ai_factor_daily.csv")

    # Daily aggregate "AI earnings news" shock: mean CAR of the firms reporting that day,
    # placed on the reaction day, zero on other days.
    daily = events.groupby("event_day")["car_0_1"].mean().rename("ai_earnings_shock")
    hyp = events[events["is_hyperscaler"]].groupby("event_day")["car_0_1"].mean() \
        .rename("hyperscaler_earnings_shock")
    cap = events.groupby("event_day")["capex_surprise_assets"].mean().rename("capex_surprise_assets")
    shocks = pd.concat([daily, hyp, cap], axis=1).reindex(ret.index)
    shocks["n_reporting"] = events.groupby("event_day").size().reindex(ret.index).fillna(0).astype(int)
    shocks = shocks.join(f[["ai_minus_mkt", "ai_ff_resid"]])
    shocks.index.name = "date"
    shocks.to_csv(PROC / "shocks_daily.csv")
    print("wrote events.csv, capex_quarterly_with_surprises.csv, ai_factor_daily.csv, shocks_daily.csv")


if __name__ == "__main__":
    main()
