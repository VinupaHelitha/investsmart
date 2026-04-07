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
    "gold":         "GC=F",
    "silver":       "SI=F",
    "oil_brent":    "BZ=F",
    "oil_wti":      "CL=F",
    "copper":       "HG=F",
    "natural_gas":  "NG=F",
    # US Indices
    "sp500":        "^GSPC",
    "nasdaq":       "^IXIC",
    "dow":          "^DJI",
    "vix":          "^VIX",
    "russell2000":  "^RUT",
    # Asian Indices
    "sensex":       "^BSESN",
    "nifty":        "^NSEI",
    "hang_seng":    "^HSI",
    "nikkei":       "^N225",
    "shanghai":     "000001.SS",
    "kospi":        "^KS11",
    # European Indices
    "ftse100":      "^FTSE",
    "dax":          "^GDAXI",
    "cac40":        "^FCHI",
    # Forex
    "usd_lkr":      "LKR=X",
    "usd_index":    "DX-Y.NYB",
    "eur_usd":      "EURUSD=X",
    "usd_inr":      "INR=X",
    "usd_jpy":      "JPY=X",
    "usd_cny":      "CNY=X",
    "usd_gbp":      "GBPUSD=X",
    "usd_aud":      "AUDUSD=X",
    # Bond ETFs (since direct bond prices aren't on Yahoo)
    "bond_etf_20y": "TLT",    # 20+ Year Treasury Bond ETF
    "bond_etf_7y":  "IEF",    # 7-10 Year Treasury Bond ETF
    "bond_etf_em":  "EMB",    # Emerging Markets Bond ETF
    # Sector ETFs (useful for sector rotation signals)
    "etf_energy":   "XLE",
    "etf_finance":  "XLF",
    "etf_tech":     "XLK",
    "etf_gold_miners": "GDX",
    # Emerging Market ETFs
    "etf_india":    "INDA",
    "etf_em":       "EEM",
}

# FRED series IDs (US Federal Reserve economic data)
FRED_SERIES = {
    "fed_funds_rate":          "FEDFUNDS",
    "treasury_10y":            "DGS10",
    "treasury_2y":             "DGS2",
    "treasury_5y":             "DGS5",
    "real_yield_10y":          "DFII10",      # 10Y TIPS (inflation-adjusted)
    "breakeven_inflation_10y": "T10YIE",      # market inflation expectations
    "us_cpi":                  "CPIAUCSL",
    "us_core_cpi":             "CPILFESL",
    "us_unemployment":         "UNRATE",
    "us_m2":                   "M2SL",        # money supply
    "us_gdp":                  "GDP",
    "us_trade_balance":        "BOPGSTB",
    "us_consumer_confidence":  "UMCSENT",
    "us_pce":                  "PCE",         # personal consumption expenditure
}

# World Bank indicators for Sri Lanka
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

# NewsAPI search queries (6 categories for Sri Lankan investors)
NEWS_QUERIES = {
    "sri_lanka":    "Sri Lanka economy stock market CSE Colombo",
    "gold_silver":  "gold silver price precious metals bullion",
    "us_economy":   "Federal Reserve interest rates US economy inflation",
    "asian_markets":"India China Asian stock market Sensex Nifty",
    "oil_energy":   "oil price OPEC crude energy commodity",
    "geopolitical": "geopolitical risk war sanctions trade conflict",
}


# ─────────────────────────────────────────────────
# FETCH FUNCTIONS
# ─────────────────────────────────────────────────

