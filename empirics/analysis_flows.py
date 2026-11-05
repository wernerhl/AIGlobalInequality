"""Quantities: who is raising money, and where it is going, before and after the AI boom.

A. Bond markets: international debt-securities issuance by international financial
   institutions (IFIs: World Bank group, regional development banks, EIB and other
   supranationals), by emerging/developing-economy (EMDE) residents and governments,
   and by the world; US nonfinancial corporate debt flows; hyperscaler debt issuance.
B. Development finance: ODA (DAC1), ODA by sector (DAC5), private finance mobilised,
   World Bank external-debt flows to low-income countries, BIS cross-border bank
   flows to EMDEs.
C. United States: data-center construction vs other nonresidential construction,
   information-processing investment, and how the hyperscalers fund capex.
D. Quarterly regressions of EMDE financing quantities on the AI factor.

Pre/post split: "pre" = 2019Q1-2022Q3, "post" = 2023Q1-latest (ChatGPT released 30 Nov 2022).
Outputs: output/results_flows.md, output/fig_bond_issuance.png, output/fig_dev_finance.png,
         output/fig_us_investment.png, output/quarterly_panel.csv
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import HYPERSCALERS, OUT, PROC

PRE = (pd.Period("2019Q1"), pd.Period("2022Q3"))
POST = (pd.Period("2023Q1"), pd.Period("2026Q4"))


def qsum(s, freq="Q"):
    return s.groupby(s.index.to_period(freq)).sum(min_count=1)


def pre_post(s, name, unit="USD bn per quarter"):
    s = s.dropna()
    pre = s[(s.index >= PRE[0]) & (s.index <= PRE[1])]
    post = s[(s.index >= POST[0]) & (s.index <= POST[1])]
    return {"series": name, "pre_mean": pre.mean(), "post_mean": post.mean(),
            "change_pct": 100 * (post.mean() / pre.mean() - 1) if pre.mean() else np.nan,
            "pre_n": len(pre), "post_n": len(post), "last_4q_sum": s.iloc[-4:].sum(),
            "latest": str(s.index[-1]), "unit": unit}


# ------------------------------------------------------------------ A. bond markets
def bond_markets():
    ids = pd.read_csv(PROC / "bis_ids_quarterly.csv")
    ids["quarter"] = pd.PeriodIndex(ids["quarter"], freq="Q")
    piv = ids.pivot_table(index="quarter", columns="series", values="OBS_VALUE") / 1e3  # USD bn
    q = pd.read_csv(PROC / "edgar_quarterly.csv", parse_dates=["period_end"])
    h = q[q["ticker"].isin(HYPERSCALERS)].copy()
    h["quarter"] = h["period_end"].dt.to_period("Q")
    hyp = h.groupby("quarter")[["capex", "cfo", "debt_issued", "debt_repaid", "buybacks", "dividends"]].sum(min_count=1) / 1e9
    fi = pd.read_csv(PROC / "fred_us_investment.csv", index_col=0, parse_dates=True)
    usc = fi["nonfin_corp_debt_and_loans_flow"].dropna()
    usc.index = usc.index.to_period("Q")
    usc = usc / 1e3  # FRED Z.1 flows are in USD millions at annual rate -> bn per quarter
    usc = usc / 4

    rows = []
    pick = {
        "intl_debt_sec_gross_issues_all_issuers_Intl_organisations": "IFIs / supranationals: gross international bond issuance",
        "intl_debt_sec_net_issues_all_issuers_Intl_organisations": "IFIs / supranationals: net international bond issuance",
        "intl_debt_sec_gross_issues_all_issuers_EMDE": "EMDE residents: gross international bond issuance",
        "intl_debt_sec_net_issues_all_issuers_EMDE": "EMDE residents: net international bond issuance",
        "intl_debt_sec_gross_issues_general_government_EMDE": "EMDE governments: gross international bond issuance",
        "intl_debt_sec_net_issues_general_government_EMDE": "EMDE governments: net international bond issuance",
        "intl_debt_sec_net_issues_general_government_Africa_MiddleEast": "Africa & Middle East governments: net intl bond issuance",
        "intl_debt_sec_net_issues_nonfin_corps_EMDE": "EMDE nonfinancial corporates: net intl bond issuance",
        "intl_debt_sec_gross_issues_all_issuers_World": "World: gross international bond issuance",
        "intl_debt_sec_net_issues_all_issuers_United_States": "US residents: net international bond issuance",
    }
    for col, name in pick.items():
        if col in piv:
            rows.append(pre_post(piv[col], name))
    rows.append(pre_post(usc, "US nonfinancial corporates: net debt securities + loans (Z.1)"))
    rows.append(pre_post(hyp["debt_issued"], "Hyperscalers (5): long-term debt issued"))
    rows.append(pre_post(hyp["capex"], "Hyperscalers (5): capital expenditure"))
    rows.append(pre_post(hyp["buybacks"], "Hyperscalers (5): share buybacks"))
    tab = pd.DataFrame(rows)

    # IFI share of world issuance, hyperscaler debt relative to IFI issuance
    share = pd.DataFrame({
        "ifi_gross": piv.get("intl_debt_sec_gross_issues_all_issuers_Intl_organisations"),
        "emde_gross": piv.get("intl_debt_sec_gross_issues_all_issuers_EMDE"),
        "emde_gov_gross": piv.get("intl_debt_sec_gross_issues_general_government_EMDE"),
        "world_gross": piv.get("intl_debt_sec_gross_issues_all_issuers_World"),
        "hyp_debt_issued": hyp["debt_issued"], "hyp_capex": hyp["capex"],
    })
    share["ifi_share_world_pct"] = 100 * share["ifi_gross"] / share["world_gross"]
    share["emde_share_world_pct"] = 100 * share["emde_gross"] / share["world_gross"]
    annual = share.groupby(share.index.year).sum(min_count=1)
    annual["ifi_share_world_pct"] = 100 * annual["ifi_gross"] / annual["world_gross"]
    annual["emde_share_world_pct"] = 100 * annual["emde_gross"] / annual["world_gross"]
    annual = annual[annual.index >= 2015]

    fig, ax = plt.subplots(2, 1, figsize=(9, 8), sharex=True)
    s4 = share.rolling(4).sum()
    ax[0].plot(s4.index.to_timestamp(), s4["ifi_gross"], label="IFIs / supranationals, gross intl issuance")
    ax[0].plot(s4.index.to_timestamp(), s4["emde_gross"], label="EMDE residents, gross intl issuance")
    ax[0].plot(s4.index.to_timestamp(), s4["emde_gov_gross"], label="EMDE governments, gross intl issuance")
    ax[0].plot(s4.index.to_timestamp(), s4["hyp_debt_issued"], label="Hyperscalers, LT debt issued", lw=2)
    ax[0].set_ylabel("USD bn, trailing 4 quarters")
    ax[0].axvline(pd.Timestamp("2022-11-30"), color="k", ls="--", lw=0.8)
    ax[0].legend(fontsize=8, frameon=False)
    ax[0].set_title("Bond-market funding: development lenders, developing countries and hyperscalers")
    ax[1].plot(s4.index.to_timestamp(), s4["hyp_capex"], label="Hyperscaler capex", lw=2)
    ax[1].plot(s4.index.to_timestamp(), s4["ifi_gross"], label="IFI gross issuance")
    ax[1].plot(s4.index.to_timestamp(), s4["emde_gross"], label="EMDE gross issuance")
    ax[1].set_ylabel("USD bn, trailing 4 quarters")
    ax[1].axvline(pd.Timestamp("2022-11-30"), color="k", ls="--", lw=0.8)
    ax[1].legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_bond_issuance.png", dpi=160)
    plt.close(fig)
    return tab, annual, share, hyp


# ------------------------------------------------------------ B. development finance
def development_finance():
    d1 = pd.read_csv(PROC / "oecd_dac1_by_donor.csv")
    oda = d1[(d1.measure == 1010) & (d1.flow_type == 1140) & (d1.unit == "USD")]
    oda_real = oda[oda.price_base == "Q"].pivot_table(index="year", columns="donor", values="value") / 1e3
    donors = ["DAC", "USA", "DEU", "GBR", "FRA", "JPN", "CAN", "NLD", "SWE", "NOR"]
    oda_tab = oda_real[[c for c in donors if c in oda_real]].copy()
    oda_tab["DAC_ex_USA"] = oda_tab["DAC"] - oda_tab["USA"]
    hum = d1[d1.measure_name.str.startswith("humanitarian") & (d1.flow_type == 1140) & (d1.unit == "USD") & (d1.price_base == "Q") & (d1.donor == "DAC")]
    hum = hum.pivot_table(index="year", columns="measure_name", values="value") / 1e3 if len(hum) else None
    # Donor cross-section: 2025 vs 2024 and vs 2022-24 average, real
    members = [c for c in oda_real.columns if c not in ("DAC", "DAC_EC", "DACEU", "G7", "WXDAC", "ALLM", "4EU001")
               and oda_real.loc[2024, c] >= 0.5]
    cs = pd.DataFrame({"oda_2024": oda_real.loc[2024, members], "oda_2025": oda_real.loc[2025, members]})
    cs["chg_2025_pct"] = 100 * (cs["oda_2025"] / cs["oda_2024"] - 1)
    cs["avg_2022_24"] = oda_real.loc[2022:2024, members].mean()
    cs["chg_vs_avg_pct"] = 100 * (cs["oda_2025"] / cs["avg_2022_24"] - 1)
    cs = cs.dropna().sort_values("chg_2025_pct")
    cs.to_csv(OUT / "donor_cross_section_2025.csv")

    d5 = pd.read_csv(PROC / "oecd_dac5_sector.csv")
    sec = d5[(d5.donor == "DAC") & (d5.measure == 528) & (d5.price_base == "Q")]
    sec = sec.pivot_table(index="sector_name", columns="year", values="value") / 1e3
    sel = ["All sectors", "Humanitarian aid", "Health", "Education", "Water supply & sanitation",
           "Agriculture", "Energy", "Transport and storage", "General environment protection",
           "Government and civil society", "Banking and financial services", "Industry, mining, construction"]
    sec = sec.loc[[s for s in sel if s in sec.index]]
    yrs = [y for y in (2019, 2021, 2022, 2023, 2024, 2025) if y in sec.columns]
    sec_tab = sec[yrs].copy()
    last = yrs[-1]
    sec_tab[f"chg_{last}_vs_2022_pct"] = 100 * (sec[last] / sec[2022] - 1)

    mob = pd.read_csv(PROC / "oecd_mobilisation.csv")
    m = mob[(mob.provider == "ALLD") & (mob.mechanism == "_T") & (mob.flow_type == 100) & (mob.price_base == "Q")]
    mob_year = m[(m.sector == 1000)].groupby("year")["value"].sum() / 1e3
    mob_sec = m[m.sector.isin([120, 110, 230, 210, 140, 240, 310])].pivot_table(index="sector_name", columns="year", values="value", aggfunc="sum") / 1e3

    wb = pd.read_csv(PROC / "wb_flows.csv")
    wbcols = ["net_oda_received", "fdi_inflows", "net_debt_flows_total", "net_debt_flows_official",
              "net_debt_flows_multilateral", "net_debt_flows_bilateral", "net_debt_flows_private_creditors",
              "net_debt_flows_bonds_ppg", "disbursements_ltd_ext_debt", "remittances", "gross_capital_formation"]
    wb = wb[(wb.year <= 2025)]
    lic = wb[wb.country_id.isin(["LIC", "XM"])].pivot_table(index="year", columns="series", values="value") / 1e9
    lmc = wb[wb.country_id.isin(["LMC", "XN"])].pivot_table(index="year", columns="series", values="value") / 1e9
    lic = lic[[c for c in wbcols if c in lic]]
    lmc = lmc[[c for c in wbcols if c in lmc]]

    lbs = pd.read_csv(PROC / "bis_lbs_quarterly.csv")
    lbs["quarter"] = pd.PeriodIndex(lbs["quarter"], freq="Q")
    lp = lbs.pivot_table(index="quarter", columns="series", values="OBS_VALUE") / 1e3
    flows = {c: n for c, n in {
        "xb_claims_flow_fx_adj_all_sectors_EMDE": "Cross-border bank claims on EMDEs, all sectors (flow)",
        "xb_claims_flow_fx_adj_general_government_EMDE": "Cross-border bank claims on EMDE governments (flow)",
        "xb_claims_flow_fx_adj_all_sectors_Africa_MiddleEast": "Cross-border bank claims on Africa & Middle East (flow)",
        "xb_claims_flow_fx_adj_all_sectors_Asia_Pacific": "Cross-border bank claims on emerging Asia (flow)",
        "xb_claims_flow_fx_adj_all_sectors_LatAm_Caribbean": "Cross-border bank claims on Latin America (flow)",
        "xb_claims_flow_fx_adj_all_sectors_United_States": "Cross-border bank claims on the United States (flow)",
    }.items() if c in lp}
    lbs_tab = pd.DataFrame([pre_post(lp[c], n) for c, n in flows.items()])

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    oda_tab[["DAC", "USA", "DAC_ex_USA"]].plot(ax=ax[0, 0], marker="o")
    ax[0, 0].set_title("Net ODA, constant USD bn (DAC1; 2025 preliminary)")
    sec_plot = sec.loc[[s for s in ["Humanitarian aid", "Health", "Education", "Energy", "Transport and storage", "Water supply & sanitation"] if s in sec.index]].T
    sec_plot.plot(ax=ax[0, 1], marker="o")
    ax[0, 1].set_title("DAC bilateral ODA commitments by sector, constant USD bn (DAC5)")
    ax[0, 1].legend(fontsize=7, frameon=False)
    l4 = lp[[c for c in flows if "EMDE" in c or "Africa" in c]].rolling(4).sum()
    for c in l4:
        ax[1, 0].plot(l4.index.to_timestamp(), l4[c], label=flows[c].replace(" (flow)", ""))
    ax[1, 0].axhline(0, color="k", lw=0.5)
    ax[1, 0].axvline(pd.Timestamp("2022-11-30"), color="k", ls="--", lw=0.8)
    ax[1, 0].set_title("BIS cross-border bank flows, USD bn, trailing 4 quarters")
    ax[1, 0].legend(fontsize=7, frameon=False)
    cols = [c for c in ["net_debt_flows_total", "net_debt_flows_official", "net_debt_flows_private_creditors", "fdi_inflows", "net_oda_received"] if c in lic]
    lic.loc[2012:, cols].plot(ax=ax[1, 1], marker="o")
    ax[1, 1].set_title("Low-income countries: external flows, USD bn (World Bank WDI/IDS)")
    ax[1, 1].legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_dev_finance.png", dpi=160)
    plt.close(fig)
    return oda_tab, hum, cs, sec_tab, mob_year, mob_sec, lic, lmc, lbs_tab, lp


# ------------------------------------------------------------------- C. US side
def us_side(hyp):
    fi = pd.read_csv(PROC / "fred_us_investment.csv", index_col=0, parse_dates=True)
    ce = pd.read_csv(PROC / "census_construction_monthly.csv", index_col=0, parse_dates=True)
    ce_q = ce.resample("QE").sum(min_count=3)
    ce_q.index = ce_q.index.to_period("Q")
    ce_q = ce_q / 1e3
    ce_q["data_center_share_nonres_pct"] = 100 * ce_q["data_center"] / ce_q["nonresidential"]
    ce_q["nonres_ex_datacenter"] = ce_q["nonresidential"] - ce_q["data_center"]
    fq = fi.resample("QE").mean()
    fq.index = fq.index.to_period("Q")
    us = pd.DataFrame(index=ce_q.index)
    us["data_center_constr"] = ce_q["data_center"]
    us["nonres_constr_ex_dc"] = ce_q["nonres_ex_datacenter"]
    us["manufacturing_constr"] = ce_q["manufacturing"]
    us["health_constr"] = ce_q["health_care"]
    us["education_constr"] = ce_q["educational"]
    us["dc_share_nonres_pct"] = ce_q["data_center_share_nonres_pct"]
    for c in ["private_nonres_fixed_investment", "info_processing_equipment", "info_proc_equip_and_software", "nonres_structures", "nonres_equipment", "research_and_development", "gdp"]:
        if c in fq:
            us[c] = fq[c] / 4          # USD bn, SAAR -> per quarter
    if "ci_loans" in fq:
        us["ci_loans"] = fq["ci_loans"]  # USD bn, level
    if "private_nonres_fixed_investment" in us and "info_processing_equipment" in us:
        us["info_proc_share_pnfi_pct"] = 100 * us["info_processing_equipment"] / us["private_nonres_fixed_investment"]
    us["hyp_capex"] = hyp["capex"]
    if "private_nonres_fixed_investment" in us:
        us["hyp_capex_share_pnfi_pct"] = 100 * us["hyp_capex"] / us["private_nonres_fixed_investment"]
        us["pnfi_ex_hyp_capex"] = us["private_nonres_fixed_investment"] - us["hyp_capex"]
        us["hyp_capex_share_gdp_pct"] = 100 * us["hyp_capex"] / us["gdp"] if "gdp" in us else np.nan
    rows = [pre_post(us[c], n) for c, n in {
        "data_center_constr": "US data-center construction (Census)",
        "nonres_constr_ex_dc": "US nonresidential construction ex data centers",
        "manufacturing_constr": "US manufacturing construction", "health_constr": "US health-care construction",
        "education_constr": "US educational construction",
        "private_nonres_fixed_investment": "US private nonresidential fixed investment (BEA, per quarter)",
        "pnfi_ex_hyp_capex": "US private nonres. investment minus hyperscaler capex",
        "info_processing_equipment": "US info-processing equipment investment (BEA, per quarter)",
        "nonres_structures": "US nonresidential structures investment (BEA, per quarter)",
        "research_and_development": "US R&D investment (BEA, per quarter)",
    }.items() if c in us]
    us_tab = pd.DataFrame(rows)

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    u4 = us[["data_center_constr", "nonres_constr_ex_dc", "manufacturing_constr", "health_constr", "education_constr"]].rolling(4).sum()
    for c in u4:
        ax[0].plot(u4.index.to_timestamp(), u4[c] / u4[c].loc[pd.Period("2022Q3")] * 100, label=c.replace("_constr", "").replace("_", " "))
    ax[0].axhline(100, color="k", lw=0.5)
    ax[0].axvline(pd.Timestamp("2022-11-30"), color="k", ls="--", lw=0.8)
    ax[0].set_title("US private construction by type, 2022Q3 = 100 (trailing 4Q)")
    ax[0].legend(fontsize=8, frameon=False)
    if "hyp_capex_share_pnfi_pct" in us:
        ax[1].plot(us.index.to_timestamp(), us["hyp_capex_share_pnfi_pct"], label="Hyperscaler capex / US private nonres. investment (%)")
    if "info_proc_share_pnfi_pct" in us:
        ax[1].plot(us.index.to_timestamp(), us["info_proc_share_pnfi_pct"], label="Info-processing equipment / PNFI (%)")
    ax[1].plot(us.index.to_timestamp(), us["dc_share_nonres_pct"], label="Data centers / nonres. construction (%)")
    ax[1].axvline(pd.Timestamp("2022-11-30"), color="k", ls="--", lw=0.8)
    ax[1].set_title("AI's share of US investment")
    ax[1].legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "fig_us_investment.png", dpi=160)
    plt.close(fig)
    return us, us_tab


# ------------------------------------------------------------ D. quarterly regressions
def quarterly_regressions(lp, share, hyp, us):
    f = pd.read_csv(PROC / "ai_factor_daily.csv", index_col=0, parse_dates=True)
    fred = pd.read_csv(PROC / "fred_daily.csv", index_col=0, parse_dates=True)
    ret = pd.read_csv(PROC / "returns_daily.csv", index_col=0, parse_dates=True)
    panel = pd.DataFrame({
        "ai_factor_q": qsum(f["ai_ff_resid"]), "ai_minus_mkt_q": qsum(f["ai_minus_mkt"]),
        "spy_q": qsum(ret["SPY"]),
        "d_dgs2": fred["DGS2"].resample("QE").last().diff().set_axis(fred["DGS2"].resample("QE").last().index.to_period("Q")),
        "vix_avg": fred["VIXCLS"].resample("QE").mean().set_axis(fred["VIXCLS"].resample("QE").mean().index.to_period("Q")),
        "d_log_usd": np.log(fred["DTWEXBGS"].resample("QE").last()).diff().set_axis(fred["DTWEXBGS"].resample("QE").last().index.to_period("Q")),
    })
    panel["hyp_capex_growth"] = np.log(hyp["capex"]).diff(4)
    panel["hyp_debt_issued"] = hyp["debt_issued"]
    for c in lp:
        if "flow" in c:
            panel[c] = lp[c]
    for c in ["ifi_gross", "emde_gross", "emde_gov_gross", "world_gross"]:
        panel[c] = share[c]
    panel["xb_claims_flow_EMDE_scaled_pct"] = 100 * lp["xb_claims_flow_fx_adj_all_sectors_EMDE"] / lp["xb_claims_stock_all_sectors_EMDE"].shift(1)
    panel["emde_gross_share_world_pct"] = share["emde_share_world_pct"]
    panel["ifi_gross_share_world_pct"] = share["ifi_share_world_pct"]
    panel["data_center_constr"] = us["data_center_constr"]
    panel["nonres_constr_ex_dc"] = us["nonres_constr_ex_dc"]
    panel = panel[panel.index >= "2015Q1"]
    panel.to_csv(OUT / "quarterly_panel.csv")

    rows = []
    outcomes = {
        "xb_claims_flow_EMDE_scaled_pct": "BIS cross-border bank flow to EMDEs, % of lagged stock",
        "xb_claims_flow_fx_adj_general_government_EMDE": "BIS cross-border bank flow to EMDE governments, USD bn",
        "emde_gross": "EMDE gross international bond issuance, USD bn",
        "emde_gov_gross": "EMDE government gross international bond issuance, USD bn",
        "ifi_gross": "IFI gross international bond issuance, USD bn",
        "emde_gross_share_world_pct": "EMDE share of world gross issuance, %",
        "ifi_gross_share_world_pct": "IFI share of world gross issuance, %",
    }
    controls = ["spy_q", "d_dgs2", "vix_avg", "d_log_usd"]
    for shock in ["ai_factor_q", "ai_minus_mkt_q", "hyp_capex_growth"]:
        for y, lab in outcomes.items():
            for c in ([], controls):
                d = panel[[y, shock] + c].dropna()
                if len(d) < 16:
                    continue
                m = sm.OLS(d[y], sm.add_constant(d[[shock] + c])).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
                rows.append({"outcome": lab, "shock": shock, "controls": "yes" if c else "no",
                             "coef": m.params[shock], "se": m.bse[shock], "t": m.tvalues[shock],
                             "p": m.pvalues[shock], "n": int(m.nobs), "r2": m.rsquared})
    return pd.DataFrame(rows), panel


def md(df, floatfmt=".1f"):
    return df.to_markdown(floatfmt=floatfmt)


def main():
    tab, annual, share, hyp = bond_markets()
    oda_tab, hum, cs, sec_tab, mob_year, mob_sec, lic, lmc, lbs_tab, lp = development_finance()
    us, us_tab = us_side(hyp)
    reg, panel = quarterly_regressions(lp, share, hyp, us)
    reg.to_csv(OUT / "results_quarterly.csv", index=False)

    def pp(df):
        d = df.copy()
        for c in ["pre_mean", "post_mean", "last_4q_sum"]:
            d[c] = d[c].round(1)
        d["change_pct"] = d["change_pct"].round(0)
        return d[["series", "pre_mean", "post_mean", "change_pct", "last_4q_sum", "latest"]].to_markdown(index=False)

    r = reg.copy()
    r["coef (se)"] = r.apply(lambda x: f"{x['coef']:.3f} ({x['se']:.3f})", axis=1)
    r["t"] = r["t"].round(2); r["p"] = r["p"].round(3); r["r2"] = r["r2"].round(2)

    lines = [
        "# Financing quantities before and after the AI boom", "",
        "Pre = 2019Q1-2022Q3 average, Post = 2023Q1-latest average (quarterly, USD bn unless noted). "
        "ChatGPT was released on 30 Nov 2022. BIS international debt securities = bonds issued outside the "
        "issuer's domestic market (the market in which IFIs, EM sovereigns and the hyperscalers all fund). "
        "BEA investment series are seasonally adjusted annual rates divided by four.", "",
        "## A. Bond markets: who is raising money", "", pp(tab), "",
        "### Annual gross international issuance (USD bn) and shares", "",
        md(annual[["ifi_gross", "emde_gross", "emde_gov_gross", "world_gross", "hyp_debt_issued", "hyp_capex", "ifi_share_world_pct", "emde_share_world_pct"]]), "",
        "## B. Development finance", "",
        "### Net ODA, constant prices, USD bn (OECD DAC1; 2025 preliminary)", "", md(oda_tab), "",
        "### Donor cross-section: real ODA change in 2025 (%)", "", md(cs.round(1)), "",
        "### DAC bilateral ODA commitments by sector, constant USD bn (DAC5)", "", md(sec_tab), "",
        "### Private finance mobilised by official development finance, constant USD bn (OECD)", "",
        md(mob_year.to_frame("mobilised_total").T), "", md(mob_sec), "",
        "### Low-income countries: external flows, USD bn (World Bank WDI / IDS)", "", md(lic.loc[2015:].round(1)), "",
        "### Lower-middle-income countries: external flows, USD bn", "", md(lmc.loc[2015:].round(1)), "",
        "### BIS cross-border bank flows (FX- and break-adjusted), USD bn per quarter", "", pp(lbs_tab), "",
        "## C. United States: non-AI investment inside the same pool", "", pp(us_tab), "",
        "### Hyperscaler funding of capex, USD bn per quarter (EDGAR)", "",
        md(hyp.loc["2022Q1":].round(1)), "",
        "## D. Quarterly regressions of financing quantities on the AI factor", "",
        "`ai_factor_q` = quarterly sum of the daily AI-basket residual from the FF5+Mom model; "
        "`ai_minus_mkt_q` = quarterly sum of basket return minus SPY; `hyp_capex_growth` = 4-quarter log "
        "change in hyperscaler capex. Controls: SPY quarterly return, change in 2y Treasury, mean VIX, "
        "change in log broad dollar. HAC standard errors. Crowding-out predicts negative coefficients on "
        "EMDE and IFI quantities.", "",
        r[["outcome", "shock", "controls", "coef (se)", "t", "p", "n", "r2"]].to_markdown(index=False), "",
        "Figures: `fig_bond_issuance.png`, `fig_dev_finance.png`, `fig_us_investment.png`. Panel: `quarterly_panel.csv`.",
    ]
    if hum is not None:
        lines[lines.index("### Donor cross-section: real ODA change in 2025 (%)"):lines.index("### Donor cross-section: real ODA change in 2025 (%)")] = [
            "### DAC humanitarian aid, constant USD bn", "", md(hum), ""]
    (OUT / "results_flows.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
