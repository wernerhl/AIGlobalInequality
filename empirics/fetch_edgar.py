"""Pull quarterly financials and earnings-release (8-K item 2.02) dates from SEC EDGAR.

Outputs
-------
data/raw/edgar/companyfacts_<TICKER>.json, submissions_<TICKER>.json
data/processed/edgar_quarterly.csv : one row per firm-quarter with capex, revenue,
    operating income, net income, total assets, cash from operations (de-cumulated
    from the year-to-date figures that 10-Q filings report).
data/processed/edgar_8k_earnings.csv : filing dates of 8-Ks reporting results (item 2.02).
"""
import json
import time

import pandas as pd
import requests

from common import AI_FIRMS, PROC, RAW, SEC_UA

EDGAR_RAW = RAW / "edgar"
EDGAR_RAW.mkdir(exist_ok=True)
HEADERS = {"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"}

# Flow concepts are reported year-to-date in 10-Qs; stock concepts are point-in-time.
FLOW_CONCEPTS = {
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment",
              "PaymentsToAcquireProductiveAssets"],
    "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
                "SalesRevenueNet"],
    "op_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss"],
    "cfo": ["NetCashProvidedByUsedInOperatingActivities"],
    "dep": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization",
            "Depreciation"],
}
STOCK_CONCEPTS = {
    "assets": ["Assets"],
    "ppe_net": ["PropertyPlantAndEquipmentNet"],
}


def get_json(url, path):
    if path.exists():
        return json.loads(path.read_text())
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    path.write_text(r.text)
    time.sleep(0.2)  # SEC rate limit is 10 requests/second
    return r.json()


def facts_frame(facts, concept):
    """All USD observations of a us-gaap concept from 10-K/10-Q filings."""
    try:
        obs = facts["facts"]["us-gaap"][concept]["units"]["USD"]
    except KeyError:
        return None
    df = pd.DataFrame(obs)
    df = df[df["form"].isin(["10-K", "10-Q", "10-K/A", "10-Q/A"])].copy()
    if df.empty:
        return None
    for c in ("start", "end", "filed"):
        if c in df:
            df[c] = pd.to_datetime(df[c])
    return df


def decumulate_flow(df):
    """Convert year-to-date flow observations into quarterly flows.

    For each fiscal-year start date, the filings give cumulative values at the end of
    Q1, Q2, Q3 and FY. Differencing successive cumulative values within a start date
    yields quarterly flows; ~3-month observations are used directly.
    """
    df = df.dropna(subset=["start"]).sort_values("filed")
    # Keep the most recently filed value for each (start, end) pair.
    df = df.drop_duplicates(subset=["start", "end"], keep="last")
    df["days"] = (df["end"] - df["start"]).dt.days
    rows = []
    for start, g in df.groupby("start"):
        g = g.sort_values("end")
        prev_end, prev_val = None, 0.0
        for _, r in g.iterrows():
            if r["days"] < 100:
                rows.append((r["end"], r["val"]))
                prev_end, prev_val = r["end"], r["val"]
            elif prev_end is not None and 70 <= (r["end"] - prev_end).days <= 110:
                rows.append((r["end"], r["val"] - prev_val))
                prev_end, prev_val = r["end"], r["val"]
            else:
                # Cumulative value with no preceding quarter in this start group
                # (e.g. restated 6-month figure); cannot de-cumulate, skip.
                prev_end, prev_val = r["end"], r["val"]
    out = pd.DataFrame(rows, columns=["end", "val"]).drop_duplicates("end", keep="last")
    return out.set_index("end")["val"].sort_index()


def stock_series(df):
    df = df.sort_values("filed").drop_duplicates(subset=["end"], keep="last")
    return df.set_index("end")["val"].sort_index()


def first_available(facts, concepts, builder):
    """Merge the concept series in order of preference (firms switch tags over time)."""
    merged, used = None, []
    for c in concepts:
        df = facts_frame(facts, c)
        if df is None or len(df) < 4:
            continue
        s = builder(df)
        if s.empty:
            continue
        merged = s if merged is None else merged.combine_first(s)
        used.append(c)
    if merged is None:
        return None, None
    return merged.sort_index(), "+".join(used)


def earnings_8k_dates(subs):
    rec = subs["filings"]["recent"]
    df = pd.DataFrame({k: rec[k] for k in ("form", "filingDate", "reportDate", "items",
                                            "accessionNumber")})
    df = df[(df["form"] == "8-K") & df["items"].fillna("").str.contains("2.02")]
    df["filingDate"] = pd.to_datetime(df["filingDate"])
    df["reportDate"] = pd.to_datetime(df["reportDate"])
    return df.sort_values("filingDate")


def main():
    quarterly, eightk = [], []
    for ticker, cik in AI_FIRMS.items():
        cik10 = f"{cik:010d}"
        facts = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json",
                         EDGAR_RAW / f"companyfacts_{ticker}.json")
        subs = get_json(f"https://data.sec.gov/submissions/CIK{cik10}.json",
                        EDGAR_RAW / f"submissions_{ticker}.json")
        cols, used = {}, {}
        for name, concepts in FLOW_CONCEPTS.items():
            s, c = first_available(facts, concepts, decumulate_flow)
            if s is not None:
                cols[name], used[name] = s, c
        for name, concepts in STOCK_CONCEPTS.items():
            s, c = first_available(facts, concepts, stock_series)
            if s is not None:
                cols[name], used[name] = s, c
        df = pd.DataFrame(cols)
        df.index.name = "period_end"
        df = df[df.index >= "2015-01-01"].reset_index()
        df.insert(0, "ticker", ticker)
        df["fiscal_year_end"] = facts.get("fiscalYearEnd", "")  # mmdd
        quarterly.append(df)
        print(f"{ticker}: {len(df)} quarters; concepts used: {used}")

        e = earnings_8k_dates(subs)
        e.insert(0, "ticker", ticker)
        eightk.append(e)
        print(f"{ticker}: {len(e)} 8-K earnings releases, latest {e['filingDate'].max().date()}")

    q = pd.concat(quarterly, ignore_index=True)
    q.to_csv(PROC / "edgar_quarterly.csv", index=False)
    k = pd.concat(eightk, ignore_index=True)
    k.to_csv(PROC / "edgar_8k_earnings.csv", index=False)
    print("wrote", PROC / "edgar_quarterly.csv", "and", PROC / "edgar_8k_earnings.csv")


if __name__ == "__main__":
    main()
