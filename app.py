"""
app.py — InvestSmart
Streamlit dashboard for Colombo Stock Exchange (CSE) and global market intelligence.

Pages:
  1. Dashboard      — quick overview of all markets
  2. Gold & Silver  — precious metals analysis
  3. Global Markets — US, Asia, Europe indices
  4. News Feed      — categorised news with AI summary
  5. AI Briefing    — full AI-generated daily market briefing (Claude primary)
  6. About          — platform information

Author: InvestSmart
Run:    streamlit run app.py
"""

import os
import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────
# SECRETS — load from Streamlit Cloud or .env
# ─────────────────────────────────────────────────
def get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

ANTHROPIC_API_KEY = get_secret("ANTHROPIC_API_KEY")
OPENAI_API_KEY    = get_secret("OPENAI_API_KEY")
GEMINI_API_KEY    = get_secret("GEMINI_API_KEY")
FRED_API_KEY      = get_secret("FRED_API_KEY")
NEWS_API_KEY      = get_secret("NEWS_API_KEY")
SUPABASE_URL      = get_secret("SUPABASE_URL")
SUPABASE_KEY      = get_secret("SUPABASE_KEY")

# ─────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────
st.set_page_config(
    page_title="InvestSmart — CSE Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a clean, professional look
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: #1e2130;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #2d3147;
    }
    .positive { color: #00d26a; font-weight: 600; }
    .negative { color: #ff4b4b; font-weight: 600; }
    .neutral  { color: #ffa500; font-weight: 600; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #a0a8c8;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin: 1.5rem 0 0.5rem 0;
    }
    div[data-testid="stMetric"] {
        background: #1e2130;
        border-radius: 10px;
        padding: 12px;
    }
    div[data-testid="stMetric"] label {
        font-size: 0.78rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────
# HELPER FORMATTERS
# ─────────────────────────────────────────────────
def fmt_lkr(value: float | None) -> str:
    """Format LKR value compactly — avoids card truncation."""
    if value is None:
        return "N/A"
    if value >= 1_000_000:
        return f"LKR {value/1_000_000:.2f}M"
    if value >= 1_000:
        return f"LKR {value:,.0f}"
    return f"LKR {value:,.2f}"

def fmt_index(value: float | None) -> str:
    """Format index value compactly for narrow metric cards."""
    if value is None:
        return "N/A"
    if value >= 100_000:
        return f"{value/1_000:.1f}K"
    if value >= 10_000:
        return f"{value:,.0f}"
    return f"{value:,.2f}"


# ─────────────────────────────────────────────────
# DATA FETCHING FUNCTIONS (cached for performance)
# ─────────────────────────────────────────────────

@st.cache_data(ttl=300)  # 5 minutes — live prices
def fetch_price(ticker: str, period: str = "5d") -> pd.DataFrame | None:
    """Fetch OHLCV data from Yahoo Finance."""
    try:
        df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
        if df.empty:
            return None
        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return None


def current_price(ticker: str) -> dict:
    """Get the latest price, change, and change% for a ticker."""
    df = fetch_price(ticker, period="5d")
    if df is None or len(df) < 2:
        return {"close": None, "change": None, "change_pct": None,
                "open": None, "high": None, "low": None, "volume": None}
    last  = df.iloc[-1]
    prev  = df.iloc[-2]
    close = float(last["Close"])
    prev_close = float(prev["Close"])
    change     = close - prev_close
    change_pct = (change / prev_close) * 100 if prev_close else 0
    return {
        "close":      close,
        "change":     change,
        "change_pct": change_pct,
        "open":       float(last.get("Open",  close)),
        "high":       float(last.get("High",  close)),
        "low":        float(last.get("Low",   close)),
        "volume":     float(last.get("Volume", 0)),
    }


@st.cache_data(ttl=3600)  # 1 hour — FRED data doesn't change frequently
def fetch_fred(series_id: str) -> float | None:
    """Fetch a single value from the FRED API (Federal Reserve)."""
    if not FRED_API_KEY:
        return None
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id":         series_id,
            "api_key":           FRED_API_KEY,
            "file_type":         "json",
            "sort_order":        "desc",
            "observation_start": str(date.today() - timedelta(days=30)),
            "limit":             1,
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        obs  = data.get("observations", [])
        if obs and obs[0]["value"] != ".":
            return float(obs[0]["value"])
        return None
    except Exception:
        return None


@st.cache_data(ttl=1800)  # 30 minutes — news
def fetch_news(query: str, n: int = 8) -> list:
    """Fetch top-headline news from NewsAPI (free tier compatible)."""
    if not NEWS_API_KEY:
        return []
    try:
        # Use top-headlines with a keyword search — works on free NewsAPI tier
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "q":        query,
            "apiKey":   NEWS_API_KEY,
            "pageSize": n,
            "language": "en",
        }
        r    = requests.get(url, params=params, timeout=10)
        data = r.json()
        articles = data.get("articles", [])
        # If top-headlines returns nothing, try everything endpoint as fallback
        if not articles:
            url2 = "https://newsapi.org/v2/everything"
            params2 = {
                "q":        query,
                "apiKey":   NEWS_API_KEY,
                "pageSize": n,
                "language": "en",
                "sortBy":   "publishedAt",
                "from":     str(date.today() - timedelta(days=7)),
            }
            r2    = requests.get(url2, params=params2, timeout=10)
            data2 = r2.json()
            articles = data2.get("articles", [])
        return [a for a in articles if "[Removed]" not in (a.get("title") or "")][:n]
    except Exception:
        return []


@st.cache_data(ttl=21600)  # 6 hours — World Bank (annual data)
def fetch_worldbank(indicator: str, country: str = "LK") -> dict:
    """Fetch Sri Lanka macro data from World Bank Open API."""
    try:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        params = {"format": "json", "mrv": 1}
        r    = requests.get(url, params=params, timeout=10)
        data = r.json()
        if len(data) > 1 and data[1]:
            item = data[1][0]
            return {"value": item.get("value"), "year": item.get("date", "")}
        return {}
    except Exception:
        return {}


# ─────────────────────────────────────────────────
# AI BRIEFING FUNCTION (Claude → OpenAI → Gemini)
# ─────────────────────────────────────────────────
def call_claude_briefing(prompt: str) -> tuple[str, str]:
    """Try Claude first, then OpenAI, then Gemini. Returns (text, model_used)."""
    # 1. Try Claude (PRIMARY)
    if ANTHROPIC_API_KEY:
        try:
            import anthropic
            client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text, "Claude (claude-sonnet-4-6)"
        except Exception as e:
            st.warning(f"Claude unavailable ({e}) — trying OpenAI...")

    # 2. Try OpenAI (SECONDARY)
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client   = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2500,
                messages=[
                    {"role": "system", "content": "You are a senior investment analyst specialising in the Colombo Stock Exchange (CSE) and Sri Lankan financial markets."},
                    {"role": "user",   "content": prompt}
                ]
            )
            return response.choices[0].message.content, "OpenAI (gpt-4o)"
        except Exception as e:
            st.warning(f"OpenAI unavailable ({e}) — trying Gemini...")

    # 3. Try Gemini (FREE FALLBACK)
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model    = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.3, "max_output_tokens": 2500}
            )
            return response.text, "Gemini 1.5 Flash (free fallback)"
        except Exception as e:
            return f"All AI providers failed. Last error: {e}", "none"

    return "No AI API keys configured. Please add ANTHROPIC_API_KEY to your secrets.", "none"


