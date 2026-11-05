"""Who is left behind, and how: regional and country-level disaggregation.

Questions
  1. Regions: how did ODA received, cross-border bank flows and international bond
     issuance change by region after the AI boom (pre = 2019-2021 avg, post = 2023-latest)?
  2. Countries: for each developing country, the composition of external finance (ODA,
     FDI, private debt, official debt, remittances, % of GNI), dependence on ODA, on US
     ODA in particular, and whether the country has market access (bond issuance or
     positive net private flows 2022-24).
  3. Exposure: countries with high ODA dependence, high US share and no market access
     are the ones that cannot substitute grants with market finance when the pool
     reprices; the 2025 US cut (-57% real) is applied to each recipient's 2024 US share
     to give an exposure measure (a projection, not observed 2025 receipts).

Outputs: output/results_regions.md, output/country_exposure.csv,
         output/fig_regions.png, output/fig_country_exposure.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import OUT, PROC

PRE_Y, POST_Y = [2019, 2020, 2021], [2023, 2024]
US_CUT_2025 = 0.567   # real change in US ODA 2025 vs 2024 (DAC1 preliminary)

REGIONS_DAC = {"F6": "Sub-Saharan Africa", "F4": "Northern Africa", "F97": "Middle East",
               "S4_S7": "South & Central Asia", "S97": "Far East Asia", "A5": "Central America & Caribbean",
               "A7": "South America", "E": "Europe", "O": "Oceania"}
GROUPS_DAC = {"DPGC": "All developing countries", "OLICWB": "Low income (WB)", "LMICWB": "Lower-middle income (WB)",
              "UMICWB": "Upper-middle income (WB)", "HIPC": "Heavily indebted poor countries",
              "FSCAC": "Fragile contexts", "LLDC": "Landlocked developing", "SIDS": "Small island developing"}


def load():
    d2 = pd.read_csv(PROC / "oecd_dac2a_by_recipient.csv")
    wb = pd.read_csv(PROC / "wb_country_panel.csv")
    meta = pd.read_csv(PROC / "wb_country_meta.csv")
    mob = pd.read_csv(PROC / "oecd_mobilisation.csv")
    lbs = pd.read_csv(PROC / "bis_lbs_quarterly.csv")
    ids = pd.read_csv(PROC / "bis_ids_quarterly.csv")
    return d2, wb, meta, mob, lbs, ids


def regions(d2, lbs, ids, mob, meta):
    oda = d2[(d2.donor == "ALLD") & (d2.series == "oda_net")].pivot_table(index="recipient", columns="year", values="value") / 1e3
    us = d2[(d2.donor == "USA") & (d2.series == "oda_net")].pivot_table(index="recipient", columns="year", values="value") / 1e3
    hum = d2[(d2.donor == "ALLD") & (d2.series == "humanitarian")].pivot_table(index="recipient", columns="year", values="value") / 1e3

    def tab(codes):
        rows = []
        for code, name in codes.items():
            if code not in oda.index:
                continue
            pre, post = oda.loc[code, PRE_Y].mean(), oda.loc[code, POST_Y].mean()
            r = {"group": name, "oda_pre_2019_21": pre, "oda_post_2023_24": post, "oda_2024": oda.loc[code, 2024],
                 "chg_post_vs_pre_pct": 100 * (post / pre - 1), "chg_2024_vs_2022_pct": 100 * (oda.loc[code, 2024] / oda.loc[code, 2022] - 1),
                 "us_share_2024_pct": 100 * us.loc[code, 2024] / oda.loc[code, 2024] if code in us.index else np.nan,
                 "humanitarian_share_2024_pct": 100 * hum.loc[code, 2024] / oda.loc[code, 2024] if code in hum.index else np.nan}
            r["exposure_to_us_cut_usd_bn"] = US_CUT_2025 * us.loc[code, 2024] if code in us.index else np.nan
            r["exposure_to_us_cut_pct_of_oda"] = 100 * r["exposure_to_us_cut_usd_bn"] / r["oda_2024"]
            rows.append(r)
        return pd.DataFrame(rows).set_index("group")
    reg_oda, grp_oda = tab(REGIONS_DAC), tab(GROUPS_DAC)

    lbs["quarter"] = pd.PeriodIndex(lbs.quarter, freq="Q")
    ids["quarter"] = pd.PeriodIndex(ids.quarter, freq="Q")
    lp = lbs.pivot_table(index="quarter", columns="series", values="OBS_VALUE") / 1e3
    ip = ids.pivot_table(index="quarter", columns="series", values="OBS_VALUE") / 1e3
    pre_q = (pd.Period("2019Q1"), pd.Period("2021Q4"))
    post_q = (pd.Period("2023Q1"), pd.Period("2026Q4"))
    rows = []
    for reg, label in {"Africa_MiddleEast": "Africa & Middle East", "Asia_Pacific": "Emerging Asia-Pacific",
                       "LatAm_Caribbean": "Latin America & Caribbean", "Emerging_Europe": "Emerging Europe", "EMDE": "All EMDEs"}.items():
        r = {"region": label}
        for col, name in [(f"xb_claims_flow_fx_adj_all_sectors_{reg}", "bank_flow_all"),
                          (f"xb_claims_flow_fx_adj_general_government_{reg}", "bank_flow_govt"),
                          (f"intl_debt_sec_gross_issues_all_issuers_{reg}", "bond_gross_all"),
                          (f"intl_debt_sec_net_issues_all_issuers_{reg}", "bond_net_all"),
                          (f"intl_debt_sec_net_issues_general_government_{reg}", "bond_net_govt"),
                          (f"intl_debt_sec_gross_issues_general_government_{reg}", "bond_gross_govt")]:
            src = lp if col in lp else ip
            if col not in src:
                continue
            s = src[col]
            r[f"{name}_pre"] = s[(s.index >= pre_q[0]) & (s.index <= pre_q[1])].mean()
            r[f"{name}_post"] = s[(s.index >= post_q[0]) & (s.index <= post_q[1])].mean()
        stock = lp.get(f"xb_claims_stock_all_sectors_{reg}")
        if stock is not None:
            r["bank_stock_2019Q4"] = stock.get(pd.Period("2019Q4"))
            r["bank_stock_latest"] = stock.dropna().iloc[-1]
        rows.append(r)
    mkt = pd.DataFrame(rows).set_index("region")

    m = mob[(mob.provider == "ALLD") & (mob.mechanism == "_T") & (mob.flow_type == 100) & (mob.price_base == "Q") & (mob.sector == 1000)]
    m = m.merge(meta[["iso3", "region", "income_group"]], left_on="recipient", right_on="iso3", how="left")
    mob_reg = m.pivot_table(index="region", columns="year", values="value", aggfunc="sum") / 1e3
    mob_inc = m.pivot_table(index="income_group", columns="year", values="value", aggfunc="sum") / 1e3
    return reg_oda, grp_oda, mkt, mob_reg, mob_inc, oda, us, hum


def countries(d2, wb, meta, mob, oda, us, hum):
    p = wb.pivot_table(index=["iso3", "year"], columns="series", values="value").reset_index()
    p = p.merge(meta, on="iso3")
    dev = p[p.income_group.isin(["Low income", "Lower middle income", "Upper middle income"])].copy()

    def avg(df, cols, years):
        return df[df.year.isin(years)].groupby("iso3")[cols].mean()
    flows = ["net_oda_received", "fdi_inflows", "net_debt_flows_private", "net_debt_flows_official",
             "net_debt_flows_bonds_ppg", "net_debt_flows_bonds_png", "remittances", "portfolio_equity_inflows"]
    pre = avg(dev, flows + ["gni"], PRE_Y)
    post = avg(dev, flows + ["gni"], [2022, 2023, 2024])
    c = meta.set_index("iso3").loc[pre.index, ["country", "region", "income_group"]].copy()
    for f in flows:
        c[f"{f}_pre_pct_gni"] = 100 * pre[f] / pre["gni"]
        c[f"{f}_post_pct_gni"] = 100 * post[f] / post["gni"]
    c["ext_finance_pre_pct_gni"] = sum(c[f"{f}_pre_pct_gni"].fillna(0) for f in ["net_oda_received", "fdi_inflows", "net_debt_flows_private", "net_debt_flows_official", "portfolio_equity_inflows"])
    c["ext_finance_post_pct_gni"] = sum(c[f"{f}_post_pct_gni"].fillna(0) for f in ["net_oda_received", "fdi_inflows", "net_debt_flows_private", "net_debt_flows_official", "portfolio_equity_inflows"])
    c["chg_ext_finance_pp_gni"] = c["ext_finance_post_pct_gni"] - c["ext_finance_pre_pct_gni"]
    c["chg_oda_pp_gni"] = c["net_oda_received_post_pct_gni"] - c["net_oda_received_pre_pct_gni"]
    c["chg_private_pp_gni"] = (c["fdi_inflows_post_pct_gni"].fillna(0) + c["net_debt_flows_private_post_pct_gni"].fillna(0) + c["portfolio_equity_inflows_post_pct_gni"].fillna(0)) \
        - (c["fdi_inflows_pre_pct_gni"].fillna(0) + c["net_debt_flows_private_pre_pct_gni"].fillna(0) + c["portfolio_equity_inflows_pre_pct_gni"].fillna(0))
    # Market access: any PPG/PNG bond issuance or positive private net debt flows in 2022-24
    recent = dev[dev.year.isin([2022, 2023, 2024])].groupby("iso3")
    c["bond_access"] = (recent["net_debt_flows_bonds_ppg"].max() > 0) | (recent["net_debt_flows_bonds_png"].max() > 0)
    c["private_net_positive"] = recent["net_debt_flows_private"].mean() > 0
    c["market_access"] = c["bond_access"].fillna(False) | c["private_net_positive"].fillna(False)
    # OECD recipient-level ODA and US share (DAC2A, constant USD)
    c["oda_2024_usd_bn"] = oda.reindex(c.index)[2024]
    c["oda_chg_2024_vs_2022_pct"] = 100 * (oda.reindex(c.index)[2024] / oda.reindex(c.index)[2022] - 1)
    c["us_share_oda_2024_pct"] = 100 * us.reindex(c.index)[2024] / oda.reindex(c.index)[2024]
    c["humanitarian_share_2024_pct"] = 100 * hum.reindex(c.index)[2024] / oda.reindex(c.index)[2024]
    c["oda_pct_gni_latest"] = dev[dev.year.isin([2022, 2023, 2024])].groupby("iso3")["net_oda_pct_gni"].mean()
    c["exposure_us_cut_pct_gni"] = c["oda_pct_gni_latest"] * c["us_share_oda_2024_pct"] / 100 * US_CUT_2025
    c["population_mn"] = dev[dev.year == 2024].set_index("iso3")["population"].reindex(c.index) / 1e6
    c["gdp_per_capita"] = dev[dev.year == 2024].set_index("iso3")["gdp_per_capita"].reindex(c.index)
    m = mob[(mob.provider == "ALLD") & (mob.mechanism == "_T") & (mob.flow_type == 100) & (mob.price_base == "Q") & (mob.sector == 1000)]
    mb = m.pivot_table(index="recipient", columns="year", values="value", aggfunc="sum") / 1e3
    c["mobilised_2022_24_usd_bn_per_yr"] = mb.reindex(c.index)[[2022, 2023, 2024]].mean(axis=1)
    c["mobilised_pct_gni"] = 100 * c["mobilised_2022_24_usd_bn_per_yr"] * 1e9 / post["gni"]
    # Left-behind classification
    c["aid_dependent"] = c["oda_pct_gni_latest"] >= 5
    c["left_behind"] = c["aid_dependent"] & ~c["market_access"]
    c["left_behind_score"] = (c["oda_pct_gni_latest"].rank(pct=True).fillna(0) + c["us_share_oda_2024_pct"].rank(pct=True).fillna(0)
                              + (~c["market_access"]).astype(float) + (c["mobilised_pct_gni"].fillna(0) < 0.5).astype(float))
    c = c.sort_values("exposure_us_cut_pct_gni", ascending=False)
    c.to_csv(OUT / "country_exposure.csv")
    return c


def summarize(c):
    g = c.groupby(["income_group"]).agg(n=("country", "size"), pop_mn=("population_mn", "sum"),
                                        oda_pct_gni=("oda_pct_gni_latest", "median"), us_share=("us_share_oda_2024_pct", "median"),
                                        market_access_share=("market_access", "mean"), left_behind_n=("left_behind", "sum"),
                                        left_behind_pop_mn=("population_mn", lambda s: s[c.loc[s.index, "left_behind"]].sum()),
                                        chg_ext_fin_pp=("chg_ext_finance_pp_gni", "median"), chg_oda_pp=("chg_oda_pp_gni", "median"),
                                        chg_private_pp=("chg_private_pp_gni", "median"), exposure_us_cut_pct_gni=("exposure_us_cut_pct_gni", "median"))
    r = c.groupby(["region"]).agg(n=("country", "size"), pop_mn=("population_mn", "sum"),
                                  oda_pct_gni=("oda_pct_gni_latest", "median"), us_share=("us_share_oda_2024_pct", "median"),
                                  market_access_share=("market_access", "mean"), left_behind_n=("left_behind", "sum"),
                                  left_behind_pop_mn=("population_mn", lambda s: s[c.loc[s.index, "left_behind"]].sum()),
                                  chg_ext_fin_pp=("chg_ext_finance_pp_gni", "median"), chg_oda_pp=("chg_oda_pp_gni", "median"),
                                  chg_private_pp=("chg_private_pp_gni", "median"), exposure_us_cut_pct_gni=("exposure_us_cut_pct_gni", "median"))
    return g, r


def figures(c, reg_oda, mkt):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    d = c.dropna(subset=["oda_pct_gni_latest", "us_share_oda_2024_pct", "population_mn"])
    d = d[(d.oda_2024_usd_bn > 0) & (d.us_share_oda_2024_pct.between(0, 100)) & (d.oda_pct_gni_latest >= 0)]
    colors = {"Sub-Saharan Africa": "tab:red", "South Asia": "tab:orange", "Middle East, North Africa, Afghanistan & Pakistan": "tab:brown",
              "East Asia & Pacific": "tab:green", "Latin America & Caribbean": "tab:blue", "Europe & Central Asia": "tab:gray"}
    for reg, grp in d.groupby("region"):
        ax[0].scatter(grp["us_share_oda_2024_pct"], grp["oda_pct_gni_latest"], s=np.sqrt(grp["population_mn"]) * 6 + 5,
                      alpha=0.6, label=reg.split(",")[0], color=colors.get(reg, "k"),
                      edgecolor=np.where(grp["market_access"], "none", "k"))
    for i, r in d[(d.oda_pct_gni_latest > 8) | (d.us_share_oda_2024_pct > 45)].iterrows():
        ax[0].annotate(i, (r["us_share_oda_2024_pct"], r["oda_pct_gni_latest"]), fontsize=6)
    ax[0].set_xlabel("US share of net ODA received, 2024 (%)")
    ax[0].set_ylabel("Net ODA received, % of GNI (2022-24 avg)")
    ax[0].set_title("Aid dependence and exposure to the US cut (black edge = no market access)")
    ax[0].legend(fontsize=7, frameon=False)
    rb = reg_oda.drop(index=["Europe"], errors="ignore")  # Europe = Ukraine (+483%), off scale
    rb[["chg_post_vs_pre_pct", "chg_2024_vs_2022_pct", "exposure_to_us_cut_pct_of_oda"]].plot.barh(ax=ax[1])
    ax[1].axvline(0, color="k", lw=0.5)
    ax[1].set_title("ODA received by region (excl. Europe/Ukraine): change (%) and US-cut exposure (% of 2024 ODA)", fontsize=9)
    ax[1].legend(["2023-24 vs 2019-21", "2024 vs 2022", "US cut exposure"], fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_country_exposure.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    b = mkt[["bank_flow_all_pre", "bank_flow_all_post"]].rename(columns={"bank_flow_all_pre": "2019-21", "bank_flow_all_post": "2023-26"})
    b.plot.bar(ax=ax[0]); ax[0].axhline(0, color="k", lw=0.5)
    ax[0].set_title("BIS cross-border bank flows, USD bn per quarter"); ax[0].tick_params(axis="x", rotation=20)
    g = mkt[["bond_gross_govt_pre", "bond_gross_govt_post"]].rename(columns={"bond_gross_govt_pre": "2019-21", "bond_gross_govt_post": "2023-26"})
    g.plot.bar(ax=ax[1]); ax[1].set_title("Government international bond issuance (gross), USD bn per quarter"); ax[1].tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(OUT / "fig_regions.png", dpi=160)
    plt.close(fig)


def main():
    d2, wb, meta, mob, lbs, ids = load()
    reg_oda, grp_oda, mkt, mob_reg, mob_inc, oda, us, hum = regions(d2, lbs, ids, mob, meta)
    c = countries(d2, wb, meta, mob, oda, us, hum)
    g, r = summarize(c)
    figures(c, reg_oda, mkt)
    lb = c[c.left_behind].sort_values("exposure_us_cut_pct_gni", ascending=False)
    top = c.head(25)
    show = ["country", "region", "income_group", "oda_pct_gni_latest", "us_share_oda_2024_pct", "humanitarian_share_2024_pct",
            "exposure_us_cut_pct_gni", "market_access", "mobilised_pct_gni", "chg_oda_pp_gni", "chg_private_pp_gni", "population_mn"]
    lines = [
        "# Who is left behind: regional and country disaggregation", "",
        f"Pre = {PRE_Y[0]}-{PRE_Y[-1]} average, post = {POST_Y[0]}-{POST_Y[-1]} average. ODA received is from OECD DAC2A "
        "(all official donors, constant USD); recipient-level data end in 2024, so exposure to the 2025 collapse is "
        f"computed as each recipient's 2024 US share times the observed real US cut ({US_CUT_2025:.0%}). 'Market access' = any "
        "PPG or PNG bond issuance, or positive net private debt flows, in 2022-24 (World Bank IDS). 'Left behind' = net ODA "
        ">= 5% of GNI and no market access.", "",
        "## 1. ODA received by region (USD bn, constant)", "", reg_oda.round(1).to_markdown(), "",
        "## 2. ODA received by group", "", grp_oda.round(1).to_markdown(), "",
        "## 3. Market finance by region (BIS), USD bn per quarter", "", mkt.round(1).to_markdown(), "",
        "## 4. Private finance mobilised by official interventions, by recipient region / income group (USD bn, constant)", "",
        mob_reg[[y for y in range(2017, 2025) if y in mob_reg]].round(1).to_markdown(), "", mob_inc[[y for y in range(2017, 2025) if y in mob_inc]].round(1).to_markdown(), "",
        "## 5. Country summary by income group", "", g.round(2).to_markdown(), "",
        "## 6. Country summary by region", "", r.round(2).to_markdown(), "",
        f"## 7. Left-behind countries ({len(lb)}; ODA >= 5% of GNI and no market access), sorted by exposure to the US cut (% of GNI)", "",
        lb[show].round(2).to_markdown(), "",
        "## 8. Twenty-five most exposed developing countries (US cut as % of GNI)", "", top[show].round(2).to_markdown(), "",
        "Caveats: 'Europe' and the upper-middle-income jump are Ukraine. The Marshall Islands, Micronesia and Palau "
        "receive US Compact of Free Association funding counted as ODA, which the 2025 cut did not touch, so their "
        "exposure is overstated. Syria and Afghanistan are humanitarian cases where the ODA/GNI ratio reflects a collapsed GNI.", "",
        "Full table: `country_exposure.csv`. Figures: `fig_country_exposure.png`, `fig_regions.png`.",
    ]
    (OUT / "results_regions.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
