"""Daily prices and earnings-date/EPS-surprise tables from Yahoo Finance.

Outputs
-------
data/processed/prices_adjclose.csv : wide panel of adjusted closes (one column per ticker).
data/processed/returns_daily.csv   : simple daily returns.
data/processed/yahoo_earnings_dates.csv : announcement timestamps with EPS estimate,
    reported EPS and surprise for the AI firms.
"""
import time

import pandas as pd
import yfinance as yf

from common import AI_FIRMS, ALL_TICKERS, PROC, RAW, START


def main():
    px = yf.download(ALL_TICKERS, start=START, auto_adjust=True, progress=False,
                     group_by="column", threads=False)
    close = px["Close"].copy()
    close.index.name = "date"
    close.to_csv(PROC / "prices_adjclose.csv")
    close.pct_change().to_csv(PROC / "returns_daily.csv")
    print("prices:", close.shape, "from", close.index.min().date(), "to",
          close.index.max().date())
    missing = close.isna().mean().sort_values(ascending=False).head(8)
    print("share missing (top):\n", missing.round(3).to_string())

    frames = []
    for t in AI_FIRMS:
        try:
            ed = yf.Ticker(t).get_earnings_dates(limit=60)
        except Exception as e:  # noqa: BLE001
            print(t, "earnings dates failed:", e)
            continue
        if ed is None or ed.empty:
            print(t, "no earnings dates")
            continue
        ed = ed.reset_index()
        ed.insert(0, "ticker", t)
        frames.append(ed)
        time.sleep(0.5)
    if frames:
        e = pd.concat(frames, ignore_index=True)
        e.columns = [c.strip().lower().replace(" ", "_").replace("(%)", "pct")
                     for c in e.columns]
        e.to_csv(RAW / "yahoo_earnings_dates_raw.csv", index=False)
        e.to_csv(PROC / "yahoo_earnings_dates.csv", index=False)
        print("earnings dates:", e.shape, "columns:", list(e.columns))
        print(e.head(3).to_string())


if __name__ == "__main__":
    main()
