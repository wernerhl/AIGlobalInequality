"""Financing flows to development uses and to non-AI uses in the United States.

Why: the model's prediction is about quantities (K_D falls) as well as the price r, and
the pool is shared, so we need (a) financing to developing countries by vehicle and
sector and (b) financing to non-AI uses inside the US as a within-pool comparison.

Sources (all free)
  OECD DAC1          ODA and other flows by donor, annual, incl. preliminary 2025.
  OECD DAC5          Bilateral ODA commitments by sector and donor, annual.
  OECD Mobilisation  Private finance mobilised by official interventions, by sector,
                     recipient and leveraging mechanism, annual.
  World Bank WDI/IDS Net ODA received, FDI, portfolio equity, remittances, external
                     debt flows by creditor type for LIC / LMC / IDA aggregates, annual.
  BIS LBS            Cross-border bank claims on emerging and developing economies,
                     quarterly flows (FX/break adjusted) and stocks, by region/sector.
  BIS IDS            International debt securities net and gross issuance by EMDE
                     residents, quarterly, incl. general government.
  FRED (BEA/Z.1)     US private nonresidential investment by type, information-processing
                     equipment and software, R&D, C&I loans, nonfinancial corporate debt.
  Census C30         Private construction spending by category, monthly, incl. data centers.

Outputs in data/processed/: oecd_dac1_by_donor.csv, oecd_dac5_sector.csv,
oecd_mobilisation.csv, wb_flows.csv, bis_lbs_quarterly.csv, bis_ids_quarterly.csv,
fred_us_investment.csv, census_construction_monthly.csv
"""
import io
import json
import time

import pandas as pd
import requests

from common import PROC, RAW, SEC_UA

OECD_RAW = RAW / "oecd"
OECD_RAW.mkdir(exist_ok=True)
(RAW / "wb").mkdir(exist_ok=True)
(RAW / "bis").mkdir(exist_ok=True)
(RAW / "fred_extra").mkdir(exist_ok=True)
(RAW / "census").mkdir(exist_ok=True)
HDR = {"User-Agent": SEC_UA}


def download(url, path, headers=None, timeout=600, retries=4):
    if path.exists() and path.stat().st_size > 0:
        return path
    for i in range(retries):
        try:
            r = requests.get(url, headers=headers or HDR, timeout=timeout)
            r.raise_for_status()
            path.write_bytes(r.content)
            return path
        except requests.exceptions.HTTPError:
            raise
        except requests.exceptions.RequestException:
            if i == retries - 1:
                raise
            time.sleep(2 ** (i + 1))


