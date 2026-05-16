# Graph Report - .  (2026-04-30)

## Corpus Check
- Corpus is ~9,381 words - fits in a single context window. You may not need a graph.

## Summary
- 93 nodes · 127 edges · 13 communities detected
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_CSE Board & Premium Access|CSE Board & Premium Access]]
- [[_COMMUNITY_Core App Architecture|Core App Architecture]]
- [[_COMMUNITY_Data Fetching & Utilities|Data Fetching & Utilities]]
- [[_COMMUNITY_GitHub Push Scripts|GitHub Push Scripts]]
- [[_COMMUNITY_Database CRUD Operations|Database CRUD Operations]]
- [[_COMMUNITY_CSE Market & Watchlist|CSE Market & Watchlist]]
- [[_COMMUNITY_OAuth Authentication|OAuth Authentication]]
- [[_COMMUNITY_Python GitHub Deployer|Python GitHub Deployer]]
- [[_COMMUNITY_Ticker Validation|Ticker Validation]]
- [[_COMMUNITY_Price Fetching|Price Fetching]]
- [[_COMMUNITY_AI Briefing Generation|AI Briefing Generation]]
- [[_COMMUNITY_CSE WebSocket Worker|CSE WebSocket Worker]]
- [[_COMMUNITY_Neo4j Integration|Neo4j Integration]]