def generate_briefing(market_data: dict) -> tuple[str, str]:
    """Build the full briefing prompt and call AI."""
    mp    = market_data
    today = datetime.now().strftime("%A, %d %B %Y")

    gold_usd = mp.get("gold", {}).get("close")
    usd_lkr  = mp.get("usd_lkr", {}).get("close")
    gold_lkr = (gold_usd * usd_lkr) if gold_usd and usd_lkr else None

    def fmt(d, prefix="", suffix=""):
        if d and d.get("close"):
            c   = d["close"]
            pct = d.get("change_pct", 0) or 0
            sgn = "+" if pct >= 0 else ""
            arr = "▲" if pct >= 0 else "▼"
            return f"{prefix}{c:,.2f}{suffix}  {arr}{sgn}{pct:.2f}%"
        return "N/A"

    prompt = f"""You are a senior investment analyst with deep expertise in the Colombo Stock Exchange (CSE), Sri Lankan markets, and global macro investing. Write a concise but complete daily market briefing for Sri Lankan retail investors.

TODAY: {today}

MARKET DATA:
• Gold (USD/oz):        {fmt(mp.get('gold'),    '$')}
• Gold (LKR/oz):        {'LKR {:,.0f}'.format(gold_lkr) if gold_lkr else 'N/A'}
• Silver (USD/oz):      {fmt(mp.get('silver'),  '$')}
• Oil Brent (USD/bbl):  {fmt(mp.get('oil'),     '$')}
• S&P 500:              {fmt(mp.get('sp500'))}
• VIX:                  {fmt(mp.get('vix'))}
• USD/LKR:              {fmt(mp.get('usd_lkr'))}
• USD Index (DXY):      {fmt(mp.get('dxy'))}
• BSE Sensex (India):   {fmt(mp.get('sensex'))}
• Nifty 50:             {fmt(mp.get('nifty'))}

Write a structured briefing with these sections:
1. CSE Outlook (how today's data affects the Colombo Stock Exchange — most important)
2. Gold & Silver in LKR (critical for Sri Lankan investors)
3. Global Macro Summary (US markets, Asia, forex)
4. Key Risks & Opportunities
5. Sentiment Score: BULLISH / NEUTRAL / BEARISH for CSE, Gold, and USD/LKR

Be specific, reference actual numbers, and keep each section to 2–3 sentences. End with: *Not investment advice — for information only.*"""

    return call_claude_briefing(prompt)


