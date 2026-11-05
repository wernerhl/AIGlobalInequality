"""Sector disaggregation of ODA received: health, education, water, humanitarian,
infrastructure and so on, by recipient group, region and country (OECD CRS).

Tests the composition prediction of the model (capital-intensive development capital
should contract by more than labour-intensive services when the hurdle rate rises) and
measures sector-level exposure to the 2025 US cut.

Outputs: output/results_sectors.md, output/sector_exposure_by_country.csv,
         output/fig_sectors.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import OUT, PROC

PRE_Y, POST_Y = [2019, 2020, 2021], [2023, 2024]
US_CUT_2025 = 0.567

SECTORS = {120: "Health", 130: "Population & reproductive health", 110: "Education", 140: "Water & sanitation",
           150: "Government & civil society", 160: "Other social", 210: "Transport", 220: "Communications",
           230: "Energy", 240: "Banking & finance", 250: "Business services", 310: "Agriculture",
           320: "Industry & mining", 410: "Environment", 430: "Other multisector", 510: "Budget support",
           520: "Food assistance", 600: "Debt action", 700: "Humanitarian", 910: "Donor admin",
           930: "Refugees in donor", 998: "Unallocated"}
CAPITAL_INTENSIVE = ["Transport", "Energy", "Water & sanitation", "Industry & mining", "Communications"]
LABOUR_INTENSIVE = ["Health", "Population & reproductive health", "Education", "Government & civil society", "Other social"]
GROUPS = {"DPGC": "All developing countries", "OLICWB": "Low income", "LMICWB": "Lower-middle income",
          "UMICWB": "Upper-middle income", "FSCAC": "Fragile contexts", "HIPC": "HIPC", "LLDC": "Landlocked", "SIDS": "Small islands"}
REGIONS = {"F6": "Sub-Saharan Africa", "F4": "Northern Africa", "F97": "Middle East", "S4_S7": "South & Central Asia",
           "S97": "Far East Asia", "A5": "Central America & Caribbean", "A7": "South America", "E": "Europe", "O": "Oceania"}


def load():
    crs = pd.read_csv(PROC / "oecd_crs_recipient_sector.csv")
    crs = crs[crs.flow_type == "D"].copy()
    crs["sector_label"] = crs["sector"].map(SECTORS)
    crs = crs[crs.sector_label.notna()]
    meta = pd.read_csv(PROC / "wb_country_meta.csv")
    expo = pd.read_csv(OUT / "country_exposure.csv", index_col=0)
    return crs, meta, expo


def sector_table(crs, recipient):
    a = crs[(crs.donor == "ALLD") & (crs.recipient == recipient)].pivot_table(index="sector_label", columns="year", values="value") / 1e3
    u = crs[(crs.donor == "USA") & (crs.recipient == recipient)].pivot_table(index="sector_label", columns="year", values="value") / 1e3
    if a.empty:
        return None
    last = int(a.columns.max())
    t = pd.DataFrame({"pre_2019_21": a[PRE_Y].mean(axis=1), "2022": a.get(2022), f"{last}": a[last]})
    t["chg_post_vs_pre_pct"] = 100 * (a[[y for y in POST_Y if y in a]].mean(axis=1) / t["pre_2019_21"] - 1)
    t[f"chg_{last}_vs_2022_pct"] = 100 * (a[last] / a[2022] - 1)
    t["us_share_pct"] = 100 * u.reindex(a.index)[last] / a[last]
    t["us_cut_exposure_usd_bn"] = US_CUT_2025 * u.reindex(a.index)[last]
    t["us_cut_exposure_pct_of_sector"] = 100 * t["us_cut_exposure_usd_bn"] / a[last]
    t["share_of_total_pct"] = 100 * a[last] / a[last].sum()
    return t.sort_values(f"{last}", ascending=False)


def composition(crs, codes):
    rows = []
    for code, name in codes.items():
        t = sector_table(crs, code)
        if t is None:
            continue
        last = [c for c in t.columns if c.isdigit()][-1]
        ci = t.loc[[s for s in CAPITAL_INTENSIVE if s in t.index]]
        li = t.loc[[s for s in LABOUR_INTENSIVE if s in t.index]]
        hum = t.loc[["Humanitarian"]] if "Humanitarian" in t.index else None
        r = {"group": name, "total_last": t[last].sum(),
             "capital_intensive_last": ci[last].sum(), "labour_intensive_last": li[last].sum(),
             "capital_intensive_chg_post_vs_pre_pct": 100 * (ci[last].sum() / ci["pre_2019_21"].sum() - 1),
             "labour_intensive_chg_post_vs_pre_pct": 100 * (li[last].sum() / li["pre_2019_21"].sum() - 1),
             "humanitarian_chg_post_vs_pre_pct": 100 * (hum[last].sum() / hum["pre_2019_21"].sum() - 1) if hum is not None else np.nan,
             "capital_intensive_chg_vs_2022_pct": 100 * (ci[last].sum() / ci["2022"].sum() - 1),
             "labour_intensive_chg_vs_2022_pct": 100 * (li[last].sum() / li["2022"].sum() - 1),
             "humanitarian_chg_vs_2022_pct": 100 * (hum[last].sum() / hum["2022"].sum() - 1) if hum is not None else np.nan,
             "health_us_share_pct": t.loc["Health", "us_share_pct"] if "Health" in t.index else np.nan,
             "humanitarian_us_share_pct": t.loc["Humanitarian", "us_share_pct"] if "Humanitarian" in t.index else np.nan,
             "capital_intensive_us_share_pct": 100 * ci["us_cut_exposure_usd_bn"].sum() / US_CUT_2025 / ci[last].sum(),
             "us_cut_exposure_total_usd_bn": t["us_cut_exposure_usd_bn"].sum(),
             "us_cut_exposure_pct_total": 100 * t["us_cut_exposure_usd_bn"].sum() / t[last].sum()}
        rows.append(r)
    return pd.DataFrame(rows).set_index("group")


def country_sectors(crs, meta, expo):
    iso = set(meta.iso3)
    a = crs[(crs.donor == "ALLD") & crs.recipient.isin(iso) & (crs.year == crs.year.max())]
    u = crs[(crs.donor == "USA") & crs.recipient.isin(iso) & (crs.year == crs.year.max())]
    ap = a.pivot_table(index="recipient", columns="sector_label", values="value") / 1e3
    up = u.pivot_table(index="recipient", columns="sector_label", values="value") / 1e3
    gni = expo["oda_2024_usd_bn"] / (expo["oda_pct_gni_latest"] / 100)   # implied GNI, USD bn
    out = pd.DataFrame(index=ap.index)
    out["country"] = meta.set_index("iso3").loc[ap.index, "country"]
    out["income_group"] = meta.set_index("iso3").loc[ap.index, "income_group"]
    out["region"] = meta.set_index("iso3").loc[ap.index, "region"]
    for s in ["Health", "Population & reproductive health", "Education", "Water & sanitation", "Humanitarian", "Energy", "Transport", "Agriculture", "Government & civil society"]:
        if s in ap:
            out[f"{s}_usd_bn"] = ap[s]
            out[f"{s}_us_share_pct"] = 100 * up.reindex(ap.index).get(s, np.nan) / ap[s]
            out[f"{s}_pct_gni"] = 100 * ap[s] / gni.reindex(ap.index)
            out[f"{s}_us_cut_pct_gni"] = out[f"{s}_pct_gni"] * out[f"{s}_us_share_pct"] / 100 * US_CUT_2025
    out["health_total_us_cut_pct_gni"] = out.get("Health_us_cut_pct_gni", 0).fillna(0) + out.get("Population & reproductive health_us_cut_pct_gni", 0).fillna(0)
    out["left_behind"] = expo["left_behind"].reindex(out.index)
    out["population_mn"] = expo["population_mn"].reindex(out.index)
    out = out.sort_values("health_total_us_cut_pct_gni", ascending=False)
    out.to_csv(OUT / "sector_exposure_by_country.csv")
    return out


def figures(crs, comp_groups, comp_regions):
    a = crs[(crs.donor == "ALLD") & (crs.recipient == "DPGC")].pivot_table(index="year", columns="sector_label", values="value") / 1e3
    u = crs[(crs.donor == "USA") & (crs.recipient == "DPGC")].pivot_table(index="year", columns="sector_label", values="value") / 1e3
    keep = ["Health", "Population & reproductive health", "Education", "Water & sanitation", "Humanitarian", "Government & civil society",
            "Energy", "Transport", "Agriculture", "Banking & finance", "Environment", "Refugees in donor"]
    fig, ax = plt.subplots(1, 3, figsize=(17, 5.2))
    a[keep].plot.bar(stacked=True, ax=ax[0], colormap="tab20", width=0.8)
    ax[0].set_title("ODA disbursements to developing countries by sector, constant USD bn")
    ax[0].legend(fontsize=6, ncol=2, frameon=False); ax[0].tick_params(axis="x", rotation=0)
    last = a.index.max()
    sh = (100 * u.reindex(columns=keep).loc[last] / a[keep].loc[last]).sort_values()
    sh.plot.barh(ax=ax[1], color="tab:red")
    ax[1].set_title(f"US share of ODA by sector, {last} (%)")
    cg = comp_groups[["capital_intensive_chg_vs_2022_pct", "labour_intensive_chg_vs_2022_pct", "humanitarian_chg_vs_2022_pct"]]
    cg.columns = ["Capital-intensive (energy, transport, water, industry)", "Labour-intensive services (health, education, government)", "Humanitarian"]
    cg.plot.barh(ax=ax[2]); ax[2].axvline(0, color="k", lw=0.5)
    ax[2].set_title("Change 2024 vs 2022 by recipient group (%)"); ax[2].legend(fontsize=6, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_sectors.png", dpi=160)
    plt.close(fig)


def main():
    crs, meta, expo = load()
    dpgc = sector_table(crs, "DPGC")
    lic = sector_table(crs, "OLICWB")
    ssa = sector_table(crs, "F6")
    comp_groups = composition(crs, GROUPS)
    comp_regions = composition(crs, REGIONS)
    cs = country_sectors(crs, meta, expo)
    figures(crs, comp_groups, comp_regions)
    last = crs.year.max()
    lb = cs[cs.left_behind == True]
    show = ["country", "income_group", "Health_pct_gni", "Health_us_share_pct", "health_total_us_cut_pct_gni",
            "Humanitarian_pct_gni", "Humanitarian_us_share_pct", "Education_pct_gni", "Water & sanitation_pct_gni", "Energy_pct_gni", "population_mn"]
    show = [c for c in show if c in cs]
    lines = [
        "# ODA by sector: who loses what", "",
        f"OECD CRS, ODA disbursements by purpose sector, constant USD, all official donors (ALLD) and the United States; latest year {last}. "
        f"Exposure to the 2025 US cut = US {last} disbursements x {US_CUT_2025:.0%} (the observed real US ODA change in 2025). Capital-intensive = "
        f"{', '.join(CAPITAL_INTENSIVE)}; labour-intensive services = {', '.join(LABOUR_INTENSIVE)}.", "",
        "## 1. All developing countries, by sector (USD bn)", "", dpgc.round(1).to_markdown(), "",
        "## 2. Low-income countries, by sector (USD bn)", "", lic.round(1).to_markdown(), "",
        "## 3. Sub-Saharan Africa, by sector (USD bn)", "", ssa.round(1).to_markdown(), "",
        "## 4. Composition test by recipient group: capital-intensive vs labour-intensive vs humanitarian", "",
        comp_groups.round(1).to_markdown(), "",
        "## 5. Composition by region", "", comp_regions.round(1).to_markdown(), "",
        f"## 6. Left-behind countries: sector exposure to the US cut (% of GNI), {last}", "",
        lb[show].round(2).to_markdown(), "",
        "## 7. Twenty countries most exposed in health (US health + population ODA cut, % of GNI)", "",
        cs[show].head(20).round(2).to_markdown(), "",
        "Full table: `sector_exposure_by_country.csv`. Figure: `fig_sectors.png`.",
    ]
    (OUT / "results_sectors.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