def fetch_yahoo_all() -> dict:
    """Fetch all Yahoo Finance tickers. Returns dict of ticker_name → OHLCV dict."""
    try:
        import yfinance as yf
    except ImportError:
        print("[YAHOO] yfinance not installed. Run: pip install yfinance")
        return {}

    results = {}
    ticker_list = list(YAHOO_TICKERS.values())

    print(f"[YAHOO] Downloading {len(ticker_list)} tickers...")
    try:
        # Batch download is much faster than individual calls
        raw = yf.download(
            " ".join(ticker_list),
            period="5d",
            interval="1d",
            auto_adjust=True,
            group_by="ticker",
            progress=False,
        )
    except Exception as e:
        print(f"[YAHOO] Batch download failed: {e}")
        return {}

    for name, ticker in YAHOO_TICKERS.items():
        try:
            if len(ticker_list) == 1:
                df = raw
            else:
                df = raw[ticker] if ticker in raw.columns.get_level_values(0) else None

            if df is None or df.empty or len(df) < 1:
                results[name] = {"close": None}
                continue

            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]

            close = float(last["Close"]) if last["Close"] is not None else None
            prev_close = float(prev["Close"]) if prev["Close"] is not None else None

            change     = (close - prev_close) if close and prev_close else None
            change_pct = ((change / prev_close) * 100) if change and prev_close else None

            results[name] = {
                "ticker":     ticker,
                "close":      round(close, 4)      if close      else None,
                "open":       round(float(last.get("Open",  close)), 4) if close else None,
                "high":       round(float(last.get("High",  close)), 4) if close else None,
                "low":        round(float(last.get("Low",   close)), 4) if close else None,
                "volume":     int(last.get("Volume", 0)) if last.get("Volume") else None,
                "change":     round(change,     4) if change     else None,
                "change_pct": round(change_pct, 4) if change_pct else None,
                "date":       str(df.index[-1].date()),
            }
        except Exception as e:
            print(f"[YAHOO] Error parsing {name} ({ticker}): {e}")
            results[name] = {"close": None, "ticker": ticker}

    # Calculate Gold in LKR
    gold_close   = results.get("gold",    {}).get("close")
    usd_lkr_close= results.get("usd_lkr",{}).get("close")
    if gold_close and usd_lkr_close:
        results["gold_lkr"] = {
            "close":   round(gold_close * usd_lkr_close, 2),
            "note":    "Calculated: Gold(USD/oz) × USD/LKR",
            "date":    str(date.today()),
        }
    else:
        results["gold_lkr"] = {"close": None}

    print(f"[YAHOO] ✓ Collected {sum(1 for v in results.values() if v.get('close'))} prices")
    return results


def fetch_fred_all() -> dict:
    """Fetch all FRED macroeconomic series."""
    if not FRED_API_KEY:
        print("[FRED] No API key — skipping. Add FRED_API_KEY to your environment.")
        return {}

    results    = {}
    start_date = str(date.today() - timedelta(days=45))  # last 45 days to ensure we get latest

    for name, series_id in FRED_SERIES.items():
        try:
            url    = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id":          series_id,
                "api_key":            FRED_API_KEY,
                "file_type":          "json",
                "sort_order":         "desc",
                "observation_start":  start_date,
                "limit":              5,
            }
            r    = requests.get(url, params=params, timeout=10)
            data = r.json()
            obs  = [o for o in data.get("observations", []) if o["value"] != "."]
            if obs:
                val = float(obs[0]["value"])
                results[name] = {
                    "series_id": series_id,
                    "value":     val,
                    "date":      obs[0]["date"],
                }
            else:
                results[name] = {"series_id": series_id, "value": None}
        except Exception as e:
            print(f"[FRED] Error fetching {name} ({series_id}): {e}")
            results[name] = {"series_id": series_id, "value": None}

    # Derived: yield curve spread (10Y - 2Y)
    y10 = results.get("treasury_10y", {}).get("value")
    y2  = results.get("treasury_2y",  {}).get("value")
    if y10 and y2:
        spread = round(y10 - y2, 4)
        results["yield_curve_spread"] = {
            "value": spread,
            "note":  "10Y - 2Y Treasury. Negative = inverted (recession signal)"
        }

    print(f"[FRED] ✓ Collected {sum(1 for v in results.values() if v.get('value'))} macro series")
    return results


