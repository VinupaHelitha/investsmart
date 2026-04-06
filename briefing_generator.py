"""
briefing_generator.py — InvestSmart
Generates the daily AI market briefing.

AI Priority Order:
  1. Anthropic Claude (claude-sonnet-4-6) — BEST quality, you have paid API
  2. OpenAI GPT-4o — also excellent, fallback or secondary tasks
  3. Google Gemini 1.5 Flash — free backup if both above fail

Also handles:
  - Geopolitical event monitoring via GDELT
  - Investor behaviour prediction
  - Saving briefings to Supabase
"""

import os
import json
import requests
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────
# CONFIGURATION — API Keys
# ─────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")   # fallback only
SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY      = os.getenv("SUPABASE_KEY", "")
NEO4J_URI         = os.getenv("NEO4J_URI", "")
NEO4J_USERNAME    = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD    = os.getenv("NEO4J_PASSWORD", "")

# ─────────────────────────────────────────────────
# AI CLIENT SETUP
# ─────────────────────────────────────────────────

def call_claude(prompt: str, max_tokens: int = 2500) -> str:
    """
    Call Anthropic Claude API (claude-sonnet-4-6).
    Best quality for financial analysis and reasoning.
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("No Anthropic API key")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except ImportError:
        raise ImportError("Run: pip install anthropic")


def call_openai(prompt: str, max_tokens: int = 2500) -> str:
    """
    Call OpenAI GPT-4o API.
    Excellent quality — used as secondary AI or for specific tasks.
    """
    if not OPENAI_API_KEY:
        raise ValueError("No OpenAI API key")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior investment analyst specialising in the Colombo Stock Exchange (CSE) and Sri Lankan financial markets."
                },
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except ImportError:
        raise ImportError("Run: pip install openai")


def call_gemini(prompt: str) -> str:
    """
    Call Google Gemini 1.5 Flash API.
    Free backup — used only if Claude and OpenAI both fail.
    """
    if not GEMINI_API_KEY:
        raise ValueError("No Gemini API key")
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt, generation_config={"temperature": 0.3, "max_output_tokens": 2500})
    return response.text


def call_ai(prompt: str, max_tokens: int = 2500) -> tuple[str, str]:
    """
    Intelligent AI router — tries each provider in priority order.
    Returns (response_text, model_name_used)
    """
    attempts = [
        ("claude-sonnet-4-6",    lambda: call_claude(prompt, max_tokens)),
        ("gpt-4o",               lambda: call_openai(prompt, max_tokens)),
        ("gemini-1.5-flash",     lambda: call_gemini(prompt)),
    ]

    for model_name, fn in attempts:
        try:
            print(f"  [AI] Trying {model_name}...")
            result = fn()
            print(f"  [AI] ✓ Success with {model_name}")
            return result, model_name
        except Exception as e:
            print(f"  [AI] ✗ {model_name} failed: {e}")
            continue

    return "ERROR: All AI providers failed. Check your API keys.", "none"


# ─────────────────────────────────────────────────
# SUPABASE HELPER
# ─────────────────────────────────────────────────
def supabase_insert(table: str, data: dict) -> bool:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print(f"[SUPABASE] No credentials — skipping save to '{table}'")
        return False
    try:
        url     = f"{SUPABASE_URL}/rest/v1/{table}"
        headers = {
            "apikey":        SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type":  "application/json",
            "Prefer":        "return=minimal",
        }
        r = requests.post(url, headers=headers, json=data, timeout=15)
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"[SUPABASE] Error: {e}")
        return False


# ─────────────────────────────────────────────────
# NEO4J — Behaviour Graph
# ─────────────────────────────────────────────────
def neo4j_store_event(event: str, prediction: str, outcome: str = "pending"):
    """
    Store a geopolitical event and its predicted market reaction in Neo4j.
    Over time this builds a knowledge graph: Events → Reactions → Outcomes.
    The AI gets smarter with each event recorded.
    """
    if not NEO4J_URI or not NEO4J_PASSWORD:
        print("[NEO4J] No credentials — skipping graph storage")
        return False
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

        with driver.session() as session:
            session.run("""
                MERGE (e:Event {name: $event, date: $date})
                SET e.prediction = $prediction,
                    e.outcome = $outcome,
                    e.updated_at = $now

                MERGE (m:Market {name: 'CSE'})
                MERGE (e)-[:IMPACTS]->(m)
                SET m.last_event = $event
            """, {
                "event":      event[:200],
                "date":       str(date.today()),
                "prediction": prediction[:500],
                "outcome":    outcome,
                "now":        datetime.now().isoformat(),
            })

        driver.close()
        print(f"[NEO4J] ✓ Event stored in graph: {event[:60]}")
        return True
    except ImportError:
        print("[NEO4J] neo4j driver not installed. Run: pip install neo4j")
        return False
    except Exception as e:
        print(f"[NEO4J] Error storing event: {e}")
        return False


def neo4j_get_similar_events(event_keywords: list) -> str:
    """
    Query Neo4j for similar past events and their actual market outcomes.
    This gives the AI real historical context when making predictions.
    """
    if not NEO4J_URI or not NEO4J_PASSWORD:
        return "No historical event data available yet (Neo4j not connected)."
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

        results = []
        with driver.session() as session:
            for keyword in event_keywords[:3]:
                records = session.run("""
                    MATCH (e:Event)
                    WHERE toLower(e.name) CONTAINS toLower($keyword)
                    RETURN e.name AS event, e.date AS date,
                           e.prediction AS prediction, e.outcome AS outcome
                    ORDER BY e.date DESC
                    LIMIT 3
                """, {"keyword": keyword})

                for r in records:
                    results.append(
                        f"Event: {r['event']} ({r['date']})\n"
                        f"Prediction: {r['prediction']}\n"
                        f"Actual Outcome: {r['outcome']}"
                    )

        driver.close()
        return "\n\n".join(results) if results else "No similar historical events found yet."
    except Exception as e:
        return f"Neo4j query error: {e}"


# ─────────────────────────────────────────────────
# LOAD TODAY'S DATA
# ─────────────────────────────────────────────────
def load_todays_data() -> dict:
    filename = f"data_snapshot_{date.today()}.json"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[DATA] Loaded from {filename}")
            return data
        except Exception as e:
            print(f"[DATA] Error reading {filename}: {e}")

    print("[DATA] Snapshot not found — collecting fresh data...")
    from data_collector import collect_all
    return collect_all()


# ─────────────────────────────────────────────────
# FORMAT DATA SUMMARY
# ─────────────────────────────────────────────────
def build_data_summary(data: dict) -> str:
    mp    = data.get("market_prices", {})
    macro = data.get("us_macro", {})
    sl    = data.get("sl_macro", {})
    news  = data.get("news", [])

    def p(name, prefix="", suffix=""):
        d = mp.get(name, {})
        if d.get("close") is not None:
            chg  = d.get("change_pct", 0) or 0
            sign = "+" if chg >= 0 else ""
            arrow = "▲" if chg >= 0 else "▼"
            return f"{prefix}{d['close']:,.2f}{suffix}  {arrow}{sign}{chg:.2f}%"
        return "N/A"

    def m(name, suffix=""):
        d = macro.get(name, {})
        return f"{d['value']}{suffix}" if d.get("value") is not None else "N/A"

    def sl_v(name, suffix=""):
        d = sl.get(name, {})
        val  = d.get("value")
        year = d.get("year", "")
        return f"{val:.2f}{suffix} ({year})" if val is not None else "N/A"

    yc     = macro.get("yield_curve_spread", {}).get("value")
    yc_sig = "⚠️ INVERTED — recession risk signal" if yc and yc < 0 else ("Normal (positive spread)" if yc else "N/A")

    headlines = "\n".join(
        f"  • {a['title']}  [{a.get('source_name','?')}]"
        for a in news[:15] if a.get("title")
    )

    return f"""