# ─────────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 InvestSmart")
    st.markdown("*CSE Intelligence Platform*")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["🏠 Dashboard", "🥇 Gold & Silver", "🌍 Global Markets",
         "📰 News Feed", "🤖 AI Briefing", "ℹ️ About"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown(f"**Last updated:** {datetime.now().strftime('%H:%M:%S')}")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Data: Yahoo Finance · FRED · World Bank · NewsAPI")
    st.caption("AI: Claude · OpenAI · Gemini")


# ─────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("📊 Market Dashboard")
    st.caption(f"Real-time overview · {datetime.now().strftime('%A, %d %B %Y %H:%M')}")

    with st.spinner("Loading market data..."):
        gold   = current_price("GC=F")
        silver = current_price("SI=F")
        usd_lkr= current_price("LKR=X")
        sp500  = current_price("^GSPC")
        vix    = current_price("^VIX")
        oil    = current_price("BZ=F")
        sensex = current_price("^BSESN")
        nifty  = current_price("^NSEI")

    # ── Highlighted Metrics ──
    st.markdown("### 🔑 Key Indicators")
    col1, col2, col3, col4 = st.columns(4)

    def metric_delta(d: dict) -> str | None:
        if d.get("change_pct") is not None:
            return f"{d['change_pct']:+.2f}%"
        return None

    with col1:
        v = gold.get("close")
        st.metric("Gold (USD/oz)", f"${v:,.2f}" if v else "N/A", metric_delta(gold))
    with col2:
        g = gold.get("close")
        r = usd_lkr.get("close")
        gold_lkr = g * r if g and r else None
        st.metric("Gold (LKR/oz)", fmt_lkr(gold_lkr), metric_delta(gold))
    with col3:
        v = usd_lkr.get("close")
        st.metric("USD / LKR", f"LKR {v:,.2f}" if v else "N/A", metric_delta(usd_lkr),
                  delta_color="inverse")
    with col4:
        v = vix.get("close")
        st.metric("VIX Fear Index", f"{v:.2f}" if v else "N/A", metric_delta(vix),
                  delta_color="inverse")

    st.markdown("---")

    # ── Markets Grid ──
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**🌐 US Markets**")
        v = sp500.get("close")
        p = sp500.get("change_pct") or 0
        color = "positive" if p >= 0 else "negative"
        st.markdown(f"S&P 500: `{v:,.2f}` <span class='{color}'>{p:+.2f}%</span>" if v else "S&P 500: N/A", unsafe_allow_html=True)
        v = oil.get("close")
        p = oil.get("change_pct") or 0
        color = "positive" if p >= 0 else "negative"
        st.markdown(f"Brent Oil: `${v:,.2f}` <span class='{color}'>{p:+.2f}%</span>" if v else "Brent Oil: N/A", unsafe_allow_html=True)

    with col_b:
        st.markdown("**🌏 Asian Markets**")
        v = sensex.get("close")
        p = sensex.get("change_pct") or 0
        color = "positive" if p >= 0 else "negative"
        st.markdown(f"BSE Sensex: `{v:,.0f}` <span class='{color}'>{p:+.2f}%</span>" if v else "BSE Sensex: N/A", unsafe_allow_html=True)
        v = nifty.get("close")
        p = nifty.get("change_pct") or 0
        color = "positive" if p >= 0 else "negative"
        st.markdown(f"Nifty 50: `{v:,.0f}` <span class='{color}'>{p:+.2f}%</span>" if v else "Nifty 50: N/A", unsafe_allow_html=True)

    with col_c:
        st.markdown("**💰 Precious Metals**")
        v = silver.get("close")
        p = silver.get("change_pct") or 0
        color = "positive" if p >= 0 else "negative"
        st.markdown(f"Silver: `${v:,.2f}/oz` <span class='{color}'>{p:+.2f}%</span>" if v else "Silver: N/A", unsafe_allow_html=True)
        v = gold.get("close")
        p = gold.get("change_pct") or 0
        color = "positive" if p >= 0 else "negative"
        st.markdown(f"Gold: `${v:,.2f}/oz` <span class='{color}'>{p:+.2f}%</span>" if v else "Gold: N/A", unsafe_allow_html=True)

    # ── 30-day Performance Comparison ──
    st.markdown("---")
    st.markdown("### 📉 30-Day Performance Comparison")
    with st.spinner("Loading chart..."):
        tickers_chart = {
            "Gold":    "GC=F",
            "Silver":  "SI=F",
            "S&P 500": "^GSPC",
            "Sensex":  "^BSESN",
            "Oil":     "BZ=F",
        }
        fig = go.Figure()
        for name, ticker in tickers_chart.items():
            df = fetch_price(ticker, period="1mo")
            if df is not None and len(df) > 1:
                close  = df["Close"].squeeze()
                normed = (close / close.iloc[0] - 1) * 100
                fig.add_trace(go.Scatter(
                    x=df.index, y=normed, name=name,
                    mode="lines", line=dict(width=2)
                ))
        fig.update_layout(
            title="Normalised 30-day Return (%)",
            template="plotly_dark",
            height=380,
            yaxis_ticksuffix="%",
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.2),
            margin=dict(l=10, r=10, t=40, b=60),
        )
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────
# PAGE: GOLD & SILVER
# ─────────────────────────────────────────────────
elif page == "🥇 Gold & Silver":
    st.title("🥇 Gold & Silver")
    st.caption("Precious metals analysis — prices in USD and LKR")

    period_map  = {"1 Week": "5d", "1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y"}
    period_sel  = st.selectbox("Chart Period", list(period_map.keys()), index=1)
    period_code = period_map[period_sel]

    usd_lkr_data = current_price("LKR=X")
    usd_lkr_rate = usd_lkr_data.get("close") or 312  # updated fallback

    gold   = current_price("GC=F")
    silver = current_price("SI=F")
    gp     = gold.get("close")
    gpct   = gold.get("change_pct") or 0
    sp     = silver.get("close")
    spct   = silver.get("change_pct") or 0

    gold_lkr_val   = gp * usd_lkr_rate if gp else None
    silver_lkr_val = sp * usd_lkr_rate if sp else None

    # ── Top Metrics — 2 rows of 3 (wider cards, no truncation) ──
    st.markdown("### Key Prices")
    m1, m2, m3 = st.columns(3)
    m1.metric("Gold (USD/oz)",    f"${gp:,.2f}"           if gp else "N/A", f"{gpct:+.2f}%" if gpct else None)
    m2.metric("Gold (LKR/oz)",    fmt_lkr(gold_lkr_val),  f"{gpct:+.2f}%" if gpct else None)
    m3.metric("Gold (USD/gram)",  f"${gp/31.1035:,.2f}"   if gp else "N/A")
    m4, m5, m6 = st.columns(3)
    m4.metric("Silver (USD/oz)",  f"${sp:,.2f}"           if sp else "N/A", f"{spct:+.2f}%" if spct else None)
    m5.metric("Silver (LKR/oz)",  fmt_lkr(silver_lkr_val))
    m6.metric("Gold/Silver Ratio",f"{gp/sp:.1f}x"         if gp and sp else "N/A")

    st.markdown("---")

    # ── Charts side by side ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Gold (GC=F)")
        df_gold = fetch_price("GC=F", period=period_code)
        if df_gold is not None:
            fig = go.Figure(data=[go.Candlestick(
                x    = df_gold.index,
                open = df_gold["Open"].squeeze(),
                high = df_gold["High"].squeeze(),
                low  = df_gold["Low"].squeeze(),
                close= df_gold["Close"].squeeze(),
                name = "Gold",
                increasing_line_color="#00d26a",
                decreasing_line_color="#ff4b4b",
            )])
            fig.update_layout(
                title=f"Gold — {period_sel}",
                template="plotly_dark", height=320,
                xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Gold chart data unavailable.")

    with col2:
        st.markdown("#### Silver (SI=F)")
        df_silver = fetch_price("SI=F", period=period_code)
        if df_silver is not None:
            fig = go.Figure(data=[go.Candlestick(
                x    = df_silver.index,
                open = df_silver["Open"].squeeze(),
                high = df_silver["High"].squeeze(),
                low  = df_silver["Low"].squeeze(),
                close= df_silver["Close"].squeeze(),
                name = "Silver",
                increasing_line_color="#00d26a",
                decreasing_line_color="#ff4b4b",
            )])
            fig.update_layout(
                title=f"Silver — {period_sel}",
                template="plotly_dark", height=320,
                xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=0, t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Silver chart data unavailable.")

    # ── Gold in LKR Chart ──
    st.markdown("---")
    st.markdown("### 📊 Gold Price in LKR (last 30 days)")
    st.caption("Gold (LKR) = Gold (USD/oz) × USD/LKR rate. LKR depreciation amplifies gold returns for Sri Lankan investors.")

    df_g = fetch_price("GC=F", period="1mo")
    df_r = fetch_price("LKR=X", period="1mo")
    if df_g is not None and df_r is not None:
        gold_close  = df_g["Close"].squeeze().reindex(df_g.index)
        lkr_close   = df_r["Close"].squeeze().reindex(df_g.index, method="ffill")
        gold_in_lkr = gold_close * lkr_close

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_g.index, y=gold_in_lkr, fill="tozeroy",
                                  name="Gold (LKR/oz)", line=dict(color="#ffd700", width=2)))
        fig2.update_layout(
            template="plotly_dark", height=300,
            yaxis_title="LKR per troy oz",
            margin=dict(l=0, r=0, t=20, b=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── FRED Macro Context ──
    st.markdown("---")
    st.markdown("### 🏦 Gold Price Drivers (FRED)")
    col_a, col_b, col_c, col_d = st.columns(4)
    real_yield = fetch_fred("DFII10")
    fed_rate   = fetch_fred("FEDFUNDS")
    dxy        = current_price("DX-Y.NYB").get("close")
    inflation  = fetch_fred("T10YIE")

    col_a.metric("10Y Real Yield (TIPS)", f"{real_yield:.2f}%" if real_yield else "N/A",
                 help="Low/negative real yields → bullish for gold")
    col_b.metric("Fed Funds Rate",        f"{fed_rate:.2f}%"  if fed_rate  else "N/A")
    col_c.metric("USD Index (DXY)",       f"{dxy:.2f}"        if dxy       else "N/A",
                 help="Weak USD → higher gold in USD terms")
    col_d.metric("10Y Breakeven Inflation",f"{inflation:.2f}%" if inflation else "N/A",
                 help="Higher inflation expectations → bullish for gold")


# ─────────────────────────────────────────────────
# PAGE: GLOBAL MARKETS
# ─────────────────────────────────────────────────
elif page == "🌍 Global Markets":
    st.title("🌍 Global Markets")
    st.caption("US, Asian, and European indices — with Sri Lanka context")

    # Note: country flag emojis don't render on Linux — using text labels instead
    TICKERS = {
        "S&P 500":    "^GSPC",
        "NASDAQ":     "^IXIC",
        "Dow Jones":  "^DJI",
        "VIX (Fear)": "^VIX",
        "BSE Sensex": "^BSESN",
        "Nifty 50":   "^NSEI",
        "Hang Seng":  "^HSI",
        "Nikkei 225": "^N225",
        "FTSE 100":   "^FTSE",
        "DAX":        "^GDAXI",
    }

    st.markdown("### Live Prices")
    with st.spinner("Loading global prices..."):
        prices = {name: current_price(ticker) for name, ticker in TICKERS.items()}

    cols = st.columns(5)
    for i, (name, ticker) in enumerate(TICKERS.items()):
        d    = prices[name]
        v    = d.get("close")
        pct  = d.get("change_pct") or 0
        delta_col = "inverse" if "VIX" in name else "normal"
        with cols[i % 5]:
            st.metric(
                name,
                fmt_index(v),
                f"{pct:+.2f}%" if v else None,
                delta_color=delta_col
            )

    st.markdown("---")
    st.markdown("### 📉 1-Month Chart")
    selected = st.selectbox("Choose Market", list(TICKERS.keys()))
    df = fetch_price(TICKERS[selected], period="1mo")
    if df is not None:
        fig = go.Figure(data=[go.Candlestick(
            x    = df.index,
            open = df["Open"].squeeze(),
            high = df["High"].squeeze(),
            low  = df["Low"].squeeze(),
            close= df["Close"].squeeze(),
            name = selected,
        )])
        fig.update_layout(
            template="plotly_dark", height=400,
            xaxis_rangeslider_visible=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"Chart data unavailable for {selected}.")

    # ── Forex ──
    st.markdown("---")
    st.markdown("### 💱 Forex — Sri Lanka Relevant Pairs")
    forex = {
        "USD / LKR": "LKR=X",
        "USD Index":  "DX-Y.NYB",
        "EUR / USD":  "EURUSD=X",
        "USD / INR":  "INR=X",
        "USD / JPY":  "JPY=X",
    }
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, (name, ticker) in zip([c1, c2, c3, c4, c5], forex.items()):
        d   = current_price(ticker)
        v   = d.get("close")
        pct = d.get("change_pct") or 0
        # LKR pairs: 2 decimal places; others: 4 decimal places
        val_fmt = f"{v:,.2f}" if (v and "LKR" in name) else (f"{v:,.4f}" if v else "N/A")
        col.metric(name, val_fmt, f"{pct:+.2f}%" if v else None)


# ─────────────────────────────────────────────────
# PAGE: NEWS FEED
# ─────────────────────────────────────────────────
elif page == "📰 News Feed":
    st.title("📰 News Feed")
    st.caption("Latest financial news — categorised for Sri Lankan investors")

    categories = {
        "Sri Lanka":      "Sri Lanka economy stock market CSE",
        "Gold & Silver":  "gold silver price precious metals",
        "US Economy":     "Federal Reserve inflation US economy",
        "Asian Markets":  "India China Asian stock market",
        "Oil & Energy":   "oil price OPEC energy commodity",
        "Geopolitical":   "geopolitical risk war sanctions",
    }

    tabs = st.tabs(["🌴 " + k if k == "Sri Lanka" else
                    "🥇 " + k if k == "Gold & Silver" else
                    "💵 " + k if k == "US Economy" else
                    "🌏 " + k if k == "Asian Markets" else
                    "⚡ " + k if k == "Oil & Energy" else
                    "🌍 " + k for k in categories.keys()])

    for tab, (cat_name, query) in zip(tabs, categories.items()):
        with tab:
            with st.spinner(f"Loading {cat_name} news..."):
                articles = fetch_news(query, n=10)

            if not articles:
                if not NEWS_API_KEY:
                    st.warning("Add NEWS_API_KEY to your secrets to see news.")
                else:
                    st.info("No recent articles found. Try refreshing later.")
                continue

            for art in articles:
                title  = art.get("title", "")
                desc   = art.get("description", "")
                url    = art.get("url", "")
                source = art.get("source", {}).get("name", "")
                pub_at = art.get("publishedAt", "")[:10]

                if title and "[Removed]" not in title:
                    with st.container():
                        st.markdown(f"**[{title}]({url})**")
                        if desc and "[Removed]" not in desc:
                            st.caption(desc[:220])
                        st.caption(f"{source} · {pub_at}")
                        st.markdown("---")


# ─────────────────────────────────────────────────
# PAGE: AI BRIEFING
# ─────────────────────────────────────────────────
elif page == "🤖 AI Briefing":
    st.title("🤖 AI Market Briefing")
    st.caption("Daily market analysis powered by Claude AI (with OpenAI and Gemini fallback)")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        generate_btn = st.button("✨ Generate Today's Briefing", type="primary", use_container_width=True)
    with col_info:
        if st.session_state.get("briefing"):
            st.success("Today's briefing is ready — scroll down to read it, or click to regenerate.")
        else:
            st.info("Click to generate today's AI market briefing (takes ~30–60 seconds).")

    # Show AI key status
    with st.expander("AI Provider Status"):
        st.markdown(f"🟢 **Claude (Primary):** {'Configured ✓' if ANTHROPIC_API_KEY else '❌ Missing ANTHROPIC_API_KEY'}")
        st.markdown(f"🟡 **OpenAI (Secondary):** {'Configured ✓' if OPENAI_API_KEY else '❌ Missing OPENAI_API_KEY'}")
        st.markdown(f"🟠 **Gemini (Fallback):** {'Configured ✓' if GEMINI_API_KEY else '❌ Missing GEMINI_API_KEY'}")

    if generate_btn:
        with st.spinner("🧠 Fetching market data and generating briefing..."):
            market_data = {
                "gold":    current_price("GC=F"),
                "silver":  current_price("SI=F"),
                "usd_lkr": current_price("LKR=X"),
                "sp500":   current_price("^GSPC"),
                "vix":     current_price("^VIX"),
                "oil":     current_price("BZ=F"),
                "sensex":  current_price("^BSESN"),
                "nifty":   current_price("^NSEI"),
                "dxy":     current_price("DX-Y.NYB"),
                "nasdaq":  current_price("^IXIC"),
            }
            briefing_text, model_used = generate_briefing(market_data)

        if briefing_text and "ERROR" not in briefing_text and "failed" not in briefing_text.lower()[:50]:
            st.success(f"✅ Briefing generated by **{model_used}**")
            st.session_state["briefing"]   = briefing_text
            st.session_state["model_used"] = model_used
        else:
            st.error(briefing_text)

    # Display briefing from session state only (file system not reliable on cloud)
    briefing_to_show = st.session_state.get("briefing")
    model_label      = st.session_state.get("model_used", "")

    if briefing_to_show:
        st.markdown("---")
        if model_label:
            st.caption(f"Generated by: {model_label}")
        st.markdown(briefing_to_show)


# ─────────────────────────────────────────────────
# PAGE: ABOUT
# ─────────────────────────────────────────────────
elif page == "ℹ️ About":
    st.title("ℹ️ About InvestSmart")

    st.markdown("""
## What is InvestSmart?

InvestSmart is an AI-powered investment intelligence platform built specifically for Sri Lankan investors.
It monitors global market factors that affect the Colombo Stock Exchange (CSE), gold, silver, and bonds —
and generates daily AI briefings to help you make better-informed investment decisions.

## Data Sources

| Source | What We Use It For |
|--------|--------------------|
| Yahoo Finance | 40+ tickers — gold, silver, CSE indices, forex, global markets |
| FRED (Federal Reserve) | US macro data: interest rates, inflation, yield curve |
| World Bank Open API | Sri Lanka macro: GDP, CPI, FDI, remittances |
| NewsAPI | 6 categories of financial news |

## AI Technology

| Priority | Model | Purpose |
|----------|-------|---------|
| 1st | Claude claude-sonnet-4-6 (Anthropic) | Daily briefings, sector analysis |
| 2nd | GPT-4o (OpenAI) | Fallback for briefings |
| 3rd | Gemini 1.5 Flash (Google) | Free fallback |

## Platform Architecture

- **Frontend:** Streamlit (Python web framework)
- **Hosting:** Streamlit Community Cloud (free)
- **Database:** Supabase PostgreSQL (free 500MB)

## Disclaimer

InvestSmart is for **informational purposes only**. Nothing on this platform constitutes
investment advice. Always do your own research and consult a licensed financial advisor
before making investment decisions.

---
*Built for Sri Lankan investors · MVP Version 1.0*
""")