## God Nodes (most connected - your core abstractions)
1. `app.py (InvestSmart Streamlit Dashboard)` - 13 edges
2. `get_user()` - 11 edges
3. `page_cse_market()` - 10 edges
4. `GitHub API (Push/Deploy)` - 7 edges
5. `fetch_cse_board()` - 6 edges
6. `is_paid_user()` - 5 edges
7. `_do_fetch_cse_board()` - 5 edges
8. `show_auth_page()` - 4 edges
9. `db_get_cse_history()` - 4 edges
10. `_ensure_cse_ws()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `deploy.html (HTML Deployment Template)` --conceptually_related_to--> `app.py (InvestSmart Streamlit Dashboard)`  [INFERRED]
  deploy.html → app.py
- `app.py (InvestSmart Streamlit Dashboard)` --references--> `Streamlit`  [EXTRACTED]
  app.py → requirements.txt
- `app.py (InvestSmart Streamlit Dashboard)` --references--> `yfinance`  [EXTRACTED]
  app.py → requirements.txt
- `app.py (InvestSmart Streamlit Dashboard)` --references--> `Plotly`  [EXTRACTED]
  app.py → requirements.txt
- `app.py (InvestSmart Streamlit Dashboard)` --references--> `Anthropic Claude API`  [EXTRACTED]
  app.py → requirements.txt

## Communities

### Community 0 - "CSE Board & Premium Access"
Cohesion: 0.14
Nodes (15): _cse_board_free(), _cse_board_paid(), _do_fetch_cse_board(), _ensure_cse_ws(), fetch_cse_board(), fetch_cse_indices(), get_profile(), is_paid_user() (+7 more)

### Community 1 - "Core App Architecture"
Cohesion: 0.16
Nodes (14): Anthropic Claude API, app.py (InvestSmart Streamlit Dashboard), Authentication System (Supabase + OAuth), CSE Stock Module (Colombo Stock Exchange), deploy.html (HTML Deployment Template), Native JavaScript Auto-Refresh, OpenAI GPT-4o API, Plotly (+6 more)

### Community 2 - "Data Fetching & Utilities"
Cohesion: 0.17
Nodes (1): app.py \u2014 InvestSmart v2.0 Streamlit dashboard + full authentication for CSE

### Community 3 - "GitHub Push Scripts"
Cohesion: 0.18
Nodes (3): GitHub API (Push/Deploy), push_to_github.py (GitHub Auto-Deploy Helper), requirements.txt (Python Dependencies)

### Community 4 - "Database CRUD Operations"
Cohesion: 0.2
Nodes (10): db_delete_briefing(), db_delete_note(), db_get_briefings(), db_get_notes(), db_get_watchlist(), db_remove_watchlist(), db_save_briefing(), db_save_note() (+2 more)

### Community 5 - "CSE Market & Watchlist"
Cohesion: 0.22
Nodes (10): db_add_watchlist(), db_get_cse_history(), db_record_cse_prices(), fetch_cse_stock_history(), fmt_index(), is_logged_in(), page_cse_market(), Store CSE daily prices to Supabase cse_price_history table. (+2 more)

### Community 6 - "OAuth Authentication"
Cohesion: 0.33
Nodes (6): _google_btn(), _handle_oauth_callback(), _load_profile(), Render Google OAuth button. Shows setup notice if not configured., Full-screen auth page: Sign In \u00b7 Create Account \u00b7 Phone \u00b7 Reset., show_auth_page()

### Community 7 - "Python GitHub Deployer"
Cohesion: 0.53
Nodes (5): b64(), get_sha(), main(), push_file(), push_to_github.py  -  InvestSmart auto-deploy helper Double-click this file (or

### Community 8 - "Ticker Validation"
Cohesion: 1.0
Nodes (2): Allow only safe ticker characters to prevent injection., _valid_ticker()

### Community 9 - "Price Fetching"
Cohesion: 1.0
Nodes (2): current_price(), fetch_price()

### Community 10 - "AI Briefing Generation"
Cohesion: 1.0
Nodes (2): call_claude_briefing(), generate_briefing()

### Community 11 - "CSE WebSocket Worker"
Cohesion: 1.0
Nodes (2): _cse_ws_worker(), Daemon: SockJS+STOMP connection to wss://www.cse.lk live feed.

### Community 12 - "Neo4j Integration"
Cohesion: 1.0
Nodes (1): Neo4j Graph Database

## Knowledge Gaps
- **27 isolated node(s):** `app.py \u2014 InvestSmart v2.0 Streamlit dashboard + full authentication for CSE`, `Allow only safe ticker characters to prevent injection.`, `Render Google OAuth button. Shows setup notice if not configured.`, `Full-screen auth page: Sign In \u00b7 Create Account \u00b7 Phone \u00b7 Reset.`, `Returns True if current user has Premium tier.` (+22 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Data Fetching & Utilities`** (12 nodes): `app.py`, `do_logout()`, `fetch_fred()`, `fetch_news()`, `fetch_worldbank()`, `fmt_lkr()`, `_get_sb()`, `get_secret()`, `_init_state()`, `metric_delta()`, `app.py \u2014 InvestSmart v2.0 Streamlit dashboard + full authentication for CSE`, `show_premium_gate()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Ticker Validation`** (2 nodes): `Allow only safe ticker characters to prevent injection.`, `_valid_ticker()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Price Fetching`** (2 nodes): `current_price()`, `fetch_price()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `AI Briefing Generation`** (2 nodes): `call_claude_briefing()`, `generate_briefing()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `CSE WebSocket Worker`** (2 nodes): `_cse_ws_worker()`, `Daemon: SockJS+STOMP connection to wss://www.cse.lk live feed.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Neo4j Integration`** (1 nodes): `Neo4j Graph Database`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `app.py (InvestSmart Streamlit Dashboard)` connect `Core App Architecture` to `GitHub Push Scripts`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `push_to_github.py (GitHub Auto-Deploy Helper)` connect `GitHub Push Scripts` to `Core App Architecture`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `GitHub API (Push/Deploy)` (e.g. with `push_autorefresh_fix.js` and `push_final.js`) actually correct?**
  _`GitHub API (Push/Deploy)` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `app.py \u2014 InvestSmart v2.0 Streamlit dashboard + full authentication for CSE`, `Allow only safe ticker characters to prevent injection.`, `Render Google OAuth button. Shows setup notice if not configured.` to the rest of the system?**
  _27 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `CSE Board & Premium Access` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._