════════════════════════════════════════════════
MARKET DATA — {datetime.now().strftime('%A, %d %B %Y')}
════════════════════════════════════════════════

PRECIOUS METALS & COMMODITIES
  Gold (USD/oz):         {p('gold', '$')}
  Silver (USD/oz):       {p('silver', '$')}
  Gold in LKR (est.):    {p('gold_lkr', 'LKR ', '/oz')}
  Oil Brent (USD/bbl):   {p('oil_brent', '$')}
  Copper (USD/lb):       {p('copper', '$')}

US MARKETS
  S&P 500:               {p('sp500')}
  NASDAQ:                {p('nasdaq')}
  Dow Jones:             {p('dow')}
  VIX (Fear Index):      {p('vix')}

ASIAN MARKETS
  BSE Sensex (India):    {p('sensex')}
  Nifty 50 (India):      {p('nifty')}
  Hang Seng (HK):        {p('hang_seng')}
  Nikkei 225 (Japan):    {p('nikkei')}

EUROPEAN MARKETS
  FTSE 100 (UK):         {p('ftse100')}
  DAX (Germany):         {p('dax')}

FOREX
  USD / LKR:             {p('usd_lkr')}  LKR per USD
  USD Index (DXY):       {p('usd_index')}
  EUR / USD:             {p('eur_usd')}
  USD / INR:             {p('usd_inr')}

