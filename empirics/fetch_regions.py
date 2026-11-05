"""Country- and region-level external financing (who is left behind).

Sources
  World Bank WDI, country level: net ODA received (USD and % of GNI), FDI inflows (USD,
      % of GDP), portfolio equity, remittances, gross capital formation (% GDP), GDP,
      GNI, GDP per capita, population, debt service (% exports).
  World Bank IDS, country level: net external-debt flows by creditor type (total,
      official, multilateral, bilateral, private, PPG bonds, PNG bonds), disbursements.
  World Bank country metadata: region and income group.
  OECD DAC2A: ODA received by recipient (all donors), net and gross, humanitarian,
      imputed multilateral, country programmable aid, ODA % GNI (fetched in
      fetch_regions_oecd() if the SDMX key is available).
Outputs: data/processed/wb_country_panel.csv (long), data/processed/wb_country_meta.csv
"""
import json
import time

import pandas as pd
import requests

from common import PROC, RAW, SEC_UA

WBC = RAW / "wb_country"
WBC.mkdir(exist_ok=True)
HDR = {"User-Agent": SEC_UA}

WDI = {
    "DT.ODA.ODAT.CD": "net_oda_received", "DT.ODA.ODAT.GN.ZS": "net_oda_pct_gni",
    "DT.ODA.ODAT.PC.ZS": "net_oda_per_capita",
    "BX.KLT.DINV.CD.WD": "fdi_inflows", "BX.KLT.DINV.WD.GD.ZS": "fdi_pct_gdp",
    "BX.PEF.TOTL.CD.WD": "portfolio_equity_inflows", "BX.TRF.PWKR.CD.DT": "remittances",
    "NE.GDI.TOTL.ZS": "gcf_pct_gdp", "NE.GDI.TOTL.CD": "gross_capital_formation",
    "NY.GDP.MKTP.CD": "gdp", "NY.GNP.MKTP.CD": "gni", "NY.GDP.PCAP.CD": "gdp_per_capita",
    "SP.POP.TOTL": "population", "DT.TDS.DECT.EX.ZS": "debt_service_pct_exports",
    "GC.XPN.TOTL.GD.ZS": "govt_expenditure_pct_gdp",
}
IDS = {
    "DT.NFL.DECT.CD": "net_debt_flows_total", "DT.NFL.OFFT.CD": "net_debt_flows_official",
    "DT.NFL.MLAT.CD": "net_debt_flows_multilateral", "DT.NFL.BLAT.CD": "net_debt_flows_bilateral",
    "DT.NFL.PRVT.CD": "net_debt_flows_private", "DT.NFL.PBND.CD": "net_debt_flows_bonds_ppg",
    "DT.NFL.PNGB.CD": "net_debt_flows_bonds_png", "DT.NFL.PCBK.CD": "net_debt_flows_banks_ppg",
    "DT.DIS.DLXF.CD": "disbursements_ltd", "DT.DOD.DECT.CD": "external_debt_stock",
}


def get(url, path, retries=4):
    if path.exists() and path.stat().st_size > 100:
        return json.loads(path.read_text())
    for i in range(retries):
        try:
            r = requests.get(url, headers=HDR, timeout=300)
            r.raise_for_status()
            path.write_text(r.text)
            return r.json()
        except requests.exceptions.RequestException:
            if i == retries - 1:
                raise
            time.sleep(2 ** (i + 1))


def meta():
    js = get("https://api.worldbank.org/v2/country?format=json&per_page=400", WBC / "countries.json")[1]
    rows = [(c["id"], c["iso2Code"], c["name"], c["region"]["value"].strip(), c["incomeLevel"]["value"],
             c["lendingType"]["value"]) for c in js if c["region"]["id"] != "NA"]
    m = pd.DataFrame(rows, columns=["iso3", "iso2", "country", "region", "income_group", "lending_type"])
    m.to_csv(PROC / "wb_country_meta.csv", index=False)
    return m


