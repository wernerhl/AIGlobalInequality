"""First-pass tests of the crowding-out prediction: do AI return shocks raise the cost of
capital for emerging/low-income borrowers?

Outcomes (two-day windows aligned with the event window):
  - returns on EM sovereign bond ETFs (EMB, PCY, EMHY, EMLC) and EM equity (EEM);
    a negative return on an EM bond ETF means a higher yield/spread.
  - changes in ICE BofA EM option-adjusted spreads from FRED (available from Nov 2023).
Controls: 2y Treasury change, VIX change, broad dollar change, SPY return, IEF return.

Specifications
  A. Event days only: outcome on the AI earnings shock (mean CAR of reporting firms).
  B. All days: outcome on the daily AI factor residual (basket return net of FF factors).

Outputs: output/results.md, output/results_eventday.csv, output/results_daily.csv,
         output/fig_capex.png, output/fig_ai_factor_vs_em.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import HYPERSCALERS, OUT, PROC

ETF_OUTCOMES = {"EMB": "EM USD sovereign bond ETF", "PCY": "EM sovereign debt ETF",
                "EMHY": "EM high-yield bond ETF", "EMLC": "EM local-currency bond ETF",
                "EEM": "EM equity ETF"}
OAS_OUTCOMES = {"BAMLEMPBPUBSICRPIOAS": "EM public-sector OAS",
                "BAMLEMUBCRPIUSOAS": "EM corporate plus USD OAS",
                "BAMLEMHYHYLCRPIUSOAS": "EM high-yield USD OAS",
                "BAMLH0A0HYM2": "US high-yield OAS (placebo)"}


def load():
    ret = pd.read_csv(PROC / "returns_daily.csv", index_col=0, parse_dates=True)
    fred = pd.read_csv(PROC / "fred_daily.csv", index_col=0, parse_dates=True)
    shocks = pd.read_csv(PROC / "shocks_daily.csv", index_col=0, parse_dates=True)
    events = pd.read_csv(PROC / "events.csv", parse_dates=["event_day", "period_end"])
    q = pd.read_csv(PROC / "capex_quarterly_with_surprises.csv", parse_dates=["period_end"])
    return ret, fred, shocks, events, q


def two_day(ret, fred):
    """Two-day (t, t+1) outcomes and controls aligned on the trading calendar."""
    idx = ret.index
    f = fred.reindex(idx).ffill(limit=3)
    out = pd.DataFrame(index=idx)
    for t in ETF_OUTCOMES:
        out[f"r2_{t}"] = ret[t] + ret[t].shift(-1)
    for s in OAS_OUTCOMES:
        out[f"d2_{s}"] = f[s].shift(-1) - f[s].shift(1)
    out["d2_DGS2"] = f["DGS2"].shift(-1) - f["DGS2"].shift(1)
    out["d2_VIX"] = f["VIXCLS"].shift(-1) - f["VIXCLS"].shift(1)
    out["d2_USD"] = np.log(f["DTWEXBGS"]).shift(-1) - np.log(f["DTWEXBGS"]).shift(1)
    out["r2_SPY"] = ret["SPY"] + ret["SPY"].shift(-1)
    out["r2_IEF"] = ret["IEF"] + ret["IEF"].shift(-1)
    return out


def one_day(ret, fred):
    idx = ret.index
    f = fred.reindex(idx).ffill(limit=3)
    out = pd.DataFrame(index=idx)
    for t in ETF_OUTCOMES:
        out[f"r_{t}"] = ret[t]
    for s in OAS_OUTCOMES:
        out[f"d_{s}"] = f[s].diff()
    out["d_DGS2"] = f["DGS2"].diff()
    out["d_VIX"] = f["VIXCLS"].diff()
    out["d_USD"] = np.log(f["DTWEXBGS"]).diff()
    out["r_SPY"] = ret["SPY"]
    out["r_IEF"] = ret["IEF"]
    return out


def regress(df, y, x, controls, label, scale=1.0):
    d = df[[y, x] + controls].dropna()
    if len(d) < 20:
        return None
    X = sm.add_constant(d[[x] + controls])
    m = sm.OLS(d[y] * scale, X).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
    return {"outcome": label, "shock": x, "coef": m.params[x], "se": m.bse[x],
            "t": m.tvalues[x], "p": m.pvalues[x], "n": int(m.nobs), "r2": m.rsquared,
            "controls": "yes" if controls else "no"}


def event_day_tests(ret, fred, shocks):
    df = two_day(ret, fred).join(shocks)
    df = df[df["n_reporting"] > 0]
    controls = ["d2_DGS2", "d2_VIX", "d2_USD", "r2_SPY", "r2_IEF"]
    rows = []
    for shock in ["ai_earnings_shock", "hyperscaler_earnings_shock", "capex_surprise_assets",
                  "supplier_implied_capex_shock"]:
        for t, lab in ETF_OUTCOMES.items():
            for c in ([], controls):
                r = regress(df, f"r2_{t}", shock, c, f"{lab} return (%)", scale=100)
                if r:
                    rows.append(r)
        for s, lab in OAS_OUTCOMES.items():
            for c in ([], controls):
                r = regress(df, f"d2_{s}", shock, c, f"{lab} change (bp)", scale=100)
                if r:
                    rows.append(r)
    return pd.DataFrame(rows)


def daily_tests(ret, fred, shocks):
    df = one_day(ret, fred).join(shocks)
    df = df[df.index >= "2022-10-01"]
    controls = ["d_DGS2", "d_VIX", "d_USD", "r_SPY", "r_IEF"]
    rows = []
    for shock in ["ai_ff_resid", "ai_minus_mkt"]:
        for t, lab in ETF_OUTCOMES.items():
            for c in ([], controls):
                r = regress(df, f"r_{t}", shock, c, f"{lab} return (%)", scale=100)
                if r:
                    rows.append(r)
        for s, lab in OAS_OUTCOMES.items():
            for c in ([], controls):
                r = regress(df, f"d_{s}", shock, c, f"{lab} change (bp)", scale=100)
                if r:
                    rows.append(r)
    return pd.DataFrame(rows)


def fmt_table(df):
    d = df.copy()
    d["coef (se)"] = d.apply(lambda r: f"{r['coef']:.3f} ({r['se']:.3f})", axis=1)
    d["t"] = d["t"].round(2)
    d["p"] = d["p"].round(3)
    d["r2"] = d["r2"].round(3)
    return d[["outcome", "shock", "controls", "coef (se)", "t", "p", "n", "r2"]].to_markdown(index=False)


def fig_capex(q):
    h = q[q["ticker"].isin(HYPERSCALERS)].copy()
    h["cq"] = h["period_end"].dt.to_period("Q")
    piv = h.pivot_table(index="cq", columns="ticker", values="capex", aggfunc="sum") / 1e9
    piv = piv[piv.index >= "2019Q1"]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    piv.plot.bar(stacked=True, ax=ax, width=0.85, colormap="tab10")
    ax.set_ylabel("USD billion per quarter")
    ax.set_xlabel("")
    ax.set_title("Capital expenditure of the five hyperscalers (EDGAR 10-Q/10-K, de-cumulated)")
    ax.legend(ncol=5, fontsize=8, frameon=False)
    labels = [str(p) if p.quarter == 1 else "" for p in piv.index]
    ax.set_xticklabels(labels, rotation=0)
    ax.axvline(list(piv.index).index(pd.Period("2022Q4")) + 0.5, color="k", ls="--", lw=0.8)
    ax.text(list(piv.index).index(pd.Period("2022Q4")) + 0.7, ax.get_ylim()[1] * 0.92,
            "ChatGPT release", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_capex.png", dpi=160)
    plt.close(fig)
    ttm = piv.sum(axis=1).rolling(4).sum()
    return piv, ttm


def fig_factor(shocks, fred, ret):
    f = shocks[shocks.index >= "2022-10-01"]
    cum = (1 + f["ai_ff_resid"].fillna(0)).cumprod() - 1
    emb = (1 + ret.loc[f.index, "EMB"].fillna(0)).cumprod() - 1
    oas = fred["BAMLEMPBPUBSICRPIOAS"].reindex(f.index).ffill()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(cum.index, cum * 100, label="AI basket: cumulative FF-adjusted abnormal return (%)")
    ax.plot(emb.index, emb * 100, label="EMB (EM USD sovereign bond ETF) cumulative return (%)")
    ax.set_ylabel("percent")
    ax2 = ax.twinx()
    ax2.plot(oas.index, oas * 100, color="gray", lw=1, label="EM public-sector OAS (bp, right)")
    ax2.set_ylabel("basis points")
    lines = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    labels = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    ax.legend(lines, labels, fontsize=8, frameon=False, loc="upper left")
    ax.set_title("AI abnormal returns and emerging-market bond pricing")
    fig.tight_layout()
    fig.savefig(OUT / "fig_ai_factor_vs_em.png", dpi=160)
    plt.close(fig)


def main():
    ret, fred, shocks, events, q = load()
    ev = event_day_tests(ret, fred, shocks)
    dy = daily_tests(ret, fred, shocks)
    ev.to_csv(OUT / "results_eventday.csv", index=False)
    dy.to_csv(OUT / "results_daily.csv", index=False)
    piv, ttm = fig_capex(q)
    fig_factor(shocks, fred, ret)

    n_ev = int((shocks["n_reporting"] > 0).sum())
    lines = ["# First-pass results: AI return shocks and EM cost of capital", "",
             f"Events: {len(events)} earnings releases by {events['ticker'].nunique()} AI firms, "
             f"{events['event_day'].min().date()} to {events['event_day'].max().date()}, "
             f"on {n_ev} distinct reaction days.", "",
             "Shock units: `ai_earnings_shock` and `hyperscaler_earnings_shock` are mean two-day "
             "abnormal returns (decimal) of the firms reporting that day; `capex_surprise_assets` "
             "is the capex surprise scaled by lagged assets (decimal); `supplier_implied_capex_shock` "
             "is the two-day abnormal return of the AI supply-chain basket on hyperscaler "
             "announcement days (a market-based proxy for the capex-guidance surprise); "
             "`ai_ff_resid` is the daily "
             "AI-basket residual from the FF5+Mom model (decimal); `ai_minus_mkt` is the basket "
             "return minus SPY. Outcomes are in percent (ETF returns) or basis points (OAS). "
             "A coefficient of 0.05 on an ETF-return outcome means a 10% AI abnormal return "
             "moves the ETF by 0.5%. HAC standard errors.", "",
             "Prediction of the crowding-out model: positive AI shocks lower EM bond ETF prices "
             "(negative coefficient) and raise EM spreads (positive coefficient), beyond what US "
             "rates, VIX, the dollar and the market explain. The AI-for-development view predicts "
             "the opposite signs; donor politics predicts zero.", "",
             "## A. Event days (two-day windows around AI earnings releases)", "",
             fmt_table(ev), "",
             "## B. All trading days since October 2022 (daily AI factor)", "",
             fmt_table(dy), "",
             "## Hyperscaler capex (USD bn, trailing four quarters)", "",
             ttm.dropna().iloc[-12:].round(1).to_frame("capex_ttm_bn").to_markdown(), "",
             "Figures: `fig_capex.png`, `fig_ai_factor_vs_em.png`."]
    (OUT / "results.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