US MACRO (Federal Reserve — FRED)
  Fed Funds Rate:        {m('fed_funds_rate', '%')}
  10Y Treasury Yield:    {m('treasury_10y', '%')}
  2Y Treasury Yield:     {m('treasury_2y', '%')}
  Yield Curve (10Y-2Y):  {m('yield_curve_spread', '%')} — {yc_sig}
  10Y Real Yield (TIPS): {m('real_yield_10y', '%')}
  Breakeven Inflation:   {m('breakeven_inflation_10y', '%')}
  US CPI (Inflation):    {m('us_cpi')}
  US Unemployment:       {m('us_unemployment', '%')}
  US Money Supply (M2):  ${m('us_m2')} billion

SRI LANKA MACRO (World Bank)
  GDP Growth Rate:       {sl_v('gdp_growth', '%')}
  CPI Inflation:         {sl_v('inflation_cpi', '%')}
  Remittances:           {sl_v('remittances')}
  FDI Inflows:           {sl_v('fdi_inflows')}

TOP NEWS HEADLINES
{headlines or '  (No news available — check NEWS_API_KEY)'}

════════════════════════════════════════════════
"""


# ────────────────────────────────────────────────
# GENERATE DAILY BRIEFING
# ─────────────────────────────────────────────────
def generate_daily_briefing(data_summary: str) -> tuple[str, str]:
    """
    Generate the full market briefing using the best available AI.
    Returns (briefing_text, model_used).
    """
    today = datetime.now().strftime("%A, %d %B %Y")

    prompt = f"""You are a senior investment analyst and economist with deep expertise in:
- Colombo Stock Exchange (CSE) and Sri Lankan financial markets
- Emerging market investing and macroeconomics
- Precious metals (gold and silver) as an asset class
- Global macro investing and geopolitical risk analysis

Your audience: Sri Lankan retail investors who need to understand what is happening globally and how it directly affects their investments in the CSE and in gold/silver.

Using ONLY the data provided below, write today's comprehensive market briefing. Reference specific numbers. Do not speculate beyond what the data shows.

{data_summary}

Write the briefing using EXACTLY this structure:

# 📊 Daily Market Briefing — {today}

## 1. CSE & Sri Lanka Outlook
*(Most important section — 3 paragraphs)*

**Paragraph 1 — Currency & Foreign Investor Impact:**
What does today's USD/LKR rate mean for CSE? Is the LKR strengthening or weakening, and how does this affect foreign investor risk appetite for emerging market stocks like CSE? Reference the actual USD/LKR number.

**Paragraph 2 — Sector Impact Analysis:**
Which CSE sectors are most affected today and why? Work through: (a) energy/oil impact on import costs and local companies, (b) USD strength effect on plantation exporters (tea, rubber) and garment exporters who earn in foreign currency, (c) gold price in LKR for Sri Lankan gold investors.

**Paragraph 3 — Sri Lanka Macro Context:**
What do the World Bank macro figures (GDP growth, inflation, FDI, remittances) tell us about Sri Lanka's investment environment right now?

## 2. Global Markets
*(2 paragraphs)*
US market performance and what VIX is signalling about global risk appetite. Asian market movements and their relevance — India's Sensex is particularly important for Sri Lanka as a regional peer market.

## 3. Gold & Silver Analysis
*(2 paragraphs)*
**Paragraph 1:** Today's price drivers — what is moving gold right now? Specifically: real yield direction, USD strength/weakness, and any geopolitical factors.
**Paragraph 2:** Gold in LKR terms — since LKR depreciation amplifies gold returns for Sri Lankan investors, what does today's combined gold price + LKR rate mean practically?

## 4. Bonds & Interest Rates
*(1 paragraph)*
Fed rate stance, Treasury yield movement, yield curve status (inverted/normal), and what this means for equity valuations and bond investors.