# ----------------------------------------------------------------------------- OECD
def oecd_dac1():
    p = download("https://sdmx.oecd.org/public/rest/data/OECD.DCD.FSD,DSD_DAC1@DF_DAC1,/all"
                 "?startPeriod=2018&format=csvfilewithlabels", OECD_RAW / "dac1_all_2018.csv",
                 headers={"Accept": "text/csv"})
    d = pd.read_csv(p, low_memory=False)
    d = d[(d["UNIT_MEASURE"].isin(["USD", "PT_B5G"]))]
    keep = {1010: "oda_net", 11010: "oda_grant_equiv", 1015: "bilateral_oda", 2000: "multilateral_oda",
            3300: "private_flows_market", 200: "oof", 1820: "refugees_in_donor", 1: "gni",
            1600: "debt_relief", 2233: "mobilised_private_memo", 11015: "bilateral_oda_ge",
            5: "official_and_private_flows"}
    hum = d[d["Measure"].str.contains("umanitarian", case=False, na=False)]["MEASURE"].unique()
    for h in hum:
        keep[int(h)] = "humanitarian_" + str(h)
    d = d[d["MEASURE"].astype(int).isin(keep)].copy()
    d["measure_name"] = d["MEASURE"].astype(int).map(keep)
    out = d[["DONOR", "Donor", "MEASURE", "measure_name", "Measure", "FLOW_TYPE", "Flow type",
             "UNIT_MEASURE", "PRICE_BASE", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS"]]
    out.columns = ["donor", "donor_name", "measure", "measure_name", "measure_label", "flow_type",
                   "flow_type_label", "unit", "price_base", "year", "value", "obs_status"]
    out.to_csv(PROC / "oecd_dac1_by_donor.csv", index=False)
    tot = out[(out.donor == "DAC") & (out.measure == 1010) & (out.flow_type == 1140)
              & (out.unit == "USD")].pivot(index="year", columns="price_base", values="value")
    print("DAC1: ODA net disbursements, DAC total (USD mn):\n", tot.round(0).to_string())
    return out


def oecd_dac5():
    p = download("https://sdmx.oecd.org/public/rest/data/OECD.DCD.FSD,DSD_DAC1@DF_DAC5,/all"
                 "?startPeriod=2018&format=csvfilewithlabels", OECD_RAW / "dac5_all_2018.csv",
                 headers={"Accept": "text/csv"})
    d = pd.read_csv(p, low_memory=False)
    d = d[d["UNIT_MEASURE"] == "USD"]
    out = d[["DONOR", "Donor", "SECTOR", "Sector", "MEASURE", "Measure", "PRICE_BASE",
             "TIME_PERIOD", "OBS_VALUE"]]
    out.columns = ["donor", "donor_name", "sector", "sector_name", "measure", "measure_label",
                   "price_base", "year", "value"]
    out.to_csv(PROC / "oecd_dac5_sector.csv", index=False)
    t = out[(out.donor == "DAC") & (out.measure == 528) & (out.price_base == "Q")]
    piv = t.pivot_table(index="sector_name", columns="year", values="value")
    print("DAC5: DAC bilateral ODA commitments by sector, constant USD mn (selected):")
    sel = ["All sectors", "Health", "Education", "Humanitarian aid", "Energy", "Transport and storage",
           "Water supply & sanitation", "General environment protection", "Agriculture"]
    print(piv.loc[[s for s in sel if s in piv.index]].round(0).to_string())
    return out


def oecd_mobilisation():
    # The public endpoint returns 500 for this dataflow; the dcd-public endpoint works.
    # Key order: PROVIDER.RECIPIENT.SECTOR.MEASURE.FLOW_TYPE.PRICE_BASE.UNIT_MEASURE;
    # all official providers (ALLD), every recipient and sector, total leveraging mechanism.
    base = "https://sdmx.oecd.org/dcd-public/rest/data/OECD.DCD.FSD,DSD_MOB@DF_MOBILISATION,/"
    p = OECD_RAW / "mobilisation_alld_2012.csv"
    try:
        download(base + "ALLD..._T..." + "?startPeriod=2012&format=csvfilewithlabels", p,
                 headers={"Accept": "text/csv"})
    except Exception as e:  # noqa: BLE001
        print("mobilisation filtered query failed:", e, "- falling back to 2022+ full file")
        p = download(base + "all?startPeriod=2022&format=csvfilewithlabels",
                     OECD_RAW / "mobilisation_2022.csv", headers={"Accept": "text/csv"})
    d = pd.read_csv(p, low_memory=False)
    out = d[["PROVIDER", "Provider", "RECIPIENT", "Recipient", "SECTOR", "Sector", "MEASURE",
             "Leveraging mechanism", "FLOW_TYPE", "PRICE_BASE", "TIME_PERIOD", "OBS_VALUE"]]
    out.columns = ["provider", "provider_name", "recipient", "recipient_name", "sector",
                   "sector_name", "mechanism", "mechanism_name", "flow_type", "price_base",
                   "year", "value"]
    out.to_csv(PROC / "oecd_mobilisation.csv", index=False)
    print("mobilisation rows:", len(out), "years:", sorted(out.year.unique()),
          "providers:", out.provider.nunique())
    return out


# ----------------------------------------------------------------------- World Bank
WB_AGG = ["LIC", "LMC", "UMC", "SSF", "IDX", "WLD"]   # WDI aggregates (IDX = IDA total)
IDS_AGG = ["LIC", "LMC", "UMC", "LMY", "SSA"]          # IDS income-group aggregates
WDI = {"DT.ODA.ODAT.CD": "net_oda_received", "BX.KLT.DINV.CD.WD": "fdi_inflows",
       "BX.PEF.TOTL.CD.WD": "portfolio_equity_inflows", "BX.TRF.PWKR.CD.DT": "remittances",
       "NE.GDI.TOTL.CD": "gross_capital_formation", "NY.GDP.MKTP.CD": "gdp",
       "NY.GNP.MKTP.CD": "gni"}
IDS = {"DT.NFL.DECT.CD": "net_debt_flows_total", "DT.NFL.PRVT.CD": "net_debt_flows_private_creditors",
       "DT.NFL.PBND.CD": "net_debt_flows_bonds_ppg", "DT.NFL.PCBK.CD": "net_debt_flows_banks_ppg",
       "DT.NFL.OFFT.CD": "net_debt_flows_official", "DT.NFL.MLAT.CD": "net_debt_flows_multilateral",
       "DT.NFL.BLAT.CD": "net_debt_flows_bilateral", "DT.DIS.DLXF.CD": "disbursements_ltd_ext_debt",
       "DT.NFL.PNGB.CD": "net_debt_flows_bonds_png", "DT.NFL.IMF.CD": "net_flows_imf"}


def wb_wdi(ind, countries):
    url = (f"https://api.worldbank.org/v2/country/{';'.join(countries)}/indicator/{ind}"
           f"?format=json&date=2010:2026&per_page=2000")
    p = RAW / "wb" / f"wdi_{ind}.json"
    download(url, p)
    js = json.loads(p.read_text())
    rows = [(r["country"]["id"], r["countryiso3code"], int(r["date"]), r["value"]) for r in js[1]]
    return pd.DataFrame(rows, columns=["country_id", "iso3", "year", "value"])


def wb_ids(ind, countries):
    url = (f"https://api.worldbank.org/v2/sources/6/country/{';'.join(countries)}/series/{ind}"
           f"/counterpart-area/WLD/time/all?format=json&per_page=5000")
    p = RAW / "wb" / f"ids_{ind}.json"
    download(url, p)
    js = json.loads(p.read_text())
    rows = []
    for obs in js["source"]["data"]:
        rec = {v["concept"].lower(): v["id"] for v in obs["variable"]}
        rows.append((rec.get("country"), rec.get("time"), obs.get("value")))
    df = pd.DataFrame(rows, columns=["country_id", "time", "value"])
    df["year"] = df["time"].str.extract(r"(\d{4})").astype(float)
    return df[["country_id", "year", "value"]]


def world_bank():
    frames = []
    for ind, name in WDI.items():
        try:
            d = wb_wdi(ind, WB_AGG)
            d["series"] = name
            frames.append(d[["country_id", "year", "series", "value"]])
            print(f"WDI {ind:22s} {name:30s} rows={len(d)}")
        except Exception as e:  # noqa: BLE001
            print("WDI failed", ind, e)
        time.sleep(0.3)
    for ind, name in IDS.items():
        try:
            d = wb_ids(ind, IDS_AGG)
            d["series"] = name
            frames.append(d)
            print(f"IDS {ind:22s} {name:34s} rows={len(d)} latest={d.dropna().year.max()}")
        except Exception as e:  # noqa: BLE001
            print("IDS failed", ind, e)
        time.sleep(0.3)
    out = pd.concat(frames, ignore_index=True).dropna(subset=["value"])
    out = out[out["year"] >= 2010]
    out.to_csv(PROC / "wb_flows.csv", index=False)
    piv = out[out.country_id.isin(["LIC", "XM"])].pivot_table(index="year", columns="series", values="value") / 1e9
    print("Low-income countries, USD bn:\n", piv.round(1).tail(8).to_string())
    return out


# ------------------------------------------------------------------------------ BIS
BIS = "https://stats.bis.org/api/v2/data/dataflow/BIS/"
LBS_CP = {"4T": "EMDE", "4W": "Africa_MiddleEast", "4Y": "Asia_Pacific", "4U": "LatAm_Caribbean",
          "3C": "Emerging_Europe", "US": "United_States", "5J": "All_countries"}
LBS_SECTOR = {"A": "all_sectors", "G": "general_government", "N": "non_banks"}


def bis_csv(flow, key, path):
    download(f"{BIS}{flow}/1.0/{key}?startPeriod=2010-01-01&format=csv", path)
    d = pd.read_csv(path)
    d["TIME_PERIOD"] = pd.PeriodIndex(d["TIME_PERIOD"].str.replace("-", ""), freq="Q")
    return d[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"TIME_PERIOD": "quarter"})


def bis():
    rows = []
    for cp, cpn in LBS_CP.items():
        for sec, secn in LBS_SECTOR.items():
            for meas, mn in (("F", "flow_fx_adj"), ("S", "stock")):
                key = f"Q.{meas}.C.A.TO1.A.5J.A.5A.{sec}.{cp}.N"
                try:
                    d = bis_csv("WS_LBS_D_PUB", key, RAW / "bis" / f"lbs_{meas}_{sec}_{cp}.csv")
                except Exception as e:  # noqa: BLE001
                    print("LBS missing", key, type(e).__name__)
                    continue
                d["series"] = f"xb_claims_{mn}_{secn}_{cpn}"
                rows.append(d)
    lbs = pd.concat(rows, ignore_index=True)
    lbs.to_csv(PROC / "bis_lbs_quarterly.csv", index=False)
    print("LBS series:", lbs.series.nunique(), "quarters to", lbs.quarter.max())

    rows = []
    ids_res = {k: v for k, v in LBS_CP.items() if k != "5J"}
    ids_res.update({"1C": "Intl_organisations", "3P": "World"})
    for res, resn in ids_res.items():
        # Immediate issuer sector with ultimate sector "all" (the only combination published).
        buses = (("1", "all_issuers"),) if res in ("1C", "3P") else \
            (("1", "all_issuers"), ("2", "general_government"), ("J", "nonfin_corps"))
        for bus, busn in buses:
            for meas, mn in (("G", "net_issues"), ("C", "gross_issues"), ("I", "outstanding")):
                key = f"Q.{res}.3P.{bus}.1.C.A.A.TO1.A.A.A.A.A.{meas}"
                try:
                    d = bis_csv("WS_DEBT_SEC2_PUB", key, RAW / "bis" / f"ids_{meas}_{bus}_{res}.csv")
                except Exception as e:  # noqa: BLE001
                    print("IDS missing", key, type(e).__name__)
                    continue
                d["series"] = f"intl_debt_sec_{mn}_{busn}_{resn}"
                rows.append(d)
    ids = pd.concat(rows, ignore_index=True)
    ids.to_csv(PROC / "bis_ids_quarterly.csv", index=False)
    print("IDS series:", ids.series.nunique(), "quarters to", ids.quarter.max())
    return lbs, ids


# ------------------------------------------------------------------------- FRED / BEA
FRED_INV = {
    "PNFI": "private_nonres_fixed_investment", "B009RC1Q027SBEA": "nonres_structures",
    "Y033RC1Q027SBEA": "nonres_equipment", "Y001RC1Q027SBEA": "intellectual_property",
    "Y034RC1Q027SBEA": "info_processing_equipment", "A679RC1Q027SBEA": "info_proc_equip_and_software",
    "Y006RC1Q027SBEA": "research_and_development", "W790RC1Q027SBEA": "net_domestic_business_investment",
    "GPDI": "gross_private_domestic_investment", "GDP": "gdp",
    "BUSLOANS": "ci_loans", "NCBDBIQ027S": "nonfin_corp_debt_securities_level",
    "BOGZ1FA104104005Q": "nonfin_corp_debt_and_loans_flow",
    "TLPRVCONS": "construction_private_total", "PRMFGCON": "construction_private_manufacturing",
    "PRRESCONS": "construction_private_residential", "NEWORDER": "core_capital_goods_orders",
    "PRS85006092": "nonfarm_business_output_index",
}


def fred_investment():
    cols = {}
    for sid, name in FRED_INV.items():
        p = RAW / "fred_extra" / f"fred_{sid}.csv"
        try:
            download(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", p)
            d = pd.read_csv(p, na_values=".")
            d.columns = ["date", name]
            d["date"] = pd.to_datetime(d["date"])
            cols[name] = d.set_index("date")[name]
        except Exception as e:  # noqa: BLE001
            print("FRED failed", sid, e)
    out = pd.DataFrame(cols)
    out = out[out.index >= "2010-01-01"]
    out.index.name = "date"
    out.to_csv(PROC / "fred_us_investment.csv")
    print("FRED investment series:", list(out.columns))
    return out


# ----------------------------------------------------------------------------- Census
def census_construction():
    p = download("https://www.census.gov/construction/c30/xlsx/privtime.xlsx", RAW / "census" / "privtime.xlsx")
    df = pd.read_excel(p, header=None)
    hdr = [str(v).replace("\n", " ").replace("_x000D_", "").strip() for v in df.iloc[3].values]
    body = df.iloc[4:].copy()
    body.columns = hdr
    body = body[body["Date"].astype(str).str.match(r"[A-Z][a-z]{2}-\d{2}")]
    body["date"] = pd.to_datetime(body["Date"].astype(str).str.replace(r"[pr]$", "", regex=True),
                                  format="%b-%y")
    keep = {"Total Private Construction1": "private_total", "Nonresidential": "nonresidential",
            "Office": "office", "Data center": "data_center", "Commercial (inc. Farm)": "commercial",
            "Health care": "health_care", "Educational": "educational", "Manufacturing": "manufacturing",
            "Power (inc. Gas and Oil)": "power", "Transportation": "transportation",
            "Communication": "communication", "Residential (inc. Improvements)2": "residential"}
    out = body[["date"] + list(keep)].rename(columns=keep).set_index("date").sort_index()
    out = out.apply(pd.to_numeric, errors="coerce")
    out.to_csv(PROC / "census_construction_monthly.csv")
    print("Census construction (USD mn, NSA monthly) latest:\n",
          out[["nonresidential", "office", "data_center", "manufacturing"]].tail(3).to_string())
    return out


if __name__ == "__main__":
    oecd_dac1()
    oecd_dac5()
    oecd_mobilisation()
    world_bank()
    bis()
    fred_investment()
    census_construction()
