"""Shared settings for the empirical pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "output"
for p in (RAW, PROC, OUT):
    p.mkdir(parents=True, exist_ok=True)

START = "2018-01-01"

# SEC asks for a descriptive User-Agent on automated requests.
SEC_UA = "AIGlobalInequality-research-pipeline (academic use)"

# Hyperscalers: the capex side of the AI boom.
HYPERSCALERS = {
    "MSFT": 789019,
    "GOOGL": 1652044,
    "AMZN": 1018724,
    "META": 1326801,
    "ORCL": 1341439,
}
# Suppliers: the firms whose earnings reveal the realized return to AI capex.
SUPPLIERS = {
    "NVDA": 1045810,
    "AVGO": 1730168,
    "AMD": 2488,
}
AI_FIRMS = {**HYPERSCALERS, **SUPPLIERS}

# Price-only tickers (foreign filers or no clean XBRL capex series).
AI_SUPPLY_CHAIN_EXTRA = ["TSM", "VRT", "ANET", "SMCI", "MU", "ASML"]
MARKET = ["SPY", "QQQ"]
# Emerging / frontier market proxies.
EM_PROXIES = {
    "EEM": "iShares MSCI Emerging Markets (equity)",
    "EMB": "iShares J.P. Morgan USD EM Bond (sovereign, USD)",
    "PCY": "Invesco EM Sovereign Debt (USD)",
    "EMHY": "iShares J.P. Morgan EM High Yield Bond",
    "EMLC": "VanEck J.P. Morgan EM Local Currency Bond",
    "IEF": "iShares 7-10y Treasury (control)",
}
ALL_TICKERS = (list(AI_FIRMS) + AI_SUPPLY_CHAIN_EXTRA + MARKET + list(EM_PROXIES))

FRED_SERIES = {
    "DGS2": "2y Treasury constant maturity",
    "DGS10": "10y Treasury constant maturity",
    "DFII10": "10y TIPS real yield",
    "T10YIE": "10y breakeven inflation",
    "VIXCLS": "CBOE VIX",
    "DTWEXBGS": "Broad trade-weighted dollar",
    "BAMLEMPBPUBSICRPIOAS": "ICE BofA EM public-sector issuers corporate plus OAS",
    "BAMLEMPTPRVICRPIOAS": "ICE BofA EM private-sector issuers corporate plus OAS",
    "BAMLEMHBHYCRPIOAS": "ICE BofA EM high-yield corporate plus OAS",
    "BAMLEMIBHGCRPIOAS": "ICE BofA EM high-grade corporate plus OAS",
    "BAMLEMCBPIOAS": "ICE BofA EM corporate plus OAS",
    "BAMLEMUBCRPIUSOAS": "ICE BofA EM corporate plus USD OAS",
    "BAMLEMHYHYLCRPIUSOAS": "ICE BofA EM high-yield USD OAS",
    "BAMLEMRACRPIASIAOAS": "ICE BofA Asia EM corporate plus OAS",
    "BAMLEMRLCRPILAOAS": "ICE BofA Latin America EM corporate plus OAS",
    "BAMLEMRECRPIEMEAOAS": "ICE BofA EMEA EM corporate plus OAS",
    "BAMLH0A0HYM2": "ICE BofA US high-yield OAS (control)",
    "BAMLC0A0CM": "ICE BofA US corporate OAS (control)",
    "DCOILWTICO": "WTI crude",
    "SOFR": "SOFR",
}