## 5. Key Active Market Factors Today
*(7 bullet points — reference actual numbers)*
List the 7 most important factors from the data that are actively driving markets today. Each bullet should name the factor, give the number, and state the impact direction.

## 6. CSE Sector Impact Summary
*(One line per sector)*
- 🏦 Banking sector:
- 🌿 Plantation sector (tea/rubber exports):
- 🏨 Tourism & hospitality:
- 🏭 Manufacturing & import-dependent:
- ⚡ Energy sector:
- 📦 Consumer goods:

## 7. Tomorrow's Watch List
*(5 bullet points)*
Key data releases, Fed communications, geopolitical events, or technical price levels to monitor tomorrow.

## 8. Sentiment Scorecard
| Asset | Sentiment | Key Reason |
|-------|-----------|------------|
| CSE (overall) | BULLISH / NEUTRAL / BEARISH | |
| Gold | BULLISH / NEUTRAL / BEARISH | |
| Silver | BULLISH / NEUTRAL / BEARISH | |
| Global Equities | BULLISH / NEUTRAL / BEARISH | |
| LKR | STRENGTHENING / STABLE / WEAKENING | |

**Overall Market Mood: [STRONGLY BULLISH / BULLISH / NEUTRAL / BEARISH / STRONGLY BEARISH]**
*One sentence justification.*

---
*Briefing generated by InvestSmart AI | Data sources: Yahoo Finance, FRED (Federal Reserve), World Bank | For information only — not investment advice*"""

    return call_ai(prompt, max_tokens=2500)


# ─────────────────────────────────────────────────
# GEOPOLITICAL EVENT MONITOR (GDELT)
# ─────────────────────────────────────────────────
def get_geopolitical_events() -> list:
    """Query GDELT for high-impact events in the last 24 hours. Completely free."""
    try:
        url = (
            "https://api.gdeltproject.org/api/v2/doc/doc"
            "?query=conflict%20OR%20war%20OR%20sanctions%20OR%20crisis%20OR%20election"
            "&mode=artlist&maxrecords=15&format=json&timespan=1d&sort=toneasc"
        )
        r = requests.get(url, timeout=15)
        data = r.json()
        return [
            {
                "title":  a.get("title", ""),
                "url":    a.get("url", ""),
                "domain": a.get("domain", ""),
                "tone":   a.get("tone", 0),
            }
            for a in data.get("articles", [])[:8]
        ]
    except Exception as e:
        print(f"[GDELT] Error: {e}")
        return []


# ─────────────────────────────────────────────────
# BEHAVIOUR PREDICTION ENGINE
# ─────────────────────────────────────────────────
def predict_investor_behaviour(event: str, data_summary: str) -> tuple[str, str]:
    """
    Predict how CSE investors will likely react to a geopolitical/macro event.
    Queries Neo4j for historical parallels first, then calls Claude for analysis.
    Returns (prediction_text, model_used).
    """
    # Extract keywords from event for Neo4j search
    keywords = [w for w in event.lower().split() if len(w) > 4][:5]

    # Get historical parallels from Neo4j graph
    historical_context = neo4j_get_similar_events(keywords)

    prompt = f"""You are an expert in Sri Lankan stock market investor psychology and the Colombo Stock Exchange (CSE).

CURRENT EVENT DETECTED:
"{event}"

CURRENT MARKET CONTEXT (key data):
{data_summary[:1200]}

HISTORICAL PARALLELS FROM OUR KNOWLEDGE GRAPH:
{historical_context}

Analyse this event using the causal chain framework. Be specific and quantitative where possible.

## ⚠️ Event Alert: {event[:100]}

### Causal Chain Analysis
Walk through each transmission channel step by step:

1. **Oil & Commodity Channel**
   → Does this event affect oil supply or prices?
   → Impact on Sri Lanka's import bill (Sri Lanka imports ~100% of its oil)
   → Impact on LKR (higher import costs = more USD demand = LKR pressure)

2. **USD/Safe-Haven Channel**
   → Does this event strengthen or weaken the USD?
   → How does USD movement affect gold prices?
   → Gold in LKR = Gold(USD) × USD/LKR — both directions amplify for Sri Lankans