def fetch_worldbank_all() -> dict:
    """Fetch World Bank data for Sri Lanka."""
    results = {}

    for name, indicator in SL_INDICATORS.items():
        try:
            url    = f"https://api.worldbank.org/v2/country/LK/indicator/{indicator}"
            params = {"format": "json", "mrv": 2}
            r      = requests.get(url, params=params, timeout=12)
            data   = r.json()

            if len(data) > 1 and data[1]:
                item = data[1][0]
                val  = item.get("value")
                results[name] = {
                    "indicator": indicator,
                    "value":     round(val, 4) if val is not None else None,
                    "year":      item.get("date", ""),
                    "country":   "Sri Lanka",
                }
            else:
                results[name] = {"indicator": indicator, "value": None}
        except Exception as e:
            print(f"[WORLDBANK] Error fetching {name}: {e}")
            results[name] = {"indicator": indicator, "value": None}

    print(f"[WORLDBANK] ✓ Collected {sum(1 for v in results.values() if v.get('value'))} SL indicators")
    return results


def fetch_news_all() -> list:
    """Fetch news articles from NewsAPI across all 6 categories."""
    if not NEWS_API_KEY:
        print("[NEWS] No API key — skipping. Add NEWS_API_KEY to your environment.")
        return []

    all_articles = []
    seen_urls    = set()

    for category, query in NEWS_QUERIES.items():
        try:
            url    = "https://newsapi.org/v2/everything"
            params = {
                "q":        query,
                "apiKey":   NEWS_API_KEY,
                "pageSize": 5,          # 5 per category × 6 = 30 total, within free limit
                "language": "en",
                "sortBy":   "publishedAt",
                "from":     str(date.today() - timedelta(days=1)),
            }
            r    = requests.get(url, params=params, timeout=10)
            data = r.json()

            for art in data.get("articles", []):
                url_art = art.get("url", "")
                title   = art.get("title", "")
                if url_art in seen_urls or not title or "[Removed]" in title:
                    continue
                seen_urls.add(url_art)
                all_articles.append({
                    "category":    category,
                    "title":       title,
                    "description": art.get("description", ""),
                    "url":         url_art,
                    "source_name": art.get("source", {}).get("name", ""),
                    "published_at":art.get("publishedAt", ""),
                    "collected_at":datetime.now().isoformat(),
                })
        except Exception as e:
            print(f"[NEWS] Error fetching {category}: {e}")

    print(f"[NEWS] ✓ Collected {len(all_articles)} articles")
    return all_articles


def scrape_cse() -> dict:
    """
    Scrape Colombo Stock Exchange data from cse.lk.
    This is best-effort — if it fails, the app continues without CSE data.
    Official CSE API does not exist for free access.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {"error": "beautifulsoup4 not installed"}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    }

    result = {}

    # Try to get main CSE summary data
    try:
        r   = requests.get("https://www.cse.lk/home/market-summary", headers=headers, timeout=15)
        soup= BeautifulSoup(r.content, "html.parser")

        # Try to find ASPI (All Share Price Index)
        aspi_elem = soup.find(text=lambda t: t and "ASPI" in str(t))
        if aspi_elem:
            result["aspi_found"] = True

        # Grab any market data tables
        tables = soup.find_all("table")
        for t in tables[:2]:
            rows = t.find_all("tr")
            for row in rows:
                cells = [c.get_text(strip=True) for c in row.find_all(["td","th"])]
                if len(cells) >= 2:
                    key = cells[0].lower().replace(" ", "_")[:30]
                    val = cells[1]
                    if key and val:
                        result[key] = val

        result["scraped"] = True
        result["url"]     = "https://www.cse.lk/home/market-summary"
        print(f"[CSE] ✓ Scraped {len(result)} data points from cse.lk")

    except Exception as e:
        print(f"[CSE] Scraping failed (this is OK — app still works): {e}")
        result = {"error": str(e), "scraped": False}

    return result


# ─────────────────────────────────────────────────
# SUPABASE SAVE FUNCTIONS
# ─────────────────────────────────────────────────

def supabase_upsert(table: str, data: dict, on_conflict: str = "date") -> bool:
    """Upsert a record to Supabase (insert or update if date already exists)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    try:
        url     = f"{SUPABASE_URL}/rest/v1/{table}"
        headers = {
            "apikey":        SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type":  "application/json",
            "Prefer":        f"resolution=merge-duplicates,return=minimal",
        }
        r = requests.post(url, headers=headers, json=data, timeout=15)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"[SUPABASE] Error upserting to {table}: {e}")
        return False