def wdi_all(ind):
    rows = []
    page = 1
    while True:
        js = get(f"https://api.worldbank.org/v2/country/all/indicator/{ind}?format=json&date=2010:2025&per_page=5000&page={page}",
                 WBC / f"wdi_{ind}_p{page}.json")
        rows += [(r["countryiso3code"], int(r["date"]), r["value"]) for r in js[1] if r["countryiso3code"]]
        if page >= js[0]["pages"]:
            break
        page += 1
    return pd.DataFrame(rows, columns=["iso3", "year", "value"])


def ids_all(ind):
    js = get(f"https://api.worldbank.org/v2/sources/6/country/all/series/{ind}/counterpart-area/WLD/time/all?format=json&per_page=20000",
             WBC / f"ids_{ind}.json")
    rows = []
    for obs in js["source"]["data"]:
        rec = {v["concept"].lower(): v["id"] for v in obs["variable"]}
        rows.append((rec.get("country"), rec.get("time"), obs.get("value")))
    df = pd.DataFrame(rows, columns=["iso3", "time", "value"])
    df["year"] = df["time"].str.extract(r"(\d{4})").astype(float)
    return df[["iso3", "year", "value"]]


DAC2A_MEASURES = {206: "oda_net", 240: "oda_gross", 216: "humanitarian", 106: "imputed_multilateral",
                  245: "country_programmable_aid", 286: "oda_pct_gni", 201: "oda_grants", 218: "oda_loans_net"}


def oecd_dac2a():
    """ODA received by recipient (countries, regions, income groups), constant USD mn, from
    all official donors (ALLD) and from the United States (USA). Key:
    DONOR.RECIPIENT.MEASURE.UNIT_MEASURE.PRICE_BASE."""
    frames = []
    for donor in ("ALLD", "USA", "DAC"):
        path = RAW / "oecd" / f"dac2a_{donor}_recipients.csv"
        if not path.exists():
            url = ("https://sdmx.oecd.org/public/rest/data/OECD.DCD.FSD,DSD_DAC2@DF_DAC2A,/"
                   f"{donor}..{'+'.join(str(k) for k in DAC2A_MEASURES)}.USD.Q?startPeriod=2012&format=csvfilewithlabels")
            r = requests.get(url, headers={**HDR, "Accept": "text/csv"}, timeout=900)
            r.raise_for_status()
            path.write_bytes(r.content)
        d = pd.read_csv(path, low_memory=False)
        d = d[["DONOR", "RECIPIENT", "Recipient", "MEASURE", "TIME_PERIOD", "OBS_VALUE"]]
        d.columns = ["donor", "recipient", "recipient_name", "measure", "year", "value"]
        d["series"] = d["measure"].map(DAC2A_MEASURES)
        frames.append(d)
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(PROC / "oecd_dac2a_by_recipient.csv", index=False)
    print("DAC2A rows:", len(out), "recipients:", out.recipient.nunique(), "years:", out.year.min(), "-", out.year.max())
    return out


def main():
    oecd_dac2a()
    m = meta()
    print("countries:", len(m))
    frames = []
    for ind, name in WDI.items():
        try:
            d = wdi_all(ind); d["series"] = name; frames.append(d)
            print(f"WDI {ind:22s} {name:28s} rows={len(d.dropna())}")
        except Exception as e:  # noqa: BLE001
            print("WDI failed", ind, e)
        time.sleep(0.3)
    for ind, name in IDS.items():
        try:
            d = ids_all(ind); d["series"] = name; frames.append(d)
            print(f"IDS {ind:22s} {name:28s} rows={len(d.dropna())} countries={d.dropna().iso3.nunique()}")
        except Exception as e:  # noqa: BLE001
            print("IDS failed", ind, e)
        time.sleep(0.3)
    out = pd.concat(frames, ignore_index=True).dropna(subset=["value"])
    out = out[out["iso3"].isin(m["iso3"]) & (out["year"] >= 2010) & (out["year"] <= 2025)]
    out.to_csv(PROC / "wb_country_panel.csv", index=False)
    print("panel rows:", len(out), "countries:", out.iso3.nunique())


if __name__ == "__main__":
    main()