3. **Global Risk Appetite Channel**
   → Does this event increase global risk aversion (VIX)?
   → When global VIX rises, do foreign investors exit emerging markets like CSE?
   → Which CSE sectors get hit first vs which become defensive?

4. **Trade & Remittance Channel**
   → Are Sri Lanka's export markets (EU, USA, Middle East, India) affected?
   → Middle East events particularly affect remittances from Sri Lankan migrant workers

### Predicted CSE Investor Behaviour

**Foreign institutional investors:** (buy / sell / hold — and why)
**Sri Lankan retail investors:** (typical herding behaviour based on past patterns)
**CSE sectors most exposed:** (specific sectors + direction)
**CSE sectors that may benefit:** (if any — e.g., exporters benefit from LKR weakness)

### Gold & Silver Prediction
Specific impact on gold and silver prices in USD, and in LKR (critical for Sri Lankan investors).

### Historical Parallel
{f"Based on our graph data: {historical_context[:300]}" if "No similar" not in historical_context else "No direct historical parallel found — reasoning from fundamentals."}

### Confidence Level: [HIGH / MEDIUM / LOW]
Reason for this confidence level.

### Key Numbers to Watch
What specific price levels or data points would confirm or contradict this prediction?

*This is AI-generated analysis for informational purposes only. Not investment advice.*"""

    result, model = call_ai(prompt, max_tokens=1500)
    return result, model


# ─────────────────────────────────────────────────
# SAVE BRIEFING
# ─────────────────────────────────────────────────
def save_briefing(briefing_text: str, data_summary: str, model_used: str):
    today = str(date.today())

    # Save to local file
    filename = f"briefing_{today}.md"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(briefing_text)
        print(f"[FILE] Briefing saved to {filename}")
    except Exception as e:
        print(f"[FILE] Error saving: {e}")

    # Save to Supabase
    supabase_insert("daily_briefings", {
        "date":          today,
        "briefing_text": briefing_text,
        "data_summary":  data_summary[:3000],
        "generated_at":  datetime.now().isoformat(),
        "model_used":    model_used,
    })


# ─────────────────────────────────────────────────
# MASTER FUNCTION
# ─────────────────────────────────────────────────
def run_daily_briefing():
    print("=" * 60)
    print("InvestSmart — Daily Briefing Generator")
    print(f"{datetime.now().strftime('%A %d %B %Y %H:%M:%S')}")
    print("=" * 60)

    # 1. Load data
    print("\n[1/4] Loading market data...")
    data = load_todays_data()

    # 2. Build summary
    print("\n[2/4] Formatting data...")
    data_summary = build_data_summary(data)
    print(data_summary)

    # 3. Generate main briefing (Claude preferred)
    print("\n[3/4] Generating AI briefing...")
    briefing, model_used = generate_daily_briefing(data_summary)
    print(f"\n  Model used: {model_used}")
    print(f"  Briefing length: {len(briefing)} chars")

    # 4. Check GDELT for geopolitical events
    print("\n[4/4] Checking for geopolitical events (GDELT)...")
    events = get_geopolitical_events()

    if events:
        major_events = [e for e in events if e.get("tone", 0) < -4]
        print(f"  Found {len(events)} events, {len(major_events)} high-impact")

        if major_events:
            top_event = major_events[0]
            print(f"  ⚠️ Major event: {top_event['title'][:80]}")
            print("  Generating behaviour prediction...")

            prediction, pred_model = predict_investor_behaviour(
                top_event["title"], data_summary
            )

            # Store in Neo4j graph
            neo4j_store_event(top_event["title"], prediction)

            # Save to Supabase
            supabase_insert("behaviour_predictions", {
                "date":       str(date.today()),
                "event":      top_event["title"],
                "prediction": prediction,
                "event_url":  top_event.get("url", ""),
                "model_used": pred_model,
                "created_at": datetime.now().isoformat(),
            })

            # Append to briefing
            briefing += f"\n\n---\n\n{prediction}"
    else:
        print("  No major events detected today.")

    # 5. Save everything
    print("\n[SAVING] Saving briefing...")
    save_briefing(briefing, data_summary, model_used)

    print("\n" + "=" * 60)
    print(f"✓ Briefing complete — model: {model_used}")
    print("=" * 60)
    return briefing


if __name__ == "__main__":
    briefing = run_daily_briefing()
    print("\n\n" + "=" * 60)
    print("FULL BRIEFING:")
    print("=" * 60)
    print(briefing)