def save_to_supabase(snapshot: dict):
    """Save today's complete data snapshot to Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[SUPABASE] No credentials — skipping database save.")
        return

    today = str(date.today())
    ts    = datetime.now().isoformat()

    # Save each price individually to daily_prices table
    market_prices = snapshot.get("market_prices", {})
    for name, data in market_prices.items():
        if data.get("close"):
            supabase_upsert("daily_prices", {
                "date":         today,
                "ticker_name":   name,
                "ticker_symbol": data.get("ticker", ""),
                "close":         data["close"],
                "open":          data.get("open"),
                "high":          data.get("high"),
                "low":           data.get("low"),
                "volume":        data.get("volume"),
                "change_pct":    data.get("change_pct"),
                "collected_at":  ts,
            }, on_conflict="date,ticker_name")

    # Save macro data
    macro_data = snapshot.get("us_macro", {})
    for name, data in macro_data.items():
        if data.get("value") is not None:
            supabase_upsert("macro_data", {
                "date":         today,
                "source":        "FRED",
                "series_name":  name,
                "series_id":    data.get("series_id", ""),
                "value":        data["value"],
                "collected_at": ts,
            }, on_conflict="date,series_name")

    # Save news articles
    for article in snapshot.get("news", []):
        supabase_upsert("news_items", {
            "date":         today,
            "category":     article.get("category", ""),
            "title":        article.get("title", ""),
            "url":          article.get("url", ""),
            "source_name":  article.get("source_name", ""),
            "description":  article.get("description", "")[:500],
            "published_at": article.get("published_at", ""),
            "collected_at": ts,
        }, on_conflict="url")

    print("[SUPABASE] ✓ Data saved to database")


# ─────────────────────────────────────────────────
# MASTER FUNCTION
# ─────────────────────────────────────────────────

def collect_all() -> dict:
    """
    Master data collection function.
    Collects all market data, news, and macro indicators.
    Returns a complete snapshot dict and saves to Supabase + local JSON.
    """
    print("=" * 60)
    print("InvestSmart — Data Collector")
    print(f"{datetime.now().strftime('%A %d %B %Y %H:%M:%S')} (Sri Lanka UTC+5:30)")
    print("=" * 60)

    snapshot = {
        "collected_at": datetime.now().isoformat(),
        "date":         str(date.today()),
    }

    # 1. Yahoo Finance prices
    print("\n[1/5] Fetching Yahoo Finance prices...")
    snapshot["market_prices"] = fetch_yahoo_all()

    # 2. FRED macro data
    print("\n[2/5] Fetching FRED macro data...")
    snapshot["us_macro"] = fetch_fred_all()

    # 3. World Bank Sri Lanka data
    print("\n[3/5] Fetching World Bank Sri Lanka data...")
    snapshot["sl_macro"] = fetch_worldbank_all()

    # 4. News
    print("\n[4/5] Fetching news articles...")
    snapshot["news"] = fetch_news_all()

    # 5. CSE data (best-effort scrape)
    print("\n[5/5] Scraping CSE data...")
    snapshot["cse_data"] = scrape_cse()

    # Save JSON snapshot
    filename = f"data_snapshot_{date.today()}.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, default=str)
        print(f"\n[FILE] Snapshot saved: {filename}")
    except Exception as e:
        print(f"[FILE] Error saving snapshot: {e}")

    # Save to Supabase
    print("\n[SUPABASE] Saving to database...")
    save_to_supabase(snapshot)

    # Print summary
    mp_count = sum(1 for v in snapshot["market_prices"].values() if v.get("close"))
    macro_count = sum(1 for v in snapshot["us_macro"].values() if v.get("value"))
    news_count  = len(snapshot["news"])

    print("\n" + "=" * 60)
    print(f"✓ Collection complete:")
    print(f"  Market prices: {mp_count} tickers")
    print(f"  Macro series:  {macro_count} indicators")
    print(f"  News articles: {news_count}")
    print(f"  CSE data:      {'✓' if snapshot['cse_data'].get('scraped') else 'Failed (OK)'}")
    print("=" * 60)

    return snapshot


if __name__ == "__main__":
    collect_all()
