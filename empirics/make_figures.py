"""Additional figures for the descriptive paper, written to output/ and paper/figures/."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import HYPERSCALERS, OUT, PROC, RAW, ROOT

FIG = ROOT.parent / "paper" / "figures"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "legend.frameon": False})
CUT = pd.Timestamp("2022-11-30")


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=170)
    fig.savefig(FIG / name, dpi=170)
    plt.close(fig)
    print("wrote", name)


# 1. ODA by donor: levels and the 2025 cut ------------------------------------------
def fig_oda_donors():
    d1 = pd.read_csv(PROC / "oecd_dac1_by_donor.csv")
    o = d1[(d1.measure == 1010) & (d1.flow_type == 1140) & (d1.unit == "USD") & (d1.price_base == "Q")]
    p = o.pivot_table(index="year", columns="donor", values="value") / 1e3
    cs = pd.read_csv(OUT / "donor_cross_section_2025.csv", index_col=0)
    names = d1[["donor", "donor_name"]].drop_duplicates().set_index("donor")["donor_name"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    top = ["USA", "DEU", "GBR", "FRA", "JPN", "CAN", "NLD", "ITA", "SWE", "NOR"]
    other = p["DAC"] - p[top].sum(axis=1)
    stack = p[top].copy(); stack["Other DAC"] = other
    stack.columns = [names.get(c, c) for c in top] + ["Other DAC"]
    stack.plot.bar(stacked=True, ax=ax[0], colormap="tab20", width=0.8)
    ax[0].set_title("Net ODA by donor, constant USD bn (2025 preliminary)")
    ax[0].set_xlabel(""); ax[0].tick_params(axis="x", rotation=0); ax[0].legend(fontsize=7, ncol=2)
    big = cs[cs.oda_2024 >= 1.0].sort_values("chg_2025_pct")
    big.index = [names.get(c, c) for c in big.index]
    colors = ["tab:red" if v < 0 else "tab:green" for v in big["chg_2025_pct"]]
    ax[1].barh(big.index, big["chg_2025_pct"], color=colors)
    ax[1].axvline(0, color="k", lw=0.6)
    ax[1].set_title("Real change in net ODA, 2025 vs 2024 (%), donors above USD 1 bn")
    ax[1].tick_params(axis="y", labelsize=7)
    save(fig, "fig_oda_donors.png")


# 2. ODA received by recipient group, 2012-2024 --------------------------------------
def fig_recipient_groups():
    d2 = pd.read_csv(PROC / "oecd_dac2a_by_recipient.csv")
    oda = d2[(d2.donor == "ALLD") & (d2.series == "oda_net")].pivot_table(index="year", columns="recipient", values="value") / 1e3
    us = d2[(d2.donor == "USA") & (d2.series == "oda_net")].pivot_table(index="year", columns="recipient", values="value") / 1e3
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    groups = {"OLICWB": "Low income", "LMICWB": "Lower-middle income", "UMICWB": "Upper-middle income", "UKR": "of which Ukraine", "FSCAC": "Fragile contexts", "F6": "Sub-Saharan Africa"}
    for code, lab in groups.items():
        ax[0].plot(oda.index, oda[code], marker="o", ms=3, label=lab, ls="--" if code == "UKR" else "-")
    ax[0].axvline(2022.9, color="k", ls=":", lw=0.8)
    ax[0].set_title("Net ODA received by recipient group, constant USD bn (DAC2A)")
    ax[0].legend(fontsize=7)
    sh = 100 * us / oda
    for code, lab in {"OLICWB": "Low income", "LMICWB": "Lower-middle income", "F6": "Sub-Saharan Africa", "F97": "Middle East", "DPGC": "All developing"}.items():
        ax[1].plot(sh.index, sh[code], marker="o", ms=3, label=lab)
    ax[1].set_title("United States share of ODA received (%)")
    ax[1].legend(fontsize=7)
    save(fig, "fig_recipient_groups.png")


# 3. Bond stocks outstanding and leverage --------------------------------------------
def fig_bond_stocks():
    ids = pd.read_csv(PROC / "bis_ids_quarterly.csv"); ids["quarter"] = pd.PeriodIndex(ids.quarter, freq="Q")
    p = ids.pivot_table(index="quarter", columns="series", values="OBS_VALUE") / 1e3
    cols = {"intl_debt_sec_outstanding_all_issuers_Intl_organisations": "IFIs / supranationals",
            "intl_debt_sec_outstanding_general_government_EMDE": "EMDE governments",
            "intl_debt_sec_outstanding_all_issuers_EMDE": "EMDE all issuers",
            "intl_debt_sec_outstanding_all_issuers_United_States": "US residents",
            "intl_debt_sec_outstanding_all_issuers_World": "World"}
    o = p[list(cols)].rename(columns=cols)
    base = o.loc[pd.Period("2019Q4")]
    fi = pd.read_csv(PROC / "fred_us_investment.csv", index_col=0, parse_dates=True)
    d = (fi["nonfin_corp_debt_securities_level"] / 1e3).dropna().resample("QE").last()
    g = fi["gdp"].dropna().resample("QE").last()
    lev = (100 * d / g).dropna()
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    for c in o:
        ax[0].plot(o.index.to_timestamp(), 100 * o[c] / base[c], label=c, lw=2 if c == "IFIs / supranationals" else 1.2)
    ax[0].axhline(100, color="k", lw=0.5); ax[0].axvline(CUT, color="k", ls=":", lw=0.8)
    ax[0].set_xlim(pd.Timestamp("2015-01-01"), None)
    ax[0].set_title("International bonds outstanding, 2019Q4 = 100 (BIS)")
    ax[0].legend(fontsize=7)
    ax[1].plot(lev.index, lev, color="tab:gray", label="US nonfinancial corporate bonds / GDP (%)")
    ax[1].axvline(CUT, color="k", ls=":", lw=0.8)
    ax[1].set_xlim(pd.Timestamp("2015-01-01"), None)
    ax[1].set_title("US nonfinancial corporate bonds outstanding, % of GDP (Fed Z.1)")
    ax[1].legend(fontsize=7)
    save(fig, "fig_bond_stocks.png")


# 4. Hyperscaler sources and uses of funds -------------------------------------------
def fig_hyperscaler_funding():
    q = pd.read_csv(PROC / "edgar_quarterly.csv", parse_dates=["period_end"])
    h = q[q.ticker.isin(HYPERSCALERS)].copy(); h["cq"] = h.period_end.dt.to_period("Q")
    g = h.groupby("cq")[["capex", "cfo", "debt_issued", "debt_repaid", "buybacks", "dividends"]].sum(min_count=1) / 1e9
    g = g.loc["2021Q1":]
    x = g.index.to_timestamp()
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    ax[0].bar(x, g["cfo"], width=70, label="Cash from operations", color="tab:green", alpha=0.8)
    ax[0].bar(x, g["debt_issued"], width=70, bottom=g["cfo"], label="Long-term debt issued", color="tab:red", alpha=0.8)
    ax[0].plot(x, g["capex"], color="k", lw=2, marker="o", ms=3, label="Capital expenditure")
    ax[0].plot(x, g["capex"] + g["buybacks"] + g["dividends"], color="k", lw=1, ls="--", label="Capex + buybacks + dividends")
    ax[0].set_title("Hyperscalers: sources and uses, USD bn per quarter")
    ax[0].legend(fontsize=7)
    ax[1].plot(x, g["buybacks"], marker="o", ms=3, label="Share buybacks")
    ax[1].plot(x, g["debt_issued"], marker="o", ms=3, label="Long-term debt issued")
    ax[1].plot(x, g["capex"] - g["cfo"], marker="o", ms=3, label="Capex minus cash from operations")
    ax[1].axhline(0, color="k", lw=0.5)
    ax[1].set_title("The switch to external finance, USD bn per quarter")
    ax[1].legend(fontsize=7)
    save(fig, "fig_hyperscaler_funding.png")


# 5. Mobilised private finance by sector and income group -----------------------------
def fig_mobilisation():
    mob = pd.read_csv(PROC / "oecd_mobilisation.csv")
    meta = pd.read_csv(PROC / "wb_country_meta.csv")
    m = mob[(mob.provider == "ALLD") & (mob.mechanism == "_T") & (mob.flow_type == 100) & (mob.price_base == "Q")]
    sec = m[m.sector.isin([240, 230, 210, 310, 320, 120, 110, 140, 150])].pivot_table(index="year", columns="sector_name", values="value", aggfunc="sum") / 1e3
    allsec = m[m.sector == 1000].groupby("year")["value"].sum() / 1e3
    sec["Other"] = allsec - sec.sum(axis=1)
    inc = m[m.sector == 1000].merge(meta[["iso3", "income_group"]], left_on="recipient", right_on="iso3", how="left")
    inc = inc.pivot_table(index="year", columns="income_group", values="value", aggfunc="sum") / 1e3
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    sec.loc[2015:].plot.bar(stacked=True, ax=ax[0], colormap="tab20", width=0.8)
    ax[0].set_title("Private finance mobilised by official interventions, by sector (USD bn)")
    ax[0].set_xlabel(""); ax[0].tick_params(axis="x", rotation=0); ax[0].legend(fontsize=6, ncol=2)
    inc.loc[2015:, ["Low income", "Lower middle income", "Upper middle income"]].plot.bar(stacked=True, ax=ax[1], width=0.8, color=["tab:red", "tab:orange", "tab:blue"])
    ax[1].set_title("By recipient income group (USD bn; regional/unallocated excluded)")
    ax[1].set_xlabel(""); ax[1].tick_params(axis="x", rotation=0); ax[1].legend(fontsize=7)
    save(fig, "fig_mobilisation.png")


# 6. External finance of low-income countries, % of GNI --------------------------------
def fig_lic_finance():
    wb = pd.read_csv(PROC / "wb_flows.csv")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
    for i, (cid, lab) in enumerate([("XM", "Low-income countries"), ("XN", "Lower-middle-income countries")]):
        x = wb[wb.country_id == cid].pivot_table(index="year", columns="series", values="value")
        ids = wb[wb.country_id == {"XM": "LIC", "XN": "LMC"}[cid]].pivot_table(index="year", columns="series", values="value")
        gni = x["gni"]
        comp = pd.DataFrame({"Net ODA received": x["net_oda_received"], "FDI inflows": x["fdi_inflows"],
                             "Net official debt flows": ids["net_debt_flows_official"], "Net private debt flows": ids["net_debt_flows_private_creditors"],
                             "Portfolio equity": x["portfolio_equity_inflows"]})
        comp = (100 * comp.div(gni, axis=0)).loc[2012:2023]
        comp.index = comp.index.astype(int)
        comp.plot.bar(stacked=True, ax=ax[i], width=0.8)
        rem = (100 * x["remittances"] / gni).loc[2012:2023]
        ax[i].plot(range(len(rem)), rem.values, color="k", marker="o", ms=3, label="Remittances (not stacked)")
        ax[i].set_title(f"{lab}: external finance, % of GNI"); ax[i].set_xlabel(""); ax[i].tick_params(axis="x", rotation=0)
        ax[i].legend(fontsize=7)
    save(fig, "fig_lic_finance.png")


# 7. Event-study coefficient plot -----------------------------------------------------
def fig_event_coefs():
    ev = pd.read_csv(OUT / "results_eventday.csv")
    ev = ev[ev.controls == "yes"]
    outcomes = ["EM USD sovereign bond ETF return (%)", "EM high-yield bond ETF return (%)", "EM local-currency bond ETF return (%)",
                "EM equity ETF return (%)", "EM public-sector OAS change (bp)", "EM high-yield USD OAS change (bp)", "US high-yield OAS (placebo) change (bp)"]
    shocks = {"ai_earnings_shock": ("AI firms' abnormal return", 0.09), "capex_surprise_assets": ("Capex surprise", 0.01),
              "supplier_implied_capex_shock": ("Supplier-implied capex shock", 0.023)}
    fig, ax = plt.subplots(1, 3, figsize=(13, 4.4), sharey=True)
    for k, (shock, (lab, sd)) in enumerate(shocks.items()):
        d = ev[ev.shock == shock].set_index("outcome").reindex(outcomes)
        y = np.arange(len(outcomes))
        ax[k].errorbar(d["coef"] * sd, y, xerr=1.96 * d["se"] * sd, fmt="o", color="tab:blue", capsize=3)
        ax[k].axvline(0, color="k", lw=0.6)
        ax[k].set_title(f"{lab}: effect of a one-s.d. shock")
        ax[k].set_yticks(y); ax[k].set_yticklabels([o.replace(" change", "").replace(" return", "") for o in outcomes], fontsize=7)
        ax[k].set_xlabel("% (ETFs) or bp (spreads), 95% CI")
    save(fig, "fig_event_coefs.png")


# 8. Country sector exposure bars ------------------------------------------------------
def fig_country_sector_exposure():
    cs = pd.read_csv(OUT / "sector_exposure_by_country.csv", index_col=0)
    ex = pd.read_csv(OUT / "country_exposure.csv", index_col=0)
    cs["Health and HIV"] = cs.get("Health_us_cut_pct_gni", 0).fillna(0) + cs.get("Population & reproductive health_us_cut_pct_gni", 0).fillna(0)
    cs["Humanitarian"] = cs.get("Humanitarian_us_cut_pct_gni", 0).fillna(0)
    cs["Government and civil society"] = cs.get("Government & civil society_us_cut_pct_gni", 0).fillna(0)
    cs["Other sectors"] = (ex["exposure_us_cut_pct_gni"].reindex(cs.index) - cs[["Health and HIV", "Humanitarian", "Government and civil society"]].sum(axis=1)).clip(lower=0)
    cs = cs[~cs.index.isin(["MHL", "FSM", "PLW", "TUV"])]
    top = cs.assign(total=ex["exposure_us_cut_pct_gni"].reindex(cs.index)).dropna(subset=["total"]).sort_values("total", ascending=True).tail(25)
    fig, ax = plt.subplots(figsize=(9, 6.5))
    left = np.zeros(len(top))
    for col, color in [("Health and HIV", "tab:blue"), ("Humanitarian", "tab:red"), ("Government and civil society", "tab:orange"), ("Other sectors", "tab:gray")]:
        ax.barh(top["country"], top[col], left=left, color=color, label=col); left += top[col].values
    ax.set_xlabel("Exposure to the 2025 US ODA cut, % of GNI (2024 US disbursements x 57%)")
    ax.set_title("Twenty-five most exposed countries, by sector of the cut")
    ax.legend(fontsize=8, loc="lower right")
    save(fig, "fig_country_sector_exposure.png")


# 9. World map of exposure -------------------------------------------------------------
def fig_map():
    try:
        import geopandas as gpd
    except ImportError:
        print("geopandas not available; skipping map"); return
    world = gpd.read_file(RAW / "naturalearth" / "ne_110m_admin_0_countries.shp")
    ex = pd.read_csv(OUT / "country_exposure.csv", index_col=0)
    iso_col = "ISO_A3_EH" if "ISO_A3_EH" in world else "ISO_A3"
    w = world.merge(ex[["exposure_us_cut_pct_gni", "oda_pct_gni_latest", "left_behind", "market_access"]], left_on=iso_col, right_index=True, how="left")
    w = w[w["NAME"] != "Antarctica"]
    fig, ax = plt.subplots(2, 1, figsize=(11, 9.5))
    w.plot(ax=ax[0], color="#eeeeee", edgecolor="white", lw=0.3)
    w.dropna(subset=["oda_pct_gni_latest"]).plot(column="oda_pct_gni_latest", ax=ax[0], cmap="YlOrRd", vmin=0, vmax=20, legend=True,
                                                  legend_kwds={"label": "Net ODA received, % of GNI (2022-24 avg, capped at 20)", "shrink": 0.6}, edgecolor="white", lw=0.3)
    w[w["left_behind"] == True].boundary.plot(ax=ax[0], color="black", lw=0.8)
    ax[0].set_title("Aid dependence; black outline = ODA above 5% of GNI and no market access (32 countries)")
    ax[0].set_axis_off()
    w.plot(ax=ax[1], color="#eeeeee", edgecolor="white", lw=0.3)
    w.dropna(subset=["exposure_us_cut_pct_gni"]).plot(column="exposure_us_cut_pct_gni", ax=ax[1], cmap="PuRd", vmin=0, vmax=3, legend=True,
                                                       legend_kwds={"label": "Exposure to the 2025 US ODA cut, % of GNI (capped at 3)", "shrink": 0.6}, edgecolor="white", lw=0.3)
    ax[1].set_title("Where the 2025 United States cut lands (2024 US share of ODA x 57%)")
    ax[1].set_axis_off()
    save(fig, "fig_map_exposure.png")


# 10. Sector figure re-laid out in two rows -------------------------------------------
def fig_sectors_tall():
    crs = pd.read_csv(PROC / "oecd_crs_recipient_sector.csv")
    crs = crs[crs.flow_type == "D"]
    from analysis_sectors import SECTORS, composition, GROUPS
    crs["sector_label"] = crs["sector"].map(SECTORS); crs = crs[crs.sector_label.notna()]
    a = crs[(crs.donor == "ALLD") & (crs.recipient == "DPGC")].pivot_table(index="year", columns="sector_label", values="value") / 1e3
    u = crs[(crs.donor == "USA") & (crs.recipient == "DPGC")].pivot_table(index="year", columns="sector_label", values="value") / 1e3
    keep = ["Health", "Population & reproductive health", "Education", "Water & sanitation", "Humanitarian", "Government & civil society",
            "Energy", "Transport", "Agriculture", "Budget support", "Environment", "Refugees in donor"]
    cg = composition(crs, GROUPS)
    fig, ax = plt.subplots(2, 2, figsize=(11, 8.5))
    a[keep].plot.bar(stacked=True, ax=ax[0, 0], colormap="tab20", width=0.8)
    ax[0, 0].set_title("ODA to developing countries by sector, constant USD bn (CRS)"); ax[0, 0].set_xlabel(""); ax[0, 0].tick_params(axis="x", rotation=0); ax[0, 0].legend(fontsize=6, ncol=2)
    last = a.index.max()
    sh = (100 * u.reindex(columns=keep).loc[last] / a[keep].loc[last]).sort_values()
    sh.plot.barh(ax=ax[0, 1], color="tab:red"); ax[0, 1].set_title(f"United States share by sector, {last} (%)")
    lic = crs[(crs.donor == "ALLD") & (crs.recipient == "OLICWB")].pivot_table(index="year", columns="sector_label", values="value") / 1e3
    lic[["Humanitarian", "Health", "Population & reproductive health", "Government & civil society", "Education", "Agriculture", "Energy", "Transport", "Water & sanitation"]].plot(ax=ax[1, 0], marker="o", ms=3)
    ax[1, 0].axvline(2022.9, color="k", ls=":", lw=0.8); ax[1, 0].set_title("Low-income countries: ODA by sector, constant USD bn"); ax[1, 0].legend(fontsize=6, ncol=2)
    cgp = cg[["capital_intensive_chg_vs_2022_pct", "labour_intensive_chg_vs_2022_pct", "humanitarian_chg_vs_2022_pct"]]
    cgp.columns = ["Capital-intensive (energy, transport, water, industry)", "Labour-intensive services (health, education, government)", "Humanitarian"]
    cgp.plot.barh(ax=ax[1, 1]); ax[1, 1].axvline(0, color="k", lw=0.5); ax[1, 1].set_title("Change 2024 vs 2022 by recipient group (%)"); ax[1, 1].legend(fontsize=6); ax[1, 1].set_ylabel("")
    save(fig, "fig_sectors.png")


if __name__ == "__main__":
    fig_oda_donors(); fig_recipient_groups(); fig_bond_stocks(); fig_hyperscaler_funding(); fig_mobilisation()
    fig_lic_finance(); fig_event_coefs(); fig_country_sector_exposure(); fig_map(); fig_sectors_tall()
