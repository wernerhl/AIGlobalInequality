"""FRED daily series (rates, VIX, dollar, EM and US credit spreads) and Ken French factors.

Outputs
-------
data/processed/fred_daily.csv   : one column per FRED series, daily, NaN on holidays.
data/processed/ff_factors_daily.csv : Fama-French 5 factors + momentum, daily, in decimals.
"""
import io
import zipfile

import pandas as pd
import requests

from common import FRED_SERIES, PROC, RAW, START

FF_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FF_FILES = {
    "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip": "F-F_Research_Data_5_Factors_2x3_daily.csv",
    "F-F_Momentum_Factor_daily_CSV.zip": "F-F_Momentum_Factor_daily.csv",
}


def fetch_fred():
    cols = {}
    for sid, desc in FRED_SERIES.items():
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        (RAW / f"fred_{sid}.csv").write_text(r.text)
        df = pd.read_csv(io.StringIO(r.text), na_values=".")
        df.columns = ["date", sid]
        df["date"] = pd.to_datetime(df["date"])
        cols[sid] = df.set_index("date")[sid]
        print(f"{sid:22s} {desc:55s} {df['date'].min().date()} -> {df['date'].max().date()}")
    out = pd.DataFrame(cols)
    out = out[out.index >= START]
    out.to_csv(PROC / "fred_daily.csv")
    return out


def parse_french(text):
    """French CSVs have a text header, then rows 'YYYYMMDD,x,y,...' and a trailer."""
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l[:8].strip().isdigit())
    body = []
    for l in lines[start:]:
        if l[:8].strip().isdigit():
            body.append(l)
        elif body:
            break
    header = lines[start - 1]
    df = pd.read_csv(io.StringIO("\n".join([header] + body)))
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    df.columns = [c.strip() for c in df.columns]
    return df.set_index("date") / 100.0


def fetch_french():
    parts = []
    for zname, cname in FF_FILES.items():
        r = requests.get(FF_BASE + zname, timeout=60)
        r.raise_for_status()
        (RAW / zname).write_bytes(r.content)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            text = z.read(cname).decode("latin-1")
        parts.append(parse_french(text))
    ff = pd.concat(parts, axis=1)
    ff.columns = [c.replace("Mom   ", "Mom").strip() for c in ff.columns]
    ff = ff[ff.index >= START]
    ff.to_csv(PROC / "ff_factors_daily.csv")
    print("French factors:", list(ff.columns), ff.index.min().date(), "->", ff.index.max().date())
    return ff


if __name__ == "__main__":
    fetch_fred()
    fetch_french()
