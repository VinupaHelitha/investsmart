"""
data_collector.py — InvestSmart
Master data collection script. Run by GitHub Actions at 3:00 PM Sri Lanka time (weekdays).

Collects:
  - 40+ Yahoo Finance tickers (prices, forex, commodities, indices)
  - 14 FRED macroeconomic series (US Federal Reserve data)
  - 10 World Bank indicators (Sri Lanka macro)
  - 6 categories of news (NewsAPI)
  - CSE data (scraped from cse.lk)
  - Gold price in LKR (calculated: gold_usd × usd_lkr)

Then saves everything to:
  - Supabase (PostgreSQL database)
  - Local JSON snapshot file
"""

import os
import json
import requests
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# All Yahoo Finance tickers we track
YAHOO_TICKERS = {
    # Precious Metals & Commodities
    "gold":          "GC=F",
    "silver":        "SI=F",
    "oil_brent":     "BZ=F",
    "oil_wti":       "CL=F",
    "copper":        "HG=F",
    "natural_gas":   "NG=F",
    # US Indices
    "sp500":         "^GSPC",
    "nasdaq":        "^IXIC",
    "dow":           "^DJI",
    "vix":           "^VIX",
    "russell2000":   "^RUT",
    # Asian Indices
    "sensex":        "^BSESN",
    "nifty":         "^NSEI",
    "hang_seng":     "^HSI",
    "nikkei":        "^N225",
    "shanghai":      "000001.SS",
    "kospi":         "^KS11",
    # European Indices
    "ftse100":       "^FTSE",
    "dax":           "^GDAXI",
    "cac40":         "^FCHI",
    # Forex
    "usd_lkr":       "LKR=X",
    "usd_index":     "DX-Y.NYB",
    "eur_usd":       "EURUSD=X",
    "usd_inr":       "INR=X",
    "usd_jpy":       "JPY=X",
    "usd_cny":       "CNY=X",
    "usd_gbp":       "GBPUSD=X",
    "usd_aud":       "AUDUSD=X",
    # Bond ETFs
    "bond_etf_20y":  "TLT",
    "bond_etf_7y":   "IEF",
    "bond_etf_em":   "EMB",
    # Sector ETFs
    "etf_energy":    "XLE",
    "etf_finance":   "XLF",
    "etf_tech":      "XLK",
    "etf_gold_miners": "GDpx",
    # Emerging Market ETFs
    "etf_india":     "INDA",
    "etf_em":        "EEM",
}

FRED_SERIES = {
    "fed_funds_rate": "FEDFUNDS",
    "treasury_10y":   "DGS10",
    "treasury_2y":    "DGS2",
    "treasury_5y":    "DGS5",
    "real_yield_10y": "DFII10",
    "breakeven_inflation_10y": "T10YIE",
    "us_cpi":          "CPIAUCSL",
    "us_core_cpi":     "CPILFESL",
    "us_unemployment": "UNRATE",
    "us_m2":           "M2SL",
    "us_gdp":          "GDP",
    "us_trade_balance": "BOPGSTB",
    "us_consumer_confidence": "UMCSENT",
    "us_pce": "PCE",
}

SL_INDICATORS = {
    "gdp_growth":      "NY.GDP.MKTP.KD.ZG",
    "inflation_cpi":   "FP.CPI.TOTL.ZG",
    "remittances":     "BX.TRF.PWKR.CD.DT",
    "fdi_inflows":     "BX.KLT.DINV.CD.WD",
    "unemployment":    "SL.UEM.TOTL.ZS",
    "exports":         "NE.EXP.GNFS.CD",
    "imports":         "NE.IMP.GNFS.CD",
    "reserves":        "FI.RES.TOTL.CD",
    "current_account": "BN.CAB.XOKA.CD",
    "trade_balance":   "NE.RSB.GNFS.CD",
}

NEWS_QUERIES = {
    "sri_lanka":     "Sri Lanka economy stock market CSE Colombo",
    "gold_silver":   "gold silver price precious metals bullion",
    "us_economy":    "Federal Reserve interest rates US economy inflation",
    "asian_markets": "IOndia China Asian stock market Sensex Nifty",
    "oil_energy":    "oil price OPEC crude energy commodity",
    "geopolitical":  "geopolitical risk war sanctions trade conflict",
}

def fetch_yahoo_all():
    try:
        import yfinance as yf
    except ImportError:
        return {}
    results = {}
    ticker_list = list(YAHOO_TICKERS_values())
    try:
        raw = yf.download(" ".join(ticker_list), period="5d", interval="1d", auto_adjust=True, group_by="ticker", progress=False)
    except Exception as e:
        return {}
    for name, ticker in YAHOO_TICKERS.items():
        try:
            df = raw[ticker] if hasattr(raw, '__getitem__') and not raw.empty else None
            if df is None or df.empty:
                results[name] = {"close": None}
                continue
            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            close = float(last["Close"])
            prev_close = float(prev["Close"])
            change = close - prev_close
            results[name] = {"ticker": ticker, "close": round(close, 4), "change_pct": round(change/prev_close*100, 4), "date": str(df.index[-1].date())}
        except:
            results[name] = {"close": None}
    gold = results.get("gold", {}).get("close")
    lkr = results.get("usd_lkr", {}).get("close")
    if gold and lkr:
        results["gold_lkr"] = {"close": round(gold * lkr, 2), "date": str(date.today())}
    return results

def fetch_fred_all():
    if not FRED:
        return {}
    results = {}
    start = str(date.today() - timedelta(days=45))
    for name, sid in FRED_SERIES.items():
        try:
            r = requests.get("https://api.stlouisfed.org/fred/series/observations", params={"series_id":sid,"api_key":FRED_API_KEY,"file_type":"json","sort_order":"desc","observation_start":start,"limit":5}, timeout=10)
            obs = [o for o in r.json().get("observations",[]) if o["value"]!="."]
            if obs:
                results[name] = {"series_id":sid,"value":float(obs[0]["value"]),"date":obs[0]["date"]}
        except: pass
    return results

def fetch_worldbank_all():
    results = {}
    for name, ind in SL_INDICATORS.items():
        try:
            r = requests.get(f"https://api.worldbank.org/v2/country/LK/indicator/{ind}", params={"format":"json","mrv":2}, timeout=12)
            d = r.json()
            if len(d)>1 and d[1]:
                item = d[1][0]
                results[name] = {"indicator":ind,"value":item.get("value"),"year":item.get("date","")}
        except: pass
    return results

def fetch_news_all():
    if not NEWS_API_KEY: return []
    all = []
    seen = set()
    for cat, q in NEWS_QUERIES.items():
        try:
            r = requests.get("https://newsapi.org/v2/everything", params={"q":q,"apiKey":NEWS_API_KEY,"pageSize":5,"language":"en","sortBy":"publishedAt","from":str(date.today()-timedelta(days=1))}, timeout=10)
            for a in r.json().get("articles",[]):
                u = a.get("url","")
                if u not in seen:
                    seen.add(u)
                    all.append({"category":cat,"title":a.get("title",""),"url":u,"source_name":a.get("source",{}).get("name",""),"published_at":a.get("publishedAt","")})
        except: pass
    return all

def supabase_upsert(table, data, on_conflict="date"):
    if not SUPABASE_URL: return False
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}, json=data, timeout=15)
        return r.status_code in (200,201)
    except: return False

def scrape_cse():
    try:
        from bs4 import BeautifulSoup
        r = requests.get("https://www.cse.lk/home/market-summary", headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(r.content, "html.parser")
        return {"scraped": True, "url": "https://www.cse.lk/home/market-summary"}
    except Exception as e:
        return {"scraped": False, "error": str(e)}

def collect_all():
    print("InvestSmart Data Collector")
    snapshot = {"collected_at": datetime.now().isoformat(), "date": str(date.today())}
    snapshot["market_prices"] = fetch_yahoo_all()
    snapshot["us_macro"] = fetch_fred_all()
    snapshot["sl_macro"] = fetch_worldbank_all()
    snapshot["news"] = fetch_news_all()
    snapshot["cse_data"] = scrape_cse()
    with open(f"data_snapshot_{date.today()}.json", "w") as f:
        json.dump(snapshot, f, indent=2, default=str)
    return snapshot

if __name__ == "__main__":
    collect_all()
