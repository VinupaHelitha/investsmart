"""
app.py \u2014 InvestSmart v2.0
Streamlit dashboard + full authentication for CSE & global market intelligence.

Pages (Free):    Dashboard \u00b7 Gold & Silver \u00b7 Global Markets \u00b7 News Feed \u00b7 About
Pages (Premium): AI Briefing \u00b7 Watchlist \u00b7 My Reports  (require login)

Auth:  Supabase \u2014 Email/Password \u00b7 Google OAuth \u00b7 Phone SMS OTP
"""

import os
import re
import json
import random
import logging
import string as _string_mod
import threading as _threading
import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import html as _html
import time as _time

logger = logging.getLogger(__name__)

import streamlit.components.v1 as _components_v1
_AUTOREFRESH_OK = False  # Use native JS approach instead

try:
    from supabase import create_client
    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False

load_dotenv()

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# SECRETS
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
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
APP_URL           = get_secret("APP_URL", "https://investsmart-uznzrnzf4rdkmthkmtuofc.streamlit.app")

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PAGE CONFIG
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
st.set_page_config(
    page_title="InvestSmart \u2014 CSE Intelligence",
    page_icon="\U0001f4c8",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .main { background-color: #0e1117; }
  .metric-card { background:#1e2130; border-radius:12px; padding:16px 20px; border:1px solid #2d3147; }
  .positive { color:#00d26a; font-weight:600; }
  .negative { color:#ff4b4b; font-weight:600; }
  .neutral  { color:#ffa500; font-weight:600; }
  .section-header { font-size:1.1rem; font-weight:700; color:#a0a8c8; letter-spacing:.05em;
                    text-transform:uppercase; margin:1.5rem 0 .5rem 0; }
  div[data-testid="stMetric"] { background:#1e2130; border-radius:10px; padding:12px; }
  div[data-testid="stMetric"] label { font-size:0.78rem !important; }

  /* \u2500\u2500 Auth \u2500\u2500 */
  .auth-logo { text-align:center; padding:24px 0 8px 0; }
  .auth-logo .icon { font-size:3rem; }
  .auth-logo .brand { font-size:1.7rem; font-weight:800; color:#e0e4ff; margin-top:4px; }
  .auth-logo .tagline { color:#7b82a8; font-size:0.88rem; margin-top:2px; }
  .or-divider { display:flex; align-items:center; gap:12px; margin:14px 0; color:#4a5070; font-size:0.8rem; }
  .or-divider::before,.or-divider::after { content:""; flex:1; height:1px; background:#2a2f4a; }
  .google-btn-wrap a { text-decoration:none !important; }
  .google-btn {
    display:flex; align-items:center; justify-content:center; gap:10px;
    background:#ffffff; color:#333333; border-radius:10px; padding:11px 16px;
    font-weight:600; font-size:14px; cursor:pointer;
    border:1px solid #cccccc; width:100%; box-sizing:border-box;
    transition:background .15s;
  }
  .google-btn:hover { background:#f0f0f0; }
  .user-card {
    display:flex; align-items:center; gap:10px; padding:10px 12px;
    background:#161b2e; border-radius:12px; border:1px solid #2a2f4a; margin-bottom:10px;
  }
  .user-avatar {
    width:38px; height:38px; border-radius:50%; background:#3b4fd9;
    display:flex; align-items:center; justify-content:center;
    color:white; font-weight:800; font-size:1rem; flex-shrink:0;
  }
  .user-name  { font-weight:700; color:#e0e4ff; font-size:0.9rem; line-height:1.2; }
  .user-email { color:#7b82a8; font-size:0.73rem; }
  .badge-free    { display:inline-block; background:#1e2440; color:#7b8cde;
                   padding:2px 10px; border-radius:20px; font-size:0.72rem; }
  .badge-premium { display:inline-block; background:#2a1f40; color:#c084fc;
                   padding:2px 10px; border-radius:20px; font-size:0.72rem; }
  .premium-gate  { text-align:center; padding:60px 20px; }
  .premium-gate h2 { color:#c084fc; font-size:1.6rem; margin-bottom:8px; }
  .premium-gate p  { color:#7b82a8; font-size:1rem; }
  .ticker-row { display:flex; align-items:center; padding:10px 4px;
                border-bottom:1px solid #1e2440; gap:10px; }
</style>
""", unsafe_allow_html=True)

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# FORMATTERS
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def fmt_lkr(value: float | None) -> str:
    if value is None: return "N/A"
    if value >= 1_000_000: return f"LKR {value/1_000_000:.2f}M"
    if value >= 1_000:     return f"LKR {value:,.0f}"
    return f"LKR {value:,.2f}"

def fmt_index(value: float | None) -> str:
    if value is None: return "N/A"
    if value >= 100_000: return f"{value/1_000:.1f}K"
    if value >= 1_000:   return f"{value:,.0f}"
    return f"{value:,.2f}"


def _valid_ticker(t: str) -> bool:
    """Allow only safe ticker characters to prevent injection."""
    import re
    return bool(re.match(r'^[A-Z0-9\.\^=\-]{1,20}$', t.strip().upper()))

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# SUPABASE CLIENT
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@st.cache_resource
def _get_sb():
    if not _SUPABASE_OK or not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

_sb = _get_sb()

# \u2500\u2500 Auth state helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def _init_state():
    defaults = {
        "auth_user": None, "auth_session": None, "auth_profile": None,
        "show_auth": False, "auth_tab": 0,
        "phone_step": 1, "phone_number": "",
        "auth_error": "", "auth_success": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _load_profile():
    user = st.session_state.get("auth_user")
    if not user or not _sb: return
    try:
        r = _sb.table("profiles").select("*").eq("id", user.id).maybe_single().execute()
        st.session_state["auth_profile"] = r.data or {}
    except Exception as e:
        logger.warning(f"Failed to load user profile: {e}")
        st.session_state["auth_profile"] = {}

def _handle_oauth_callback():
    params = st.query_params
    if "code" in params and not st.session_state.get("auth_user") and _sb:
        try:
            resp = _sb.auth.exchange_code_for_session({"auth_code": params["code"]})
            if resp.session:
                st.session_state["auth_user"]    = resp.user
                st.session_state["auth_session"] = resp.session
                st.session_state["show_auth"]    = False
                st.query_params.clear()
                _load_profile()
                st.rerun()
        except Exception as e:
            st.session_state["auth_error"] = f"Sign-in error: {e}"

def is_logged_in() -> bool:
    return st.session_state.get("auth_user") is not None

def get_user():
    return st.session_state.get("auth_user")

def get_profile() -> dict:
    return st.session_state.get("auth_profile") or {}

def do_logout():
    if _sb:
        try: _sb.auth.sign_out()
        except Exception as e:
            logger.warning(f"Error during sign out: {e}")
    for k in ["auth_user", "auth_session", "auth_profile"]:
        st.session_state[k] = None
    st.session_state["show_auth"] = False
    st.rerun()

# \u2500\u2500 DB helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def db_get_watchlist():
    user = get_user()
    if not user or not _sb: return []
    try:
        r = _sb.table("watchlist").select("*").eq("user_id", user.id).order("added_at", desc=True).execute()
        return r.data or []
    except Exception as e:
        logger.error(f"DB error retrieving watchlist: {e}")
        return []

def db_add_watchlist(ticker: str, name: str, category: str = "stock") -> bool:
    user = get_user()
    if not user or not _sb: return False
    try:
        _sb.table("watchlist").upsert({
            "user_id": user.id, "ticker": ticker,
            "ticker_name": name, "category": category
        }).execute()
        return True
    except Exception as e:
        logger.error(f"DB error adding watchlist item: {e}")
        return False

def db_remove_watchlist(ticker: str):
    user = get_user()
    if not user or not _sb: return
    try:
        _sb.table("watchlist").delete().eq("user_id", user.id).eq("ticker", ticker).execute()
    except Exception as e:
        logger.warning(f"Error removing watchlist item: {e}")

# ── Task 4.2: Price Alert Functions ──────────────────────
def db_create_price_alert(ticker: str, alert_type: str, price_threshold: float) -> bool:
    """
    Task 4.2: Create a new price alert for a ticker.
    alert_type: 'above' (alert when price >= threshold) or 'below' (alert when price <= threshold)
    """
    user = get_user()
    if not user or not _sb: return False
    try:
        _sb.table("price_alerts").insert({
            "user_id": user.id,
            "ticker": ticker,
            "alert_type": alert_type,
            "price_threshold": price_threshold,
            "is_active": True
        }).execute()
        return True
    except Exception as e:
        logger.error(f"DB error creating price alert: {e}")
        return False

def db_get_price_alerts():
    """Get all active price alerts for current user."""
    user = get_user()
    if not user or not _sb: return []
    try:
        r = _sb.table("price_alerts").select("*").eq("user_id", user.id).eq("is_active", True).order("created_at", desc=True).execute()
        return r.data or []
    except Exception as e:
        logger.error(f"DB error retrieving price alerts: {e}")
        return []

def db_delete_price_alert(alert_id: str) -> bool:
    """Delete/deactivate a price alert."""
    user = get_user()
    if not user or not _sb: return False
    try:
        _sb.table("price_alerts").update({"is_active": False}).eq("id", alert_id).eq("user_id", user.id).execute()
        return True
    except Exception as e:
        logger.error(f"DB error deleting price alert: {e}")
        return False

def check_price_alerts(board: dict) -> list:
    """
    Task 4.2: Check all active alerts against current prices.
    Returns list of triggered alerts: [{"ticker": "...", "alert_type": "...", "current_price": ..., "threshold": ...}, ...]
    """
    alerts = db_get_price_alerts()
    triggered = []

    for alert in alerts:
        ticker = alert.get("ticker", "").upper()
        if ticker not in board:
            continue

        current_price = board[ticker].get("close", 0)
        threshold = alert.get("price_threshold", 0)
        alert_type = alert.get("alert_type", "above")

        # Check if alert condition is met
        if alert_type == "above" and current_price >= threshold:
            triggered.append({
                "alert_id": alert.get("id"),
                "ticker": ticker,
                "alert_type": alert_type,
                "current_price": current_price,
                "threshold": threshold,
                "company": CSE_STOCKS.get(ticker, (ticker, ""))[0]
            })
        elif alert_type == "below" and current_price <= threshold:
            triggered.append({
                "alert_id": alert.get("id"),
                "ticker": ticker,
                "alert_type": alert_type,
                "current_price": current_price,
                "threshold": threshold,
                "company": CSE_STOCKS.get(ticker, (ticker, ""))[0]
            })

    return triggered

def display_price_alerts_widget(board: dict):
    """
    Task 4.2: Display price alerts management widget in sidebar.
    Shows active alerts, triggered alerts, and form to create new alerts.
    """
    st.markdown("### 🔔 Price Alerts")

    if not get_user():
        st.info("Sign in to create and manage price alerts.")
        return

    # SECTION 1: Create New Alert
    with st.expander("➕ Create Alert", expanded=False):
        col1, col2 = st.columns([2, 1])
        with col1:
            ticker_input = st.selectbox(
                "Ticker", CSE_STOCKS.keys(), key="alert_ticker",
                format_func=lambda t: f"{t} — {CSE_STOCKS[t][0][:25]}"
            )
        with col2:
            alert_type = st.selectbox(
                "Type", ["above", "below"], key="alert_type",
                format_func=lambda x: f"Alert when {'≥' if x == 'above' else '≤'}"
            )

        price_threshold = st.number_input(
            "Price (LKR)", min_value=1.0, step=1.0, key="alert_price",
            value=100.0
        )

        if st.button("✅ Create Alert", use_container_width=True):
            if db_create_price_alert(ticker_input, alert_type, price_threshold):
                st.success(f"✅ Alert created for {ticker_input} at LKR {price_threshold}")
                st.rerun()
            else:
                st.error("Failed to create alert. Try again.")

    st.divider()

    # SECTION 2: Check for Triggered Alerts
    triggered_alerts = check_price_alerts(board)
    if triggered_alerts:
        st.markdown("⚠️ **Triggered Alerts**")
        for ta in triggered_alerts:
            col_t, col_p, col_a = st.columns([2, 2, 1])
            with col_t:
                st.markdown(f"**{ta['ticker']}** — {ta['company'][:20]}")
            with col_p:
                direction = "↑" if ta['alert_type'] == "above" else "↓"
                st.markdown(f"{direction} LKR {ta['current_price']:.2f} (Threshold: {ta['threshold']:.2f})")
            with col_a:
                if st.button("✕", key=f"dismiss_{ta['alert_id']}"):
                    db_delete_price_alert(ta['alert_id'])
                    st.rerun()
        st.divider()

    # SECTION 3: Active Alerts
    active_alerts = db_get_price_alerts()
    if active_alerts:
        st.markdown(f"📋 **Active Alerts** ({len(active_alerts)})")
        for alert in active_alerts:
            ticker = alert.get("ticker", "").upper()
            threshold = alert.get("price_threshold", 0)
            alert_type = alert.get("alert_type", "above")
            company = CSE_STOCKS.get(ticker, (ticker, ""))[0][:20]

            # Get current price if available
            current_price = board.get(ticker, {}).get("close", "—")
            if isinstance(current_price, (int, float)):
                current_price = f"LKR {current_price:.2f}"

            direction = "≥" if alert_type == "above" else "≤"
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;padding:6px;'
                f'background:#1a1a1a;border-radius:4px;margin:4px 0;">'
                f'<span>{ticker} — {company}</span>'
                f'<span style="color:#888;font-size:0.9em">{direction} {threshold:.2f} | Now: {current_price}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

            if st.button("Delete", key=f"delete_{alert.get('id')}", use_container_width=True):
                if db_delete_price_alert(alert.get('id')):
                    st.success("Alert deleted.")
                    st.rerun()
    else:
        st.caption("No active alerts. Create one above!")

# ── Task 4.3: Portfolio Tracking Functions ──────────────────
def db_add_portfolio_holding(ticker: str, quantity: int, entry_price: float, purchase_date: str = None) -> bool:
    """
    Task 4.3: Add a holding to user's investment portfolio.
    """
    user = get_user()
    if not user or not _sb: return False
    try:
        _sb.table("portfolio_holdings").insert({
            "user_id": user.id,
            "ticker": ticker.upper(),
            "quantity": quantity,
            "entry_price": entry_price,
            "purchase_date": purchase_date or datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        logger.error(f"DB error adding portfolio holding: {e}")
        return False

def db_get_portfolio_holdings():
    """Get all portfolio holdings for current user."""
    user = get_user()
    if not user or not _sb: return []
    try:
        r = _sb.table("portfolio_holdings").select("*").eq("user_id", user.id).order("purchase_date", desc=True).execute()
        return r.data or []
    except Exception as e:
        logger.error(f"DB error retrieving portfolio: {e}")
        return []

def db_update_portfolio_holding(holding_id: str, quantity: int, entry_price: float) -> bool:
    """Update a portfolio holding (quantity/entry price)."""
    user = get_user()
    if not user or not _sb: return False
    try:
        _sb.table("portfolio_holdings").update({
            "quantity": quantity,
            "entry_price": entry_price
        }).eq("id", holding_id).eq("user_id", user.id).execute()
        return True
    except Exception as e:
        logger.error(f"DB error updating portfolio: {e}")
        return False

def db_delete_portfolio_holding(holding_id: str) -> bool:
    """Remove a holding from portfolio."""
    user = get_user()
    if not user or not _sb: return False
    try:
        _sb.table("portfolio_holdings").delete().eq("id", holding_id).eq("user_id", user.id).execute()
        return True
    except Exception as e:
        logger.error(f"DB error deleting portfolio holding: {e}")
        return False

def calculate_portfolio_metrics(holdings: list, board: dict) -> dict:
    """
    Task 4.3: Calculate comprehensive portfolio metrics.
    Returns: {total_investment, current_value, total_gain_loss, gain_loss_pct, allocation, holdings_summary}
    """
    if not holdings:
        return {
            "total_investment": 0,
            "current_value": 0,
            "total_gain_loss": 0,
            "gain_loss_pct": 0,
            "allocation": {},
            "holdings": []
        }

    holdings_detail = []
    total_investment = 0
    current_value = 0

    for h in holdings:
        ticker = h.get("ticker", "").upper()
        quantity = h.get("quantity", 0)
        entry_price = h.get("entry_price", 0)
        cost_basis = quantity * entry_price
        total_investment += cost_basis

        # Get current price from board
        current_price = board.get(ticker, {}).get("close", entry_price)
        current_holdings_value = quantity * current_price
        current_value += current_holdings_value

        gain_loss = current_holdings_value - cost_basis
        gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis else 0

        company = CSE_STOCKS.get(ticker, (ticker, ""))[0]

        holdings_detail.append({
            "ticker": ticker,
            "company": company,
            "quantity": quantity,
            "entry_price": entry_price,
            "current_price": current_price,
            "cost_basis": cost_basis,
            "current_value": current_holdings_value,
            "gain_loss": gain_loss,
            "gain_loss_pct": gain_loss_pct,
            "holding_id": h.get("id")
        })

    total_gain_loss = current_value - total_investment
    total_gain_loss_pct = (total_gain_loss / total_investment * 100) if total_investment else 0

    # Calculate allocation percentages
    allocation = {}
    for h in holdings_detail:
        allocation[h["ticker"]] = (h["current_value"] / current_value * 100) if current_value else 0

    return {
        "total_investment": total_investment,
        "current_value": current_value,
        "total_gain_loss": total_gain_loss,
        "gain_loss_pct": total_gain_loss_pct,
        "allocation": allocation,
        "holdings": holdings_detail
    }

def display_portfolio_dashboard(holdings: list, board: dict):
    """
    Task 4.3: Display comprehensive portfolio tracking dashboard.
    Shows portfolio overview, allocation, holdings, and performance.
    """
    st.markdown("### " + chr(128202) + " Portfolio Tracking")

    if not get_user():
        st.info("Sign in to track your investment portfolio.")
        return

    # SECTION 1: Add New Holding
    with st.expander("Add Holding", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_ticker = st.selectbox(
                "Ticker", CSE_STOCKS.keys(), key="portfolio_ticker",
                format_func=lambda t: f"{t} — {CSE_STOCKS[t][0][:20]}"
            )
        with col2:
            new_qty = st.number_input("Quantity", min_value=1, step=1, key="portfolio_qty", value=10)
        with col3:
            new_price = st.number_input("Entry Price (LKR)", min_value=0.1, step=1.0, key="portfolio_price", value=100.0)

        if st.button("Add to Portfolio", use_container_width=True):
            if db_add_portfolio_holding(new_ticker, new_qty, new_price):
                st.success(f"Added {new_qty} x {new_ticker}")
                st.rerun()
            else:
                st.error("Failed to add holding.")

    st.divider()

    # Calculate portfolio metrics
    metrics = calculate_portfolio_metrics(holdings, board)

    if metrics["current_value"] == 0:
        st.info("No holdings yet. Add your first holding above!")
        return

    # SECTION 2: Portfolio Summary Cards
    st.markdown("#### Portfolio Summary")
    sm1, sm2, sm3, sm4 = st.columns(4)

    with sm1:
        st.metric(
            "Total Invested",
            f"LKR {metrics['total_investment']:,.0f}",
            f"{len(holdings)} stocks"
        )

    with sm2:
        st.metric(
            "Current Value",
            f"LKR {metrics['current_value']:,.0f}",
            f"vs LKR {metrics['total_investment']:,.0f}"
        )

    with sm3:
        st.metric(
            "Total Gain/Loss",
            f"LKR {metrics['total_gain_loss']:,.0f}",
            f"{metrics['gain_loss_pct']:+.2f}%",
            delta_color=("normal" if metrics["gain_loss"] >= 0 else "inverse")
        )

    with sm4:
        allocation_diversity = len(metrics["allocation"])
        st.metric(
            "Diversification",
            f"{allocation_diversity} stocks",
            f"{allocation_diversity}/10 sectors"
        )

    st.markdown("---")

    # SECTION 3: Asset Allocation Pie Chart
    col_alloc, col_perf = st.columns(2)

    with col_alloc:
        st.markdown("#### Asset Allocation")
        alloc_df = pd.DataFrame({
            "Ticker": list(metrics["allocation"].keys()),
            "Allocation %": list(metrics["allocation"].values())
        }).sort_values("Allocation %", ascending=False)

        fig_alloc = go.Figure(go.Pie(
            labels=alloc_df["Ticker"],
            values=alloc_df["Allocation %"],
            hole=0.3
        ))
        fig_alloc.update_layout(
            template="plotly_dark", height=350,
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117"
        )
        st.plotly_chart(fig_alloc, use_container_width=True)

    with col_perf:
        st.markdown("#### Performance by Holding")
        perf_df = pd.DataFrame({
            "Ticker": [h["ticker"] for h in metrics["holdings"]],
            "Gain/Loss %": [h["gain_loss_pct"] for h in metrics["holdings"]]
        }).sort_values("Gain/Loss %", ascending=False)

        colors_perf = ["#00d26a" if v >= 0 else "#ff4b4b" for v in perf_df["Gain/Loss %"]]
        fig_perf = go.Figure(go.Bar(
            y=perf_df["Ticker"],
            x=perf_df["Gain/Loss %"],
            orientation="h",
            marker_color=colors_perf,
            text=[f"{v:+.1f}%" for v in perf_df["Gain/Loss %"]],
            textposition="outside"
        ))
        fig_perf.update_layout(
            template="plotly_dark", height=350,
            margin=dict(l=60, r=10, t=20, b=20),
            xaxis_ticksuffix="%",
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            yaxis_autorange="reversed"
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    st.markdown("---")

    # SECTION 4: Holdings Table
    st.markdown("#### Holdings Details")
    holdings_table = []
    for h in metrics["holdings"]:
        holdings_table.append({
            "Ticker": h["ticker"],
            "Company": h["company"][:20],
            "Qty": h["quantity"],
            "Entry": f"LKR {h['entry_price']:.2f}",
            "Current": f"LKR {h['current_price']:.2f}",
            "Cost Basis": f"LKR {h['cost_basis']:,.0f}",
            "Value": f"LKR {h['current_value']:,.0f}",
            "Gain/Loss": f"LKR {h['gain_loss']:+,.0f}",
            "Return": f"{h['gain_loss_pct']:+.2f}%"
        })

    holdings_df = pd.DataFrame(holdings_table)
    st.dataframe(holdings_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # SECTION 5: Manage Holdings
    st.markdown("#### Manage Holdings")
    for h in metrics["holdings"]:
        col_ticker, col_action = st.columns([4, 1])
        with col_ticker:
            st.markdown(
                f'<div style="padding:8px;background:#1a1a1a;border-radius:4px;">'
                f'<strong>{h["ticker"]}</strong> | {h["company"][:25]} | '
                f'{h["quantity"]} units @ LKR {h["entry_price"]:.2f} | '
                f'<span style="color:{"#00d26a" if h["gain_loss"] >= 0 else "#ff4b4b"}">LKR {h["gain_loss"]:+,.0f}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        with col_action:
            if st.button("X", key=f"remove_holding_{h['holding_id']}", use_container_width=True):
                if db_delete_portfolio_holding(h['holding_id']):
                    st.success("Holding removed.")
                    st.rerun()

def db_save_briefing(title: str, content: str, model: str, sentiment: str = "") -> bool:
    user = get_user()
    if not user or not _sb: return False
    try:
        _sb.table("saved_briefings").insert({
            "user_id": user.id, "title": title,
            "content": content, "model_used": model, "sentiment": sentiment
        }).execute()
        return True
    except Exception as e:
        logger.error(f"DB error saving briefing: {e}")
        return False

def db_get_briefings():
    user = get_user()
    if not user or not _sb: return []
    try:
        r = _sb.table("saved_briefings").select("*").eq("user_id", user.id)\
               .order("created_at", desc=True).limit(30).execute()
        return r.data or []
    except Exception as e:
        logger.error(f"DB error retrieving briefings: {e}")
        return []

def db_delete_briefing(bid: int):
    user = get_user()
    if not user or not _sb: return
    try:
        _sb.table("saved_briefings").delete().eq("id", bid).eq("user_id", user.id).execute()
    except Exception as e:
        logger.warning(f"Error deleting briefing: {e}")

def db_get_notes():
    user = get_user()
    if not user or not _sb: return []
    try:
        r = _sb.table("user_notes").select("*").eq("user_id", user.id)\
               .order("is_pinned", desc=True).order("updated_at", desc=True).execute()
        return r.data or []
    except Exception as e:
        logger.error(f"DB error retrieving notes: {e}")
        return []

def db_save_note(title: str, content: str, tags=None, is_pinned: bool = False):
    user = get_user()
    if not user or not _sb: return None
    try:
        r = _sb.table("user_notes").insert({
            "user_id": user.id, "title": title,
            "content": content, "tags": tags or [], "is_pinned": is_pinned
        }).execute()
        return r.data[0] if r.data else None
    except Exception as e:
        logger.error(f"DB error saving note: {e}")
        return None

def db_update_note(nid: int, **kwargs):
    user = get_user()
    if not user or not _sb: return
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    try:
        _sb.table("user_notes").update(kwargs).eq("id", nid).eq("user_id", user.id).execute()
    except Exception as e:
        logger.warning(f"Error updating note: {e}")

def db_delete_note(nid: int):
    user = get_user()
    if not user or not _sb: return
    try:
        _sb.table("user_notes").delete().eq("id", nid).eq("user_id", user.id).execute()
    except Exception as e:
        logger.warning(f"Error deleting note: {e}")

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# AUTH PAGE UI
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
_G_ICON = """<svg width="18" height="18" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
<path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0
 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
<path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26
 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
<path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19
C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
<path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16
 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
</svg>"""

def _google_btn(label: str):
    """Render Google OAuth button. Shows setup notice if not configured."""
    if not _sb: return
    try:
        g = _sb.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": APP_URL, "scopes": "email profile"}
        })
        if g.url:
            st.markdown(f"""<div class="google-btn-wrap">
          <a href="{g.url}" target="_self">
            <div class="google-btn">{_G_ICON}&nbsp; {label}</div>
          </a></div>""", unsafe_allow_html=True)
            st.caption("\u2139\ufe0f If Google sign-in shows a 403 error, use Email or Phone OTP instead while Google OAuth is being configured.")
        else:
            st.caption("Google sign-in not yet configured \u2014 use email or phone below.")
    except Exception as e:
        logger.warning(f"Google OAuth configuration error: {e}")
        st.caption("Google sign-in not yet configured \u2014 use email or phone below.")

def _validate_password_strength(password: str) -> list:
    """
    Validate password strength against security requirements.
    Returns list of error messages. Empty list = password is valid.
    """
    errors = []

    if len(password) < 8:
        errors.append("At least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("At least 1 uppercase letter (A-Z)")
    if not re.search(r"[a-z]", password):
        errors.append("At least 1 lowercase letter (a-z)")
    if not re.search(r"[0-9]", password):
        errors.append("At least 1 number (0-9)")
    if not re.search(r"[!@#$%^&*]", password):
        errors.append("At least 1 special character (!@#$%^&*)")

    return errors


def show_auth_page():
    """Full-screen auth page: Sign In \u00b7 Create Account \u00b7 Phone \u00b7 Reset."""
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        # Logo
        st.markdown("""
        <div class="auth-logo">
          <div class="icon">\U0001f4c8</div>
          <div class="brand">InvestSmart</div>
          <div class="tagline">CSE Intelligence Platform</div>
        </div>""", unsafe_allow_html=True)

        # Inline error/success
        if st.session_state.get("auth_error"):
            st.error(st.session_state.pop("auth_error"))
        if st.session_state.get("auth_success"):
            st.success(st.session_state.pop("auth_success"))

        tab_si, tab_su, tab_ph, tab_pw = st.tabs(
            ["\U0001f510 Sign In", "\u2728 Create Account", "\U0001f4f1 Phone OTP", "\U0001f511 Reset Password"]
        )

        # \u2500\u2500 SIGN IN \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        with tab_si:
            _google_btn("Continue with Google")
            st.markdown('<div class="or-divider">or sign in with email</div>',
                        unsafe_allow_html=True)

            with st.form("f_signin"):
                email    = st.text_input("Email address", placeholder="you@example.com",
                                         key="si_email")
                password = st.text_input("Password", type="password",
                                         placeholder="Your password", key="si_pw")
                ok = st.form_submit_button("Sign In \u2192", use_container_width=True,
                                           type="primary")
            if ok:
                import re as _re
                if not email or not password:
                    st.error("Enter both email and password.")
                elif not _re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    st.error("Enter a valid email address.")
                elif _sb:
                    try:
                        r = _sb.auth.sign_in_with_password(
                            {"email": email, "password": password})
                        st.session_state.update({
                            "auth_user": r.user, "auth_session": r.session,
                            "show_auth": False})
                        _load_profile()
                        st.rerun()
                    except Exception as e:
                        err = str(e).lower()
                        if "invalid" in err:
                            st.error("\u274c Invalid email or password.")
                        elif "not confirmed" in err:
                            st.warning("\U0001f4e7 Please verify your email before signing in.")
                        else:
                            st.error(f"Sign-in failed: {e}")

        # \u2500\u2500 CREATE ACCOUNT \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        with tab_su:
            _google_btn("Sign up with Google")
            st.markdown('<div class="or-divider">or create with email</div>',
                        unsafe_allow_html=True)

            with st.form("f_signup"):
                name    = st.text_input("Full name", placeholder="Your Name")
                s_email = st.text_input("Email address", placeholder="you@example.com")
                s_pw    = st.text_input("Password", type="password",
                                        placeholder="Min 8 characters")
                s_pw2   = st.text_input("Confirm password", type="password",
                                        placeholder="Repeat password")
                agreed  = st.checkbox(
                    "I agree to the Terms of Service and Privacy Policy")
                sub = st.form_submit_button("Create Account \u2192",
                                            use_container_width=True, type="primary")
            if sub:
                import re as _re
                if not name or not s_email or not s_pw:
                    st.error("Please fill all fields.")
                elif not _re.match(r"[^@]+@[^@]+\.[^@]+", s_email):
                    st.error("Enter a valid email address.")
                elif s_pw != s_pw2:
                    st.error("Passwords don't match.")
                else:
                    # Validate password strength
                    pwd_errors = _validate_password_strength(s_pw)
                    if pwd_errors:
                        st.error("Password is too weak. Requirements:\n" + "\n".join(f"• {e}" for e in pwd_errors))
                    elif not agreed:
                        st.error("Please agree to the Terms of Service.")
                    elif _sb:
                        try:
                            r = _sb.auth.sign_up({
                                "email": s_email, "password": s_pw,
                                "options": {"data": {"full_name": name}}
                            })
                            if r.session:          # auto-confirmed
                                st.session_state.update({
                                    "auth_user": r.user, "auth_session": r.session,
                                    "show_auth": False})
                                _load_profile()
                                st.rerun()
                            elif r.user:
                                st.success(
                                    "\u2705 Account created! Check your email to verify, then sign in.")
                            else:
                                st.error("Sign-up failed. Email may already be registered.")
                        except Exception as e:
                            st.error(f"Sign-up failed: {e}")

        # \u2500\u2500 PHONE OTP \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        with tab_ph:
            st.caption("Enter your mobile number \u2014 we'll send a 6-digit SMS code.")
            st.info("Include country code \u00b7 e.g. **+94 77 123 4567** for Sri Lanka")

            if st.session_state.get("phone_step", 1) == 1:
                with st.form("f_phone"):
                    ph = st.text_input("Mobile number", placeholder="+94771234567",
                                       value=st.session_state.get("phone_number", ""))
                    send = st.form_submit_button("Send SMS Code \u2192",
                                                 use_container_width=True, type="primary")
                if send:
                    ph = ph.strip()
                    if not ph.startswith("+"):
                        st.error("Include country code, e.g. +94 for Sri Lanka.")
                    elif _sb:
                        try:
                            _sb.auth.sign_in_with_otp({"phone": ph})
                            st.session_state.update(
                                {"phone_number": ph, "phone_step": 2})
                            st.rerun()
                        except Exception as e:
                            st.error(f"SMS failed: {e}")
            else:
                ph = st.session_state.get("phone_number", "")
                st.success(f"Code sent to **{ph}**")
                with st.form("f_otp"):
                    otp = st.text_input("6-digit code", placeholder="123456",
                                        max_chars=6)
                    verify = st.form_submit_button("Verify & Sign In \u2192",
                                                   use_container_width=True,
                                                   type="primary")
                if verify:
                    if _sb:
                        try:
                            r = _sb.auth.verify_otp(
                                {"phone": ph, "token": otp, "type": "sms"})
                            if r.session:
                                st.session_state.update({
                                    "auth_user": r.user, "auth_session": r.session,
                                    "phone_step": 1, "show_auth": False})
                                _load_profile()
                                st.rerun()
                            else:
                                st.error("Invalid or expired code.")
                        except Exception as e:
                            st.error(f"Verification failed: {e}")
                if st.button("\u2190 Change number"):
                    st.session_state["phone_step"] = 1
                    st.rerun()

        # \u2500\u2500 RESET PASSWORD \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        with tab_pw:
            st.caption("We'll email you a link to reset your password.")
            with st.form("f_reset"):
                r_email = st.text_input("Registered email", placeholder="you@example.com")
                send_r  = st.form_submit_button("Send Reset Link \u2192",
                                                use_container_width=True, type="primary")
            if send_r:
                if not r_email:
                    st.error("Enter your email address.")
                elif _sb:
                    try:
                        _sb.auth.reset_password_email(
                            r_email, options={"redirect_to": APP_URL})
                        st.success("\u2705 Reset link sent! Check your inbox.")
                    except Exception as e:
                        st.error(f"Failed: {e}")

        st.markdown("")
        if st.button("\u2190 Back to App", use_container_width=True):
            st.session_state["show_auth"] = False
            st.rerun()


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PREMIUM GATE
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def show_premium_gate(feature: str = "this feature"):
    st.markdown(f"""
    <div class="premium-gate">
      <h2>\U0001f510 Login Required</h2>
      <p>Please sign in to access {feature}.</p>
    </div>""", unsafe_allow_html=True)
    if st.button("\U0001f510 Sign In / Create Account", type="primary", use_container_width=False):
        st.session_state["show_auth"] = True
        st.rerun()


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# DATA FETCHING (cached)
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@st.cache_data(ttl=300)
def fetch_price(ticker: str, period: str = "5d") -> pd.DataFrame | None:
    try:
        df = yf.download(ticker, period=period, interval="1d",
                         auto_adjust=True, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        logger.warning(f"Error fetching price data for {ticker}: {e}")
        return None

def current_price(ticker: str) -> dict:
    df = fetch_price(ticker, "5d")
    empty = {"close": None, "change": None, "change_pct": None,
             "open": None, "high": None, "low": None, "volume": None}
    if df is None or len(df) < 2: return empty
    last, prev   = df.iloc[-1], df.iloc[-2]
    close        = float(last["Close"])
    prev_close   = float(prev["Close"])
    change       = close - prev_close
    change_pct   = (change / prev_close) * 100 if prev_close else 0
    return {"close": close, "change": change, "change_pct": change_pct,
            "open": float(last.get("Open", close)), "high": float(last.get("High", close)),
            "low":  float(last.get("Low",  close)), "volume": float(last.get("Volume", 0))}

@st.cache_data(ttl=3600)
def fetch_fred(series_id: str) -> float | None:
    if not FRED_API_KEY: return None
    try:
        r = requests.get("https://api.stlouisfed.org/fred/series/observations", params={
            "series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json",
            "sort_order": "desc", "observation_start": str(date.today() - timedelta(days=30)),
            "limit": 1}, timeout=10)
        r.raise_for_status()
        obs = r.json().get("observations", [])
        return float(obs[0]["value"]) if obs and obs[0]["value"] != "." else None
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.warning(f"FRED API error for {series_id}: {e}")
        return None

@st.cache_data(ttl=1800)
def fetch_news(query: str, n: int = 8) -> list:
    if not NEWS_API_KEY: return []
    try:
        r = requests.get("https://newsapi.org/v2/top-headlines",
                         params={"q": query, "apiKey": NEWS_API_KEY,
                                 "pageSize": n, "language": "en"}, timeout=10)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        if not articles:
            r2 = requests.get("https://newsapi.org/v2/everything",
                              params={"q": query, "apiKey": NEWS_API_KEY,
                                      "pageSize": n, "language": "en",
                                      "sortBy": "publishedAt",
                                      "from": str(date.today() - timedelta(days=7))},
                              timeout=10)
            r2.raise_for_status()
            articles = r2.json().get("articles", [])
        return [a for a in articles if "[Removed]" not in (a.get("title") or "")][:n]
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.warning(f"News API error for query '{query}': {e}")
        return []

@st.cache_data(ttl=21600)
def fetch_worldbank(indicator: str, country: str = "LK") -> dict:
    try:
        r = requests.get(
            f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}",
            params={"format": "json", "mrv": 1}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if len(data) > 1 and data[1]:
            item = data[1][0]
            return {"value": item.get("value"), "year": item.get("date", "")}
        return {}
    except (requests.RequestException, ValueError, IndexError) as e:
        logger.warning(f"World Bank API error for {indicator}/{country}: {e}")
        return {}



# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# CSE (COLOMBO STOCK EXCHANGE) MODULE
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

# \u2500\u2500 Major CSE stock universe (Yahoo Finance .LK tickers) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
CSE_STOCKS = {
    # Banking & Finance
    "COMB.LK": ("Commercial Bank of Ceylon PLC",      "Banking"),
    "HNB.LK":  ("Hatton National Bank PLC",           "Banking"),
    "SAMP.LK": ("Sampath Bank PLC",                   "Banking"),
    "NDB.LK":  ("NDB Bank PLC",                       "Banking"),
    "DFCC.LK": ("DFCC Bank PLC",                      "Banking"),
    "PABC.LK": ("Pan Asia Banking Corporation PLC",   "Banking"),
    "UNION.LK":("Union Bank of Colombo PLC",          "Banking"),
    "LOLC.LK": ("LOLC Holdings PLC",                  "Finance"),
    "CFIN.LK": ("Central Finance Company PLC",        "Finance"),
    "LLUB.LK": ("Lanka ORIX Leasing Company PLC",     "Finance"),
    "LOFC.LK": ("LOLC Finance PLC",                   "Finance"),
    # Diversified Holdings
    "JKH.LK":  ("John Keells Holdings PLC",           "Diversified"),
    "CARG.LK": ("Cargills (Ceylon) PLC",              "Diversified"),
    "HPWR.LK": ("Hemas Holdings PLC",                 "Diversified"),
    # Telecom
    "DIAL.LK": ("Dialog Axiata PLC",                  "Telecom"),
    "SLTL.LK": ("Sri Lanka Telecom PLC",              "Telecom"),
    # Manufacturing
    "CTC.LK":  ("Ceylon Tobacco Company PLC",         "Manufacturing"),
    "DIPD.LK": ("Dipped Products PLC",                "Manufacturing"),
    "REXP.LK": ("Richard Pieris Exports PLC",         "Manufacturing"),
    "TJL.LK":  ("Textured Jersey Lanka PLC",          "Manufacturing"),
    "ACL.LK":  ("ACL Cables PLC",                     "Manufacturing"),
    "SELI.LK": ("Sierra Cables PLC",                  "Manufacturing"),
    "LALU.LK": ("Lanka Aluminium Industries PLC",     "Manufacturing"),
    # Plantation
    "AGAL.LK": ("Agalawatte Plantations PLC",         "Plantation"),
    "MAST.LK": ("Maskeliya Plantations PLC",          "Plantation"),
    "BUKI.LK": ("Bukit Darah PLC",                    "Plantation"),
    "ELPL.LK": ("Elpitiya Plantations PLC",           "Plantation"),
    "KZOO.LK": ("Kotagala Plantations PLC",           "Plantation"),
    "NAMU.LK": ("Namunukula Plantations PLC",         "Plantation"),
    # Hotels & Leisure
    "AHPL.LK": ("Asian Hotels and Properties PLC",    "Hotels"),
    "BERU.LK": ("Beruwala Resorts PLC",               "Hotels"),
    "AMSL.LK": ("Aitken Spence Hotel Holdings PLC",   "Hotels"),
    # Healthcare
    "ASIR.LK": ("Asiri Hospital Holdings PLC",        "Healthcare"),
    "NHSL.LK": ("Nawaloka Hospitals PLC",             "Healthcare"),
    # Energy
    "LIOC.LK": ("Lanka IOC PLC",                      "Energy"),
}

CSE_SECTORS = ["All", "Banking", "Finance", "Diversified", "Telecom",
               "Manufacturing", "Plantation", "Hotels", "Healthcare", "Energy"]

# \u2500\u2500 User tier helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def is_paid_user() -> bool:
    """Returns True if current user has Premium tier."""
    return get_profile().get("tier", "free") == "premium"

# \u2500\u2500 CSE DB helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def db_record_cse_prices(prices: list) -> bool:
    """Store CSE daily prices to Supabase cse_price_history table."""
    if not _sb or not prices:
        return False
    try:
        today_str = date.today().isoformat()
        rows = []
        for p in prices:
            if p.get("close"):
                rows.append({
                    "symbol":      p.get("ticker", ""),
                    "price_date":  today_str,
                    "open_price":  p.get("open"),
                    "high_price":  p.get("high"),
                    "low_price":   p.get("low"),
                    "close_price": p["close"],
                    "volume":      int(p.get("volume") or 0),
                    "source":      "yahoo",
                })
        if rows:
            _sb.table("cse_price_history").upsert(
                rows, on_conflict="symbol,price_date").execute()
        return True
    except Exception as e:
        logger.error(f"DB error recording CSE prices: {e}")
        return False

def db_get_cse_history(symbol: str, days: int = 365) -> list:
    """Retrieve historical CSE prices from Supabase."""
    if not _sb:
        return []
    try:
        since = (date.today() - timedelta(days=days)).isoformat()
        r = (_sb.table("cse_price_history")
             .select("price_date,open_price,high_price,low_price,close_price,volume")
             .eq("symbol", symbol)
             .gte("price_date", since)
             .order("price_date", desc=False)
             .execute())
        return r.data or []
    except Exception as e:
        logger.error(f"DB error retrieving CSE history for {symbol}: {e}")
        return []

# \u2500\u2500 CSE Live WebSocket (replaces broken yfinance .LK support) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Yahoo Finance dropped .LK tickers. We connect to CSE's own SockJS+STOMP feed.
_CSE_WS_LOCK   = _threading.Lock()
_CSE_WS_CACHE: dict = {}   # cse_symbol -> {symbol,price,change,changePercentage,ts}
_CSE_WS_ASPI:  dict = {}   # latest /topic/aspi payload
_CSE_WS_THREAD = None
_CSE_WS_STOP   = None


def _cse_ws_worker(stop_evt):
    """Daemon: SockJS+STOMP connection to wss://www.cse.lk live feed."""
    try:
        import websocket as _wsc
    except ImportError:
        return
    srv = str(random.randint(0, 999)).zfill(3)
    sid = "".join(random.choices(_string_mod.ascii_lowercase + _string_mod.digits, k=10))
    url = "wss://www.cse.lk/api/ws/" + srv + "/" + sid + "/websocket"

    def on_open(ws):
        ws.send(json.dumps(["CONNECT\naccept-version:1.1,1.0\nheart-beat:0,0\n\n\x00"]))

    def on_message(ws, raw):
        if stop_evt.is_set():
            ws.close()
            return
        try:
            if not raw.startswith("a"):
                return
            frames = json.loads(raw[1:])
            flist = frames if isinstance(frames, list) else [frames]
            for frame in flist:
                if "CONNECTED" in frame:
                    ws.send(json.dumps(["SUBSCRIBE\nid:sub-dt\ndestination:/topic/daytrade\n\n\x00"]))
                    ws.send(json.dumps(["SUBSCRIBE\nid:sub-aspi\ndestination:/topic/aspi\n\n\x00"]))
                    ws.send(json.dumps(["SEND\ndestination:/app/request-daytrade\ncontent-type:application/json\n\n{}\x00"]))
                elif "/topic/daytrade" in frame:
                    _, body = frame.split("\n\n", 1)
                    data = json.loads(body.rstrip("\x00"))
                    now = _time.time()
                    with _CSE_WS_LOCK:
                        for item in data:
                            entry = dict(item)
                            entry["ts"] = now
                            _CSE_WS_CACHE[item["symbol"]] = entry
                elif "/topic/aspi" in frame:
                    _, body = frame.split("\n\n", 1)
                    aspi_data = json.loads(body.rstrip("\x00"))
                    with _CSE_WS_LOCK:
                        _CSE_WS_ASPI.clear()
                        _CSE_WS_ASPI.update(aspi_data)
        except Exception:
            pass

    def on_error(ws, err):
        pass

    def on_close(ws, code, reason):
        pass

    ws_app = _wsc.WebSocketApp(
        url, on_open=on_open, on_message=on_message,
        on_error=on_error, on_close=on_close)
    # Socket timeout: 30 seconds - prevents zombie connections hanging indefinitely
    # ping_interval: 20s - keeps connection alive
    # ping_timeout: 10s - waits max 10s for ping response before reconnect
    try:
        ws_app.run_forever(
            ping_interval=20,
            ping_timeout=10,
            reconnect=5,
            socket_timeout=30
        )
    except Exception as e:
        logger.warning(f"CSE WebSocket error: {e}")


def _ensure_cse_ws():
    """Start CSE WebSocket daemon thread if not already running."""
    global _CSE_WS_THREAD, _CSE_WS_STOP
    with _CSE_WS_LOCK:
        if _CSE_WS_THREAD is None or not _CSE_WS_THREAD.is_alive():
            _CSE_WS_STOP = _threading.Event()
            _CSE_WS_THREAD = _threading.Thread(
                target=_cse_ws_worker, args=(_CSE_WS_STOP,),
                daemon=True, name="cse-ws")
            _CSE_WS_THREAD.start()


# \u2500\u2500 CSE price fetching (WebSocket-backed, two TTLs) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def _do_fetch_cse_board() -> dict:
    """Fetch all CSE prices from the live WebSocket cache."""
    _ensure_cse_ws()
    # Wait up to 12s for first data on cold start
    deadline = _time.time() + 12
    while _time.time() < deadline:
        with _CSE_WS_LOCK:
            if _CSE_WS_CACHE:
                break
        _time.sleep(0.25)

    results = {}
    with _CSE_WS_LOCK:
        snapshot = dict(_CSE_WS_CACHE)

    for lk_ticker in CSE_STOCKS:
        base = lk_ticker.replace(".LK", "")
        # Match by base symbol prefix e.g. "JKH" matches "JKH.N0000"
        best = None
        for sym, d in snapshot.items():
            if sym.startswith(base + "."):
                best = d
                break
        if best:
            price  = float(best.get("price") or 0)
            change = float(best.get("change") or 0)
            chg_p  = float(best.get("changePercentage") or 0)
            if price > 0:
                results[lk_ticker] = {
                    "ticker":     lk_ticker,
                    "symbol":     base,
                    "close":      price,
                    "change":     change,
                    "change_pct": chg_p,
                    "open":       price,
                    "high":       price,
                    "low":        price,
                    "volume":     0,
                }
    return results

@st.cache_data(ttl=900)
def _cse_board_free() -> dict:
    """CSE board \u2014 15-min cache for free users."""
    return _do_fetch_cse_board()

@st.cache_data(ttl=60)
def _cse_board_paid() -> dict:
    """CSE board \u2014 1-min cache for premium users."""
    return _do_fetch_cse_board()

def fetch_cse_board() -> dict:
    """Return CSE board prices with appropriate TTL for user tier."""
    return _cse_board_paid() if is_paid_user() else _cse_board_free()

@st.cache_data(ttl=30)
def fetch_cse_indices() -> dict:
    """Return ASPI index from the CSE live WebSocket feed."""
    _ensure_cse_ws()
    deadline = _time.time() + 5
    while _time.time() < deadline:
        with _CSE_WS_LOCK:
            if _CSE_WS_ASPI:
                aspi = dict(_CSE_WS_ASPI)
                break
        _time.sleep(0.2)
    else:
        return {}
    idx = {}
    v   = float(aspi.get("value") or 0)
    chg = float(aspi.get("change") or 0)
    pct = float(aspi.get("percentage") or 0)
    if v > 0:
        idx["ASPI"] = {"close": v, "change": chg, "change_pct": pct}
    return idx

@st.cache_data(ttl=300)
def fetch_cse_stock_history(ticker: str, period: str = "1y"):
    """Fetch historical OHLCV for one CSE stock from Supabase history."""
    days_map = {"1mo": 35, "3mo": 95, "6mo": 185, "1y": 370, "2y": 740}
    days = days_map.get(period, 370)
    history = db_get_cse_history(ticker, days=days)
    if not history:
        return None
    df = pd.DataFrame(history)
    df["Date"] = pd.to_datetime(df["price_date"])
    df = df.set_index("Date").sort_index()
    df = df.rename(columns={
        "open_price": "Open", "high_price": "High",
        "low_price": "Low", "close_price": "Close", "volume": "Volume"
    })
    return df

def build_sector_analysis(board: dict) -> dict:
    """
    Task 4.1: Build comprehensive sector analysis from CSE price board.
    Returns dict with sector metrics: count, avg_change, advances, declines, avg_price.
    """
    if not board:
        return {}

    sector_stats = {}

    # Group stocks by sector and calculate metrics
    for ticker, d in board.items():
        sec = CSE_STOCKS.get(ticker, ("", "Unknown"))[1]
        if sec not in sector_stats:
            sector_stats[sec] = {
                "stocks": [],
                "changes": [],
                "prices": [],
                "volumes": []
            }

        change = d.get("change_pct", 0) or 0
        price = d.get("close", 0) or 0
        volume = d.get("volume", 0) or 0

        sector_stats[sec]["stocks"].append(ticker)
        sector_stats[sec]["changes"].append(change)
        sector_stats[sec]["prices"].append(price)
        sector_stats[sec]["volumes"].append(volume)

    # Compute aggregate metrics per sector
    sector_metrics = {}
    for sec, data in sector_stats.items():
        changes = data["changes"]
        prices = data["prices"]
        volumes = data["volumes"]

        sector_metrics[sec] = {
            "count": len(data["stocks"]),
            "avg_change": sum(changes) / len(changes) if changes else 0,
            "advances": sum(1 for c in changes if c > 0),
            "declines": sum(1 for c in changes if c < 0),
            "unchanged": sum(1 for c in changes if c == 0),
            "avg_price": sum(prices) / len(prices) if prices else 0,
            "total_volume": sum(volumes),
            "top_gainers": sorted(
                [(t, c) for t, c in zip(data["stocks"], changes)],
                key=lambda x: x[1], reverse=True
            )[:3],
            "top_losers": sorted(
                [(t, c) for t, c in zip(data["stocks"], changes)],
                key=lambda x: x[1]
            )[:3]
        }

    return sector_metrics

def display_sector_dashboard(board: dict):
    """
    Task 4.1: Display comprehensive sector analysis dashboard.
    Shows sector overview, performance charts, and detailed sector metrics.
    """
    if not board:
        st.warning("No CSE data available for sector analysis.")
        return

    sector_metrics = build_sector_analysis(board)
    if not sector_metrics:
        return

    # SECTION 1: Sector Overview Cards
    st.markdown("### Sector Overview")
    sector_names = sorted(sector_metrics.keys())
    overview_cols = st.columns(min(5, len(sector_names)))
    for idx, sec in enumerate(sector_names[:5]):
        with overview_cols[idx % 5]:
            m = sector_metrics[sec]
            avg_chg = m["avg_change"]
            col_val = "positive" if avg_chg > 0 else ("negative" if avg_chg < 0 else "neutral")
            st.metric(
                sec,
                f"{avg_chg:+.2f}%",
                f"{m['advances']}↑ {m['declines']}↓",
                delta_color="normal"
            )

    st.markdown("---")

    # SECTION 2: Sector Performance Charts
    col_perf, col_comp = st.columns(2)

    with col_perf:
        st.markdown("#### Sector Performance (Avg Change %)")
        perf_df = pd.DataFrame({
            "Sector": list(sector_metrics.keys()),
            "Avg Change %": [sector_metrics[s]["avg_change"] for s in sector_metrics.keys()]
        }).sort_values("Avg Change %", ascending=False)

        colors_perf = ["#00d26a" if v >= 0 else "#ff4b4b" for v in perf_df["Avg Change %"]]
        fig_perf = go.Figure(go.Bar(
            y=perf_df["Sector"],
            x=perf_df["Avg Change %"],
            orientation="h",
            marker_color=colors_perf,
            text=[f"{v:+.2f}%" for v in perf_df["Avg Change %"]],
            textposition="outside"
        ))
        fig_perf.update_layout(
            template="plotly_dark", height=350,
            margin=dict(l=100, r=10, t=20, b=20),
            xaxis_ticksuffix="%",
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
            yaxis_autorange="reversed"
        )
        st.plotly_chart(fig_perf, use_container_width=True)

    with col_comp:
        st.markdown("#### Sector Composition (Stock Count)")
        comp_df = pd.DataFrame({
            "Sector": list(sector_metrics.keys()),
            "Count": [sector_metrics[s]["count"] for s in sector_metrics.keys()]
        }).sort_values("Count", ascending=False)

        fig_comp = go.Figure(go.Pie(
            labels=comp_df["Sector"],
            values=comp_df["Count"],
            hole=0.3
        ))
        fig_comp.update_layout(
            template="plotly_dark", height=350,
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117"
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("---")

    # SECTION 3: Detailed Sector Table
    st.markdown("#### Sector Metrics Table")
    table_data = []
    for sec in sorted(sector_metrics.keys()):
        m = sector_metrics[sec]
        table_data.append({
            "Sector": sec,
            "Stocks": m["count"],
            "Avg Chg %": f"{m['avg_change']:+.2f}%",
            "Advances": m["advances"],
            "Declines": m["declines"],
            "Unchanged": m["unchanged"],
            "Avg Price": f"LKR {m['avg_price']:,.2f}"
        })
    table_df = pd.DataFrame(table_data)
    st.dataframe(table_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # SECTION 4: Top Performers Per Sector
    st.markdown("#### Top Performers by Sector")
    sector_cols = st.columns(2)
    sectors_list = sorted(sector_metrics.keys())

    for idx, sec in enumerate(sectors_list):
        col = sector_cols[idx % 2]
        with col:
            m = sector_metrics[sec]
            st.markdown(f"**{sec}** ({m['count']} stocks)")

            # Top gainers
            if m["top_gainers"]:
                st.caption("🟢 Top Gainers")
                for ticker, chg in m["top_gainers"]:
                    cname = CSE_STOCKS.get(ticker, (ticker, ""))[0][:25]
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;padding:4px;">'
                        f'<span><code>{ticker}</code> {_html.escape(cname)}</span>'
                        f'<span style="color:#00d26a;font-weight:600">+{chg:.2f}%</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            # Top losers
            if m["top_losers"]:
                st.caption("🔴 Top Losers")
                for ticker, chg in m["top_losers"]:
                    cname = CSE_STOCKS.get(ticker, (ticker, ""))[0][:25]
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;padding:4px;">'
                        f'<span><code>{ticker}</code> {_html.escape(cname)}</span>'
                        f'<span style="color:#ff4b4b;font-weight:600">{chg:.2f}%</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            st.divider()

# \u2500\u2500 CSE Market Page \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def page_cse_market():
    st.title("\U0001f1f1\U0001f1f0 CSE Market")

    # Tier banner with refresh info
    _loaded_at = datetime.now().strftime('%H:%M:%S')
    if is_paid_user():
        st.success(
            f"\u26a1 **Premium \u2014 Live Data** \u00b7 Auto-refreshes every **60 seconds** "
            f"\u00b7 Last loaded: {_loaded_at}")
    else:
        _next_ts = (datetime.now() + __import__('datetime').timedelta(minutes=15)).strftime('%H:%M')
        st.info(
            f"\u231b **15-minute delayed data** (Free plan) \u00b7 "
            f"Next auto-refresh at ~{_next_ts} "
            f"\u00b7 \u2b50 Upgrade to **Premium** for live data every 60 seconds.")

    # Pre-load board data (shared across all tabs)
    with st.spinner("Fetching CSE prices\u2026"):
        board = fetch_cse_board()

    tab_ov, tab_pb, tab_sd = st.tabs(
        ["\U0001f4ca Market Overview", "\U0001f4cb Price Board", "\U0001f4c8 Stock Detail"])

    # -- TAB 1: Market Overview --------------------------------------------------
    with tab_ov:
        st.markdown("### Market Indices")
        with st.spinner("Loading indices\u2026"):
            indices = fetch_cse_indices()
        if indices:
            icols = st.columns(len(indices))
            for i, (name, d) in enumerate(indices.items()):
                v   = d.get("close")
                pct = d.get("change_pct", 0) or 0
                with icols[i]:
                    st.metric(name, fmt_index(v), f"{pct:+.2f}%" if v else None)
        else:
            st.info(
                "\U0001f4e1 ASPI / S&P SL20 index tickers have limited availability on "
                "Yahoo Finance. Individual stock prices are shown below.")

        st.markdown("---")
        st.markdown("### Market Summary")
        advances  = sum(1 for d in board.values() if (d.get("change_pct") or 0) > 0)
        declines  = sum(1 for d in board.values() if (d.get("change_pct") or 0) < 0)
        unchanged = sum(1 for d in board.values() if (d.get("change_pct") or 0) == 0)
        tracked   = len(board)
        no_data   = len(CSE_STOCKS) - tracked

        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        sc1.metric("Stocks w/ Data", tracked)
        sc2.metric("\U0001f7e2 Advances",  advances)
        sc3.metric("\U0001f534 Declines",  declines)
        sc4.metric("\u25a0 Unchanged",     unchanged)
        sc5.metric("\u2753 No Data",       no_data)

        if board:
            sorted_all = sorted(
                board.items(), key=lambda x: x[1].get("change_pct", 0) or 0, reverse=True)
            col_g, col_l = st.columns(2)
            with col_g:
                st.markdown("#### \U0001f7e2 Top Gainers")
                gainers = [item for item in sorted_all
                           if (item[1].get("change_pct") or 0) > 0][:5]
                if gainers:
                    for ticker, d in gainers:
                        cname = CSE_STOCKS.get(ticker, (ticker, ""))[0]
                        chg   = d.get("change_pct", 0) or 0
                        st.markdown(
                            f'<div class="ticker-row">'
                            f'<span style="font-weight:700;font-family:monospace;'
                            f'min-width:65px">{d["symbol"]}</span>'
                            f'<span style="color:#aaa;font-size:0.82rem;flex:1">'
                            f'{_html.escape(cname[:32])}</span>'
                            f'<span style="font-weight:600">LKR&nbsp;{d["close"]:,.2f}</span>'
                            f'&nbsp;<span class="positive">+{chg:.2f}%</span>'
                            f'</div>', unsafe_allow_html=True)
                else:
                    st.caption("No advances today.")
            with col_l:
                st.markdown("#### \U0001f534 Top Losers")
                losers = [item for item in reversed(sorted_all)
                          if (item[1].get("change_pct") or 0) < 0][:5]
                if losers:
                    for ticker, d in losers:
                        cname = CSE_STOCKS.get(ticker, (ticker, ""))[0]
                        chg   = d.get("change_pct", 0) or 0
                        st.markdown(
                            f'<div class="ticker-row">'
                            f'<span style="font-weight:700;font-family:monospace;'
                            f'min-width:65px">{d["symbol"]}</span>'
                            f'<span style="color:#aaa;font-size:0.82rem;flex:1">'
                            f'{_html.escape(cname[:32])}</span>'
                            f'<span style="font-weight:600">LKR&nbsp;{d["close"]:,.2f}</span>'
                            f'&nbsp;<span class="negative">{chg:.2f}%</span>'
                            f'</div>', unsafe_allow_html=True)
                else:
                    st.caption("No declines today.")

            # Task 4.1: Comprehensive Sector Analysis Dashboard
            st.markdown("---")
            display_sector_dashboard(board)

    # -- TAB 2: Price Board -------------------------------------------------------
    with tab_pb:
        st.markdown("### \U0001f1f1\U0001f1f0 CSE Full Price Board")
        st.caption("Prices via Yahoo Finance \u00b7 LKR = Sri Lankan Rupees")

        pf1, pf2, pf3 = st.columns([3, 2, 1])
        with pf1:
            search = st.text_input(
                "\U0001f50d Search", placeholder="Ticker or company name\u2026",
                key="cse_search", label_visibility="collapsed")
        with pf2:
            sec_flt = st.selectbox(
                "Sector", CSE_SECTORS, key="cse_sector",
                label_visibility="collapsed")
        with pf3:
            sort_by = st.selectbox(
                "Sort", ["Change %", "Price", "Volume", "Name"],
                key="cse_sort", label_visibility="collapsed")

        if not board:
            st.warning(
                "\u26a0\ufe0f No CSE price data available right now. "
                "This is normal on weekends/public holidays when markets are closed. "
                "Yahoo Finance serves the last available trading day's prices \u2014 "
                "try clicking \U0001f504 Refresh Data in the sidebar.")
            # Show last recorded prices from Supabase as fallback
            if _sb:
                st.markdown("**Showing last recorded prices from database:**")
                try:
                    last_rec = (_sb.table("cse_price_history")
                                .select("symbol,price_date,close_price,volume")
                                .order("price_date", desc=True)
                                .limit(35)
                                .execute())
                    if last_rec.data:
                        fallback_df = pd.DataFrame(last_rec.data).rename(columns={
                            "symbol": "Ticker", "price_date": "Date",
                            "close_price": "Close (LKR)", "volume": "Volume"})
                        st.dataframe(fallback_df, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No recorded prices in database yet. "
                                   "Use the Price Board tab to record prices on a trading day.")
                except Exception as e:
                    logger.warning(f"Error displaying CSE detail: {e}")
        else:
            rows = []
            for ticker, (company, sector) in CSE_STOCKS.items():
                if sec_flt != "All" and sector != sec_flt:
                    continue
                q = search.strip().lower()
                if q and q not in company.lower() and q not in ticker.lower():
                    continue
                d = board.get(ticker, {})
                rows.append({
                    "ticker":   ticker,
                    "symbol":   ticker.replace(".LK", ""),
                    "company":  company,
                    "sector":   sector,
                    "close":    d.get("close"),
                    "change":   d.get("change"),
                    "chg_pct":  d.get("change_pct"),
                    "open":     d.get("open"),
                    "high":     d.get("high"),
                    "low":      d.get("low"),
                    "volume":   d.get("volume"),
                    "has_data": bool(d.get("close")),
                })

            def _skey(r):
                if sort_by == "Change %": return r.get("chg_pct") or -999
                if sort_by == "Price":    return r.get("close")   or 0
                if sort_by == "Volume":   return r.get("volume")  or 0
                return r.get("company", "")
            rows.sort(key=_skey, reverse=(sort_by != "Name"))

            shown    = [r for r in rows if r["has_data"]]
            no_data_r = [r for r in rows if not r["has_data"]]
            st.caption(
                f"Showing **{len(shown)}** stocks with data"
                + (f" + {len(no_data_r)} with no data" if no_data_r else ""))

            # Table header
            st.markdown(
                '<div style="display:flex;gap:8px;padding:6px 4px;'
                'color:#7b82a8;font-size:0.73rem;font-weight:700;'
                'border-bottom:2px solid #2a2f4a;margin-bottom:2px">'
                '<span style="min-width:60px">TICKER</span>'
                '<span style="flex:1">COMPANY</span>'
                '<span style="min-width:55px;text-align:center">SECTOR</span>'
                '<span style="min-width:95px;text-align:right">PRICE (LKR)</span>'
                '<span style="min-width:72px;text-align:right">CHG %</span>'
                '<span style="min-width:65px;text-align:right">VOLUME</span>'
                '<span style="min-width:85px;text-align:right">HIGH/LOW</span>'
                '</div>', unsafe_allow_html=True)

            for r in shown:
                chg  = r["chg_pct"] or 0
                cls  = "positive" if chg > 0 else ("negative" if chg < 0 else "neutral")
                arr  = "\u25b2" if chg > 0 else ("\u25bc" if chg < 0 else "\u2014")
                vol  = r["volume"] or 0
                vfmt = (f"{vol/1_000_000:.1f}M" if vol >= 1_000_000
                        else (f"{vol/1_000:.0f}K" if vol >= 1_000 else str(vol)))
                hi   = r["high"]  or r["close"]
                lo   = r["low"]   or r["close"]
                st.markdown(
                    f'<div class="ticker-row">'
                    f'<span style="font-weight:700;font-family:monospace;min-width:60px">'
                    f'{r["symbol"]}</span>'
                    f'<span style="color:#c8cfea;font-size:0.82rem;flex:1;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
                    f'{_html.escape(r["company"])}</span>'
                    f'<span style="background:#1a1e30;padding:1px 6px;border-radius:4px;'
                    f'font-size:0.68rem;color:#7b82a8;min-width:55px;text-align:center;'
                    f'white-space:nowrap">{r["sector"]}</span>'
                    f'<span style="font-weight:700;min-width:95px;text-align:right">'
                    f'LKR {r["close"]:,.2f}</span>'
                    f'<span class="{cls}" style="min-width:72px;text-align:right">'
                    f'{arr}{chg:+.2f}%</span>'
                    f'<span style="color:#7b82a8;font-size:0.78rem;min-width:65px;'
                    f'text-align:right">{vfmt}</span>'
                    f'<span style="color:#556;font-size:0.73rem;min-width:85px;'
                    f'text-align:right">{hi:,.0f}/{lo:,.0f}</span>'
                    f'</div>', unsafe_allow_html=True)

            if no_data_r:
                with st.expander(f"\u2753 {len(no_data_r)} stocks without Yahoo Finance data"):
                    for r in no_data_r:
                        st.caption(f"\u2022 **{r['symbol']}** \u2014 {r['company']}")

            st.markdown("")
            if _sb:
                rc1, rc2 = st.columns([3, 1])
                with rc1:
                    st.caption(
                        "\U0001f4be Click to save today's closing prices to the "
                        "database for long-term historical records.")
                with rc2:
                    if st.button("\U0001f4be Record Today's Prices",
                                 key="cse_record", use_container_width=True):
                        to_rec = [
                            {**board[t], "ticker": t}
                            for t in CSE_STOCKS
                            if t in board and board[t].get("close")]
                        if db_record_cse_prices(to_rec):
                            st.success(
                                f"\u2705 Recorded {len(to_rec)} stock prices!")
                        else:
                            st.error("DB write failed. Check Supabase connection.")

    # -- TAB 3: Stock Detail ------------------------------------------------------
    with tab_sd:
        st.markdown("### \U0001f4c8 Individual Stock Analysis")

        with_data    = [t for t in CSE_STOCKS if t in board and board[t].get("close")]
        without_data = [t for t in CSE_STOCKS if t not in with_data]
        ordered_t    = with_data + without_data
        options_t    = [f"{t.replace('.LK','')} \u2014 {CSE_STOCKS[t][0]}"
                        for t in ordered_t]
        sel_label    = st.selectbox("Select stock", options_t, key="cse_detail_select")
        sel_idx      = options_t.index(sel_label)
        sel_tick     = ordered_t[sel_idx]
        company, sector = CSE_STOCKS.get(sel_tick, (sel_tick, ""))
        symbol          = sel_tick.replace(".LK", "")
        d               = board.get(sel_tick, {})

        st.markdown(f"#### {symbol} \u2014 {_html.escape(company)}")
        st.caption(
            f"Sector: **{sector}** \u00b7 CSE listed "
            f"\u00b7 Yahoo ticker: `{sel_tick}`")

        if d.get("close"):
            chg  = d.get("change_pct", 0) or 0
            arr  = "\u25b2" if chg > 0 else ("\u25bc" if chg < 0 else "\u2014")
            vol  = d.get("volume", 0) or 0
            vfmt = (f"{vol/1_000_000:.1f}M" if vol >= 1_000_000
                    else (f"{vol/1_000:.0f}K" if vol >= 1_000 else str(int(vol))))
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Price (LKR)", f"{d['close']:,.2f}", f"{arr} {chg:+.2f}%")
            m2.metric("Open",  f"{d.get('open',  d['close']):,.2f}")
            m3.metric("High",  f"{d.get('high',  d['close']):,.2f}")
            m4.metric("Low",   f"{d.get('low',   d['close']):,.2f}")
            m5.metric("Volume", vfmt)

            if is_logged_in():
                if st.button(f"\u2b50 Add {symbol} to Watchlist",
                             key=f"cse_wl_{symbol}"):
                    if db_add_watchlist(sel_tick, company, "cse"):
                        st.success(f"\u2705 {symbol} added to watchlist!")
                    else:
                        st.warning("Already in watchlist or failed to add.")
            else:
                st.caption("\U0001f510 Sign in to add to watchlist.")
        else:
            st.warning(
                f"\u26a0\ufe0f No price data for **{symbol}** on Yahoo Finance. "
                "Try another stock or check back later.")

        # Historical chart
        st.markdown("---")
        st.markdown("#### Price Chart")
        p_opts = {"1 Week": "5d", "1 Month": "1mo", "3 Months": "3mo",
                  "6 Months": "6mo", "1 Year": "1y", "2 Years": "2y"}
        p_choice = st.radio(
            "Period", list(p_opts.keys()), horizontal=True,
            index=3, key="cse_chart_period")

        with st.spinner("Loading chart\u2026"):
            hist_yf = fetch_cse_stock_history(sel_tick, p_opts[p_choice])
            hist_db = db_get_cse_history(sel_tick, 730)

        if hist_yf is not None and not hist_yf.empty:
            # Candlestick
            fig_c = go.Figure(go.Candlestick(
                x=hist_yf.index,
                open=hist_yf["Open"],  high=hist_yf["High"],
                low=hist_yf["Low"],    close=hist_yf["Close"],
                increasing_line_color="#00d26a",
                decreasing_line_color="#ff4b4b",
                name=symbol))
            fig_c.update_layout(
                title=f"{symbol} \u2014 {p_choice} Candlestick (LKR)",
                template="plotly_dark", height=400,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_rangeslider_visible=False,
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
            st.plotly_chart(fig_c, use_container_width=True)

            if "Volume" in hist_yf.columns:
                fig_v = go.Figure(go.Bar(
                    x=hist_yf.index, y=hist_yf["Volume"],
                    marker_color="#3b4fd9", name="Volume", opacity=0.8))
                fig_v.update_layout(
                    title="Trading Volume",
                    template="plotly_dark", height=180,
                    margin=dict(l=20, r=20, t=30, b=20),
                    paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
                st.plotly_chart(fig_v, use_container_width=True)

            base = float(hist_yf["Close"].iloc[0])
            if base:
                pct_s = ((hist_yf["Close"] - base) / base * 100).round(2)
                fig_r = go.Figure(go.Scatter(
                    x=hist_yf.index, y=pct_s, mode="lines",
                    name="Return %",
                    line=dict(color="#c084fc", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(192,132,252,0.08)"))
                fig_r.update_layout(
                    title=f"Cumulative Return % \u2014 {p_choice}",
                    template="plotly_dark", height=200,
                    margin=dict(l=20, r=20, t=30, b=20),
                    yaxis_ticksuffix="%",
                    paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
                st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.info(
                f"\U0001f4c9 Chart not available for {symbol} "
                "on Yahoo Finance for this period.")

        st.markdown("---")
        st.markdown("#### Recorded Price History (Database)")
        if hist_db:
            st.caption(f"\U0001f4be {len(hist_db)} days recorded in database")
            dbf = pd.DataFrame(hist_db).rename(columns={
                "price_date": "Date", "open_price": "Open",
                "high_price": "High", "low_price": "Low",
                "close_price": "Close (LKR)", "volume": "Volume"})
            show_cols = [c for c in
                         ["Date", "Close (LKR)", "Open", "High", "Low", "Volume"]
                         if c in dbf.columns]
            st.dataframe(dbf[show_cols].tail(60),
                         use_container_width=True, hide_index=True)
            csv_bytes = dbf[show_cols].to_csv(index=False).encode("utf-8")
            st.download_button(
                "\u2b07\ufe0f Download CSV", csv_bytes,
                file_name=f"{symbol}_history.csv", mime="text/csv",
                key=f"dl_{symbol}")
        else:
            st.info(
                "\U0001f4be No history recorded yet. "
                "Go to **Price Board** and click \u2018Record Today\u2019s Prices\u2019 "
                "to start building your historical database.")

    # Task 4.2: Price Alerts Section
    st.markdown("---")
    display_price_alerts_widget(board)


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# AI BRIEFING
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def call_claude_briefing(prompt: str) -> tuple[str, str]:
    if ANTHROPIC_API_KEY:
        try:
            import anthropic
            c = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            m = c.messages.create(model="claude-sonnet-4-6", max_tokens=2500,
                                  messages=[{"role": "user", "content": prompt}])
            return m.content[0].text, "Claude (claude-sonnet-4-6)"
        except Exception as e:
            st.warning(f"Claude unavailable ({e}) \u2014 trying OpenAI\u2026")
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            c = OpenAI(api_key=OPENAI_API_KEY)
            r = c.chat.completions.create(
                model="gpt-4o", max_tokens=2500,
                messages=[{"role": "system", "content": "Senior CSE investment analyst."},
                          {"role": "user",   "content": prompt}])
            return r.choices[0].message.content, "OpenAI (gpt-4o)"
        except Exception as e:
            st.warning(f"OpenAI unavailable ({e}) \u2014 trying Gemini\u2026")
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            r = genai.GenerativeModel("gemini-1.5-flash").generate_content(
                prompt, generation_config={"temperature": 0.3, "max_output_tokens": 2500})
            return r.text, "Gemini 1.5 Flash"
        except Exception as e:
            return f"All AI providers failed. Last error: {e}", "none"
    return "No AI API keys configured.", "none"

def generate_briefing(md: dict) -> tuple[str, str]:
    today    = datetime.now().strftime("%A, %d %B %Y")
    gold_usd = md.get("gold",    {}).get("close")
    usd_lkr  = md.get("usd_lkr", {}).get("close")
    gold_lkr = (gold_usd * usd_lkr) if gold_usd and usd_lkr else None

    def fmt(d, prefix=""):
        if d and d.get("close"):
            c, pct = d["close"], d.get("change_pct", 0) or 0
            arrow = '\u25b2' if pct >= 0 else '\u25bc'
            return f"{prefix}{c:,.2f}  {arrow}{pct:+.2f}%"
        return "N/A"

    prompt = f"""You are a senior investment analyst with deep expertise in the Colombo Stock Exchange (CSE), Sri Lankan markets, and global macro investing. Write a concise but complete daily market briefing for Sri Lankan retail investors.

TODAY: {today}

MARKET DATA:
\u2022 Gold (USD/oz):      {fmt(md.get('gold'),    '$')}
\u2022 Gold (LKR/oz):      {(f"LKR {gold_lkr:,.0f}") if gold_lkr else 'N/A'}
\u2022 Silver (USD/oz):    {fmt(md.get('silver'),  '$')}
\u2022 Oil Brent:          {fmt(md.get('oil'),     '$')}
\u2022 S&P 500:            {fmt(md.get('sp500'))}
\u2022 VIX:                {fmt(md.get('vix'))}
\u2022 USD/LKR:            {fmt(md.get('usd_lkr'))}
\u2022 USD Index (DXY):    {fmt(md.get('dxy'))}
\u2022 BSE Sensex:         {fmt(md.get('sensex'))}
\u2022 Nifty 50:           {fmt(md.get('nifty'))}

Write a structured briefing:
1. CSE Outlook \u2014 how today's data affects the Colombo Stock Exchange
2. Gold & Silver in LKR \u2014 critical for Sri Lankan investors
3. Global Macro Summary \u2014 US markets, Asia, forex
4. Key Risks & Opportunities
5. Sentiment Score: BULLISH / NEUTRAL / BEARISH for CSE, Gold, USD/LKR

Reference actual numbers. 2\u20133 sentences per section. End with:
*Not investment advice \u2014 for information only.*"""
    return call_claude_briefing(prompt)


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# INIT + SIDEBAR
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
_init_state()
if _sb: _handle_oauth_callback()

# -- AUTO-REFRESH via native JS (60s paid / 900s free) -----------------------
_refresh_ms = 60_000 if is_paid_user() else 900_000
_components_v1.html(
    f"""<script>
      (function() {{
        var ms = {_refresh_ms};
        setTimeout(function() {{ window.parent.location.reload(); }}, ms);
      }})();
    </script>""",
    height=0, scrolling=False)

with st.sidebar:
    st.markdown("## \U0001f4c8 InvestSmart")
    st.markdown("*CSE Intelligence Platform*")
    st.markdown("---")

    # \u2500\u2500 User card (logged in) \u2500\u2500
    if is_logged_in():
        profile = get_profile()
        user    = get_user()
        name    = (profile.get("full_name") or
                   (user.email.split("@")[0].title() if user.email else "User"))
        avatar  = profile.get("avatar_url", "")
        tier    = profile.get("tier", "free")
        email_s = (user.email or "")[:30] + ("\u2026" if len(user.email or "") > 30 else "")

        if avatar:
            avatar_html = f'<img src="{avatar}" width="38" style="border-radius:50%;flex-shrink:0"/>'
        else:
            initials    = name[0].upper() if name else "U"
            avatar_html = f'<div class="user-avatar">{initials}</div>'

        name_safe  = _html.escape(name)
        email_safe = _html.escape(email_s)
        st.markdown(
            f'<div class="user-card">{avatar_html}'
            f'<div><div class="user-name">{name_safe}</div>'
            f'<div class="user-email">{email_safe}</div></div></div>',
            unsafe_allow_html=True)

        badge = (f'<span class="badge-premium">\u2b50 Premium</span>'
                 if tier == "premium"
                 else f'<span class="badge-free">\U0001f193 Free Plan</span>')
        st.markdown(badge, unsafe_allow_html=True)
        st.markdown("")

    # \u2500\u2500 Navigation \u2500\u2500
    free_pages = ["\U0001f3e0 Dashboard", "\U0001f1f1\U0001f1f0 CSE Market", "\U0001f947 Gold & Silver", "\U0001f30d Global Markets", "\U0001f4f0 News Feed"]
    if is_logged_in():
        nav_pages = free_pages + ["\U0001f916 AI Briefing", "\u2b50 Watchlist", "\U0001f4ca Portfolio", "\U0001f4cb My Reports", "\u2139\ufe0f About"]
    else:
        nav_pages = free_pages + ["\U0001f512 AI Briefing", "\U0001f512 Watchlist", "\u2139\ufe0f About"]

    page = st.radio("Navigate", nav_pages, label_visibility="collapsed")

    st.markdown("---")
    _now_str  = datetime.now().strftime('%H:%M:%S')
    _tier_lbl = "Premium (60s)" if is_paid_user() else "Free (15 min)"
    st.markdown(f"**Last updated:** {_now_str}")
    st.caption(f"\u26a1 Auto-refresh: {_tier_lbl}")
    if st.button("\U0001f504 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.pop("meta_refresh_injected", None)
        st.rerun()

    st.markdown("---")
    if is_logged_in():
        if st.button("\U0001f6aa Sign Out", use_container_width=True):
            do_logout()
    else:
        if st.button("\U0001f510 Sign In / Sign Up", type="primary", use_container_width=True):
            st.session_state["show_auth"] = True
            st.rerun()

    st.markdown("")
    st.caption("Data: Yahoo Finance (.LK) \u00b7 CSE \u00b7 FRED \u00b7 World Bank \u00b7 NewsAPI")
    st.caption("AI: Claude \u00b7 OpenAI \u00b7 Gemini")

# \u2500\u2500 Redirect locked pages to auth \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
if page in ["\U0001f512 AI Briefing", "\U0001f512 Watchlist"]:
    st.session_state["show_auth"] = True

# \u2500\u2500 Show auth page if requested \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
if st.session_state.get("show_auth") and not is_logged_in():
    show_auth_page()
    st.stop()


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PAGE: DASHBOARD
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
elif page == "\U0001f1f1\U0001f1f0 CSE Market":
    page_cse_market()

if page == "\U0001f3e0 Dashboard":
    st.title("\U0001f4ca Market Dashboard")
    _dash_tier = "Live (Premium)" if is_paid_user() else "15-min delayed (Free)"
    st.caption(f"\u00b7 {datetime.now().strftime('%A, %d %B %Y %H:%M')} \u00b7 Data: {_dash_tier} \u00b7 Auto-refreshes automatically")

    with st.spinner("Loading market data\u2026"):
        gold   = current_price("GC=F")
        silver = current_price("SI=F")
        usd_lkr= current_price("LKR=X")
        sp500  = current_price("^GSPC")
        vix    = current_price("^VIX")
        oil    = current_price("BZ=F")
        sensex = current_price("^BSESN")
        nifty  = current_price("^NSEI")

    def metric_delta(d: dict) -> str | None:
        return f"{d['change_pct']:+.2f}%" if d.get("change_pct") is not None else None

    st.markdown("### \U0001f511 Key Indicators")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        v = gold.get("close")
        st.metric("Gold (USD/oz)", f"${v:,.2f}" if v else "N/A", metric_delta(gold))
    with col2:
        g = gold.get("close"); r = usd_lkr.get("close")
        gold_lkr = g * r if g and r else None
        st.metric("Gold (LKR/oz)", fmt_lkr(gold_lkr), metric_delta(gold))
    with col3:
        v = usd_lkr.get("close")
        st.metric("USD / LKR", f"LKR {v:,.2f}" if v else "N/A",
                  metric_delta(usd_lkr), delta_color="inverse")
    with col4:
        v = vix.get("close")
        st.metric("VIX Fear Index", f"{v:.2f}" if v else "N/A",
                  metric_delta(vix), delta_color="inverse")

    # CSE indices row
    aspi_d = current_price("^CSEALL")
    sl20_d = current_price("^SL20")
    if aspi_d.get("close") or sl20_d.get("close"):
        st.markdown("#### \U0001f1f1\U0001f1f0 CSE Indices")
        ci1, ci2, ci3, ci4 = st.columns(4)
        with ci1:
            v = aspi_d.get("close")
            st.metric("ASPI", fmt_index(v), metric_delta(aspi_d) if v else None)
        with ci2:
            v = sl20_d.get("close")
            st.metric("S&P SL20", fmt_index(v), metric_delta(sl20_d) if v else None)

    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**\U0001f310 US Markets**")
        for label, d in [("S&P 500", sp500), ("Brent Oil", oil)]:
            v = d.get("close"); p = d.get("change_pct") or 0
            c = "positive" if p >= 0 else "negative"
            prefix = "$" if "Oil" in label else ""
            st.markdown(f"{label}: `{prefix}{v:,.2f}` <span class='{c}'>{p:+.2f}%</span>"
                        if v else f"{label}: N/A", unsafe_allow_html=True)
    with col_b:
        st.markdown("**\U0001f30f Asian Markets**")
        for label, d in [("BSE Sensex", sensex), ("Nifty 50", nifty)]:
            v = d.get("close"); p = d.get("change_pct") or 0
            c = "positive" if p >= 0 else "negative"
            st.markdown(f"{label}: `{v:,.0f}` <span class='{c}'>{p:+.2f}%</span>"
                        if v else f"{label}: N/A", unsafe_allow_html=True)
    with col_c:
        st.markdown("**\U0001f4b0 Precious Metals**")
        for label, d, prefix in [("Silver", silver, "$"), ("Gold", gold, "$")]:
            v = d.get("close"); p = d.get("change_pct") or 0
            c = "positive" if p >= 0 else "negative"
            st.markdown(f"{label}: `{prefix}{v:,.2f}/oz` <span class='{c}'>{p:+.2f}%</span>"
                        if v else f"{label}: N/A", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### \U0001f4c9 30-Day Performance Comparison")
    with st.spinner("Loading chart\u2026"):
        tickers_chart = {"Gold": "GC=F", "Silver": "SI=F", "S&P 500": "^GSPC",
                         "Sensex": "^BSESN", "Oil": "BZ=F"}
        fig = go.Figure()
        for n, t in tickers_chart.items():
            df = fetch_price(t, "1mo")
            if df is not None and not df.empty:
                base = df["Close"].iloc[0]
                pct  = ((df["Close"] - base) / base * 100).round(2)
                fig.add_trace(go.Scatter(x=df.index, y=pct, name=n, mode="lines"))
        fig.update_layout(
            title="Normalised 30-day Return (%)", template="plotly_dark",
            legend=dict(orientation="h", y=-0.15),
            height=380, margin=dict(l=20, r=20, t=40, b=20),
            hovermode="x unified", yaxis_ticksuffix="%",
            paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
        st.plotly_chart(fig, use_container_width=True)


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PAGE: GOLD & SILVER
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
elif page == "\U0001f947 Gold & Silver":
    st.title("\U0001f947 Gold & Silver")
    st.caption("Precious metals \u2014 priced in USD and Sri Lankan Rupees")

    with st.spinner("Loading prices\u2026"):
        gold   = current_price("GC=F")
        silver = current_price("SI=F")
        usd_lkr_data = current_price("LKR=X")

    usd_lkr_rate = usd_lkr_data.get("close") or 320

    gp   = gold.get("close");   gpct = gold.get("change_pct")
    sp   = silver.get("close"); spct = silver.get("change_pct")
    gold_lkr_val   = gp * usd_lkr_rate if gp else None
    silver_lkr_val = sp * usd_lkr_rate if sp else None

    st.markdown("### Key Prices")
    m1, m2, m3 = st.columns(3)
    m1.metric("Gold (USD/oz)",    f"${gp:,.2f}"         if gp else "N/A",
              f"{gpct:+.2f}%"    if gpct else None)
    m2.metric("Gold (LKR/oz)",    fmt_lkr(gold_lkr_val),
              f"{gpct:+.2f}%"    if gpct else None)
    m3.metric("Gold (USD/gram)",  f"${gp/31.1035:,.2f}" if gp else "N/A")

    m4, m5, m6 = st.columns(3)
    m4.metric("Silver (USD/oz)",  f"${sp:,.2f}"         if sp else "N/A",
              f"{spct:+.2f}%"    if spct else None)
    m5.metric("Silver (LKR/oz)",  fmt_lkr(silver_lkr_val))
    m6.metric("Gold/Silver Ratio",f"{gp/sp:.1f}x"       if gp and sp else "N/A")

    st.caption("Gold (LKR) = Gold (USD/oz) \u00d7 USD/LKR rate. LKR depreciation amplifies gold returns.")

    st.markdown("---")
    st.markdown("### 1-Month Price Chart")
    choice = st.selectbox("Choose metal", ["Gold (GC=F)", "Silver (SI=F)"])
    ticker = "GC=F" if "Gold" in choice else "SI=F"
    with st.spinner("Loading chart\u2026"):
        df = fetch_price(ticker, "1mo")
        if df is not None and not df.empty:
            fig = go.Figure(go.Candlestick(
                x=df.index, open=df["Open"], high=df["High"],
                low=df["Low"],  close=df["Close"],
                increasing_line_color="#00d26a", decreasing_line_color="#ff4b4b"))
            fig.update_layout(
                template="plotly_dark", height=380,
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### Sri Lanka Macro Context")
    with st.spinner("Loading World Bank data\u2026"):
        gdp  = fetch_worldbank("NY.GDP.MKTP.CD")
        cpi  = fetch_worldbank("FP.CPI.TOTL.ZG")
        fdi  = fetch_worldbank("BX.KLT.DINV.CD.WD")
        rem  = fetch_worldbank("BX.TRF.PWKR.CD.DT")

    wb1, wb2, wb3, wb4 = st.columns(4)
    wb1.metric("GDP (USD bn)",
               f"${gdp['value']/1e9:.1f}B" if gdp.get("value") else "N/A",
               gdp.get("year",""))
    wb2.metric("Inflation (CPI %)",
               f"{cpi['value']:.1f}%" if cpi.get("value") else "N/A",
               cpi.get("year",""))
    wb3.metric("FDI (USD mn)",
               f"${fdi['value']/1e6:.0f}M" if fdi.get("value") else "N/A",
               fdi.get("year",""))
    wb4.metric("Remittances",
               f"${rem['value']/1e9:.2f}B" if rem.get("value") else "N/A",
               rem.get("year",""))


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PAGE: GLOBAL MARKETS
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
elif page == "\U0001f30d Global Markets":
    st.title("\U0001f30d Global Markets")
    st.caption("US, Asian, and European indices \u2014 with Sri Lanka context")

    with st.spinner("Fetching indices\u2026"):
        indices = {
            "S&P 500":    current_price("^GSPC"),
            "NASDAQ":     current_price("^IXIC"),
            "Dow Jones":  current_price("^DJI"),
            "VIX (Fear)": current_price("^VIX"),
            "BSE Sensex": current_price("^BSESN"),
            "Nifty 50":   current_price("^NSEI"),
            "Hang Seng":  current_price("^HSI"),
            "Nikkei 225": current_price("^N225"),
            "FTSE 100":   current_price("^FTSE"),
            "DAX":        current_price("^GDAXI"),
        }

    st.markdown("### Live Prices")
    names = list(indices.keys())
    row1, row2 = names[:5], names[5:]

    for row in [row1, row2]:
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            d = indices[name]; v = d.get("close"); p = d.get("change_pct")
            col.metric(name, fmt_index(v), f"{p:+.2f}%" if p is not None else None,
                       delta_color="inverse" if name == "VIX (Fear)" else "normal")

    st.markdown("---")
    st.markdown("### 1-Month Chart")
    market_choice = st.selectbox("Choose Market", list(indices.keys()))
    tmap = {"S&P 500": "^GSPC", "NASDAQ": "^IXIC", "Dow Jones": "^DJI",
            "VIX (Fear)": "^VIX", "BSE Sensex": "^BSESN", "Nifty 50": "^NSEI",
            "Hang Seng": "^HSI", "Nikkei 225": "^N225", "FTSE 100": "^FTSE", "DAX": "^GDAXI"}
    with st.spinner("Loading chart\u2026"):
        df = fetch_price(tmap.get(market_choice, "^GSPC"), "1mo")
        if df is not None and not df.empty:
            fig = go.Figure(go.Scatter(x=df.index, y=df["Close"], fill="tozeroy",
                                       line=dict(color="#3b82f6", width=2)))
            fig.update_layout(template="plotly_dark", height=350,
                              margin=dict(l=20, r=20, t=30, b=20),
                              paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### \U0001f4b1 Forex \u2014 Sri Lanka Relevant Pairs")
    with st.spinner("Loading forex\u2026"):
        forex = {"USD/LKR": current_price("LKR=X"),  "EUR/LKR": current_price("EURLKR=X"),
                 "GBP/LKR": current_price("GBPLKR=X"), "AED/LKR": current_price("AEDLKR=X"),
                 "JPY/LKR": current_price("JPYLKR=X"), "USD/EUR":  current_price("EURUSD=X")}
    fx_cols = st.columns(len(forex))
    for col, (pair, d) in zip(fx_cols, forex.items()):
        v = d.get("close"); p = d.get("change_pct")
        col.metric(pair, f"{v:,.4f}" if v else "N/A", f"{p:+.2f}%" if p is not None else None)


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PAGE: NEWS FEED
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
elif page == "\U0001f4f0 News Feed":
    st.title("\U0001f4f0 News Feed")
    st.caption("Latest financial news \u2014 categorised for Sri Lankan investors")

    categories = {
        "Sri Lanka":     "Sri Lanka",
        "Gold & Silver": "gold silver price precious metals",
        "US Economy":    "Federal Reserve inflation US economy",
        "Asian Markets": "India China Asian stock market",
        "Oil & Energy":  "oil price OPEC energy commodity",
        "Geopolitical":  "geopolitical risk war sanctions",
    }
    tabs = st.tabs(["\U0001f334 Sri Lanka", "\U0001f947 Gold & Silver", "\U0001f4b5 US Economy",
                    "\U0001f30f Asian Markets", "\u26a1 Oil & Energy", "\U0001f30d Geopolitical"])

    for tab, (cat_name, query) in zip(tabs, categories.items()):
        with tab:
            with st.spinner(f"Loading {cat_name} news\u2026"):
                articles = fetch_news(query, n=10)
            if not articles:
                if not NEWS_API_KEY:
                    st.warning("Add NEWS_API_KEY to your secrets to see news.")
                else:
                    st.info("No recent articles found. Try refreshing later.")
                continue
            for art in articles:
                title  = art.get("title", "")
                desc   = art.get("description", "") or ""
                url    = art.get("url", "")
                source = art.get("source", {}).get("name", "")
                pub_at = art.get("publishedAt", "")[:10]
                desc   = re.sub(r"<[^>]+>", "", desc).strip()
                if title and "[Removed]" not in title:
                    with st.container():
                        st.markdown(f"**[{title}]({url})**")
                        if desc and "[Removed]" not in desc:
                            st.caption(desc[:220])
                        st.caption(f"{source} \u00b7 {pub_at}")
                        st.markdown("---")


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PAGE: AI BRIEFING  (Premium)
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
elif page == "\U0001f916 AI Briefing":
    if not is_logged_in():
        show_premium_gate("AI Market Briefing")
        st.stop()

    st.title("\U0001f916 AI Market Briefing")
    st.caption("Daily market analysis powered by Claude AI (with OpenAI and Gemini fallback)")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        gen_btn = st.button("\u2728 Generate Today's Briefing", type="primary",
                            use_container_width=True)
    with col_info:
        if st.session_state.get("briefing"):
            st.success("Today's briefing is ready \u2014 scroll down to read it, or regenerate.")
        else:
            st.info("Click to generate today's AI market briefing (takes ~30\u201360 seconds).")

    with st.expander("AI Provider Status"):
        claude_status = 'Configured \u2713' if ANTHROPIC_API_KEY else '\u274c Missing ANTHROPIC_API_KEY'
        openai_status = 'Configured \u2713' if OPENAI_API_KEY else '\u274c Missing OPENAI_API_KEY'
        gemini_status = 'Configured \u2713' if GEMINI_API_KEY else '\u274c Missing GEMINI_API_KEY'
        st.markdown(f"\U0001f7e2 **Claude (Primary):** {claude_status}")
        st.markdown(f"\U0001f7e1 **OpenAI (Secondary):** {openai_status}")
        st.markdown(f"\U0001f7e0 **Gemini (Fallback):** {gemini_status}")

    if gen_btn:
        with st.spinner("\U0001f9e0 Fetching market data and generating briefing\u2026"):
            md = {k: current_price(t) for k, t in {
                "gold": "GC=F", "silver": "SI=F", "usd_lkr": "LKR=X",
                "sp500": "^GSPC", "vix": "^VIX", "oil": "BZ=F",
                "sensex": "^BSESN", "nifty": "^NSEI",
                "dxy": "DX=F", "nasdaq": "^IXIC"}.items()}
            briefing_text, model_used = generate_briefing(md)

        if briefing_text and "failed" not in briefing_text.lower()[:50]:
            st.success(f"\u2705 Generated by **{model_used}**")
            st.session_state["briefing"]   = briefing_text
            st.session_state["model_used"] = model_used
        else:
            st.error(briefing_text)

    briefing_to_show = st.session_state.get("briefing")
    model_label      = st.session_state.get("model_used", "")

    if briefing_to_show:
        st.markdown("---")
        if model_label: st.caption(f"Generated by: {model_label}")

        col_read, col_save = st.columns([4, 1])
        with col_read:
            st.markdown(briefing_to_show)
        with col_save:
            st.markdown("##### Save Briefing")
            save_title = st.text_input("Title", value=f"Briefing {date.today()}", key="save_title")
            # Extract sentiment
            sent = "NEUTRAL"
            text_lower = briefing_to_show.lower()
            if "bullish" in text_lower: sent = "BULLISH"
            elif "bearish" in text_lower: sent = "BEARISH"
            if st.button("\U0001f4be Save to My Reports", use_container_width=True):
                if db_save_briefing(save_title, briefing_to_show, model_label, sent):
                    st.success("Saved!")
                else:
                    st.error("Save failed \u2014 make sure you're logged in.")


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PAGE: WATCHLIST  (Premium)
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
elif page == "\u2b50 Watchlist":
    if not is_logged_in():
        show_premium_gate("Watchlist")
        st.stop()

    st.title("\u2b50 My Watchlist")
    st.caption("Track your favourite tickers \u2014 CSE stocks, global indices, commodities")

    # \u2500\u2500 Add ticker \u2500\u2500
    with st.expander("\u2795 Add Ticker", expanded=False):
        ac1, ac2, ac3, ac4 = st.columns([2, 2, 1.5, 1])
        with ac1: new_t = st.text_input("Ticker symbol", placeholder="JKH.N0000 or ^GSPC")
        with ac2: new_n = st.text_input("Display name",  placeholder="John Keells")
        with ac3: cat   = st.selectbox("Category", ["stock", "index", "commodity", "forex"])
        with ac4:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            if st.button("Add \u2192", type="primary"):
                if new_t and new_n:
                    t_clean = new_t.strip().upper()
                    if not _valid_ticker(t_clean):
                        st.error("Invalid ticker symbol. Use letters, digits, ^, =, . only (max 20 chars).")
                    elif db_add_watchlist(t_clean, new_n.strip()[:60], cat):
                        st.success(f"\u2705 {t_clean} added!")
                        st.rerun()
                    else:
                        st.error("Could not add ticker. It may already exist.")
                else:
                    st.warning("Enter ticker and name.")

    # \u2500\u2500 Display \u2500\u2500
    items = db_get_watchlist()
    if not items:
        st.info("Your watchlist is empty. Add tickers above to start tracking.")
    else:
        st.markdown(f"**{len(items)} tickers tracked**")
        st.markdown("---")

        cat_colors = {"stock": "#1e3a5f", "index": "#1a3040",
                      "commodity": "#2d3520", "forex": "#2a1f40"}

        hdr = st.columns([3, 2, 2, 1.5, 0.8])
        for h, t in zip(hdr, ["Ticker", "Price", "Change", "Added", ""]):
            h.markdown(f"**{t}**")
        st.markdown("---")

        for item in items:
            ticker = item["ticker"]
            d      = current_price(ticker)
            v      = d.get("close")
            p      = d.get("change_pct")
            cc     = cat_colors.get(item.get("category", "stock"), "#1e2440")
            cat_badge = (f'<span style="background:{cc};color:#7b8cde;'
                         f'padding:1px 7px;border-radius:4px;font-size:0.68rem">'
                         f'{_html.escape(item.get("category","").upper())}</span>')

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1.5, 0.8])
            with c1:
                st.markdown(f"**{_html.escape(str(item['ticker_name']))}** {cat_badge}",
                            unsafe_allow_html=True)
                st.caption(ticker)
            with c2:
                st.markdown(f"**{v:,.2f}**" if v else "\u2014")
            with c3:
                if p is not None:
                    arrow = "\u25b2" if p >= 0 else "\u25bc"
                    cls   = "positive" if p >= 0 else "negative"
                    st.markdown(f'<span class="{cls}">{arrow} {abs(p):.2f}%</span>',
                                unsafe_allow_html=True)
                else:
                    st.markdown("\u2014")
            with c4:
                st.caption(item.get("added_at", "")[:10])
            with c5:
                if st.button("\u2715", key=f"rm_{ticker}"):
                    db_remove_watchlist(ticker)
                    st.rerun()
            st.markdown("---")


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PAGE: PORTFOLIO
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
elif page == "\U0001f4ca Portfolio":
    if not is_logged_in():
        st.info("Sign in to manage your investment portfolio.")
        st.stop()

    st.title("\U0001f4ca My Portfolio")

    with st.spinner("Loading CSE prices..."):
        board = fetch_cse_board()

    holdings = db_get_portfolio_holdings()
    display_portfolio_dashboard(holdings, board)


# PAGE: MY REPORTS  (Premium)
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
elif page == "\U0001f4cb My Reports":
    if not is_logged_in():
        show_premium_gate("My Reports")
        st.stop()

    st.title("\U0001f4cb My Reports")
    st.caption("Saved AI briefings and personal investment notes")

    tab_b, tab_n = st.tabs(["\U0001f916 Saved Briefings", "\U0001f4dd My Notes"])

    # \u2500\u2500 SAVED BRIEFINGS \u2500\u2500
    with tab_b:
        briefings = db_get_briefings()
        if not briefings:
            st.info("No saved briefings yet. Generate one on the AI Briefing page and tap 'Save'.")
        else:
            st.markdown(f"**{len(briefings)} briefings saved**")
            for b in briefings:
                sent  = b.get("sentiment", "")
                sent_badge = {"BULLISH": "\U0001f7e2", "BEARISH": "\U0001f534", "NEUTRAL": "\U0001f7e1"}.get(sent, "\u26aa")
                title = b.get("title", "Briefing")
                dt    = b.get("created_at", "")[:10]
                with st.expander(f"{sent_badge} {title} \u2014 {dt}"):
                    st.markdown(b.get("content", ""))
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.caption(f"Model: {b.get('model_used','?')} \u00b7 Sentiment: {sent or 'N/A'}")
                    with c2:
                        if st.button("\U0001f5d1 Delete", key=f"del_b_{b['id']}"):
                            db_delete_briefing(b["id"])
                            st.rerun()

    # \u2500\u2500 MY NOTES \u2500\u2500
    with tab_n:
        # New note form
        with st.expander("\u270f\ufe0f Write New Note", expanded=False):
            nc1, nc2 = st.columns([3, 1])
            with nc1: n_title = st.text_input("Note title", placeholder="My CSE Analysis")
            with nc2: n_pinned = st.checkbox("\U0001f4cc Pin")
            n_content = st.text_area("Content", height=140,
                                     placeholder="Your thoughts, analysis, reminders\u2026")
            n_tags = st.text_input("Tags (comma separated)",
                                   placeholder="CSE, gold, weekly-review")
            if st.button("\U0001f4be Save Note", type="primary"):
                if n_title and n_content:
                    tags = [t.strip() for t in n_tags.split(",") if t.strip()]
                    db_save_note(n_title, n_content, tags, n_pinned)
                    st.success("\u2705 Note saved!")
                    st.rerun()
                else:
                    st.warning("Enter a title and content.")

        st.markdown("---")
        notes = db_get_notes()
        if not notes:
            st.info("No notes yet. Write your first investment note above!")
        else:
            st.markdown(f"**{len(notes)} notes**")
            for n in notes:
                pin_icon = "\U0001f4cc " if n.get("is_pinned") else ""
                tags_html = " ".join(
                    f'<span style="background:#1e2440;color:#7b8cde;'
                    f'padding:1px 8px;border-radius:4px;font-size:0.72rem">{_html.escape(str(t))}</span>'
                    for t in (n.get("tags") or []))
                label = f"{pin_icon}{_html.escape(str(n.get('title','Note')))[:80]} \u2014 {n.get('updated_at','')[:10]}"
                with st.expander(label):
                    if tags_html:
                        st.markdown(tags_html, unsafe_allow_html=True)
                        st.markdown("")
                    edited = st.text_area("", value=n.get("content", ""), height=130,
                                          key=f"edit_{n['id']}")
                    ec1, ec2, ec3 = st.columns([3, 1, 1])
                    with ec1:
                        st.caption(f"Updated {n.get('updated_at','')[:16]}")
                    with ec2:
                        if st.button("\U0001f4be Save", key=f"sv_{n['id']}"):
                            db_update_note(n["id"], content=edited)
                            st.success("Saved!")
                            st.rerun()
                    with ec3:
                        if st.button("\U0001f5d1 Del", key=f"dn_{n['id']}"):
                            db_delete_note(n["id"])
                            st.rerun()


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# PAGE: ABOUT
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
elif page == "\u2139\ufe0f About":
    st.title("\u2139\ufe0f About InvestSmart")
    st.markdown("""
## What is InvestSmart?

InvestSmart is an AI-powered investment intelligence platform built specifically for Sri Lankan investors.
It monitors global market factors that affect the Colombo Stock Exchange (CSE), gold, silver, and bonds \u2014
and generates daily AI briefings to help you make better-informed investment decisions.

## Data Sources

| Source | What We Use It For |
|--------|--------------------|
| Yahoo Finance | 40+ tickers \u2014 gold, silver, CSE (.LK stocks), indices, forex, global markets |
| FRED (Federal Reserve) | US macro data: interest rates, inflation, yield curve |
| World Bank Open API | Sri Lanka macro: GDP, CPI, FDI, remittances |
| NewsAPI | 6 categories of financial news |

## AI Technology

| Priority | Model | Purpose |
|----------|-------|---------|
| 1st | claude-sonnet-4-6 (Anthropic) | Daily briefings, sector analysis |
| 2nd | GPT-4o (OpenAI) | Fallback for briefings |
| 3rd | Gemini 1.5 Flash (Google) | Free fallback |

## Platform Architecture

- **Frontend:** Streamlit (Python)
- **Hosting:** Streamlit Community Cloud
- **Database & Auth:** Supabase (PostgreSQL + Auth)
- **Auth Methods:** Email/Password \u00b7 Google OAuth \u00b7 Phone SMS OTP

## Account Features (Free vs Premium)

| Feature | Free | Logged In | Premium |
|---------|------|-----------|---------|
| Dashboard (ASPI/SL20) | \u2705 | \u2705 | \u2705 |
| CSE Market (15-min data) | \u2705 | \u2705 | \u2014 |
| CSE Market (Live 1-min) | \u2014 | \u2014 | \u2705 |
| Gold & Silver | \u2705 | \u2705 | \u2705 |
| Global Markets | \u2705 | \u2705 | \u2705 |
| News Feed | \u2705 | \u2705 | \u2705 |
| AI Briefing | \u2014 | \u2705 | \u2705 |
| Watchlist | \u2014 | \u2705 | \u2705 |
| My Reports & Notes | \u2014 | \u2705 | \u2705 |
| CSE Price Recording (DB) | \u2014 | \u2705 | \u2705 |

## Disclaimer

InvestSmart is for **informational purposes only**. Nothing on this platform constitutes
investment advice. Always do your own research and consult a licensed financial advisor
before making investment decisions.

*Built for Sri Lankan investors \u00b7 v2.0 \u2014 with Authentication*
""")daily AI briefings to help you make better-informed investment decisions.

## Data Sources

| Source | What We Use It For |
|--------|--------------------|
| Yahoo Finance | 40+ tickers \u2014 gold, silver, CSE (.LK stocks), indices, forex, global markets |
| FRED (Federal Reserve) | US macro data: interest rates, inflation, yield curve |
| World Bank Open API | Sri Lanka macro: GDP, CPI, FDI, remittances |
| NewsAPI | 6 categories of financial news |

## AI Technology

| Priority | Model | Purpose |
|----------|-------|---------|
| 1st | claude-sonnet-4-6 (Anthropic) | Daily briefings, sector analysis |
| 2nd | GPT-4o (OpenAI) | Fallback for briefings |
| 3rd | Gemini 1.5 Flash (Google) | Free fallback |

## Platform Architecture

- **Frontend:** Streamlit (Python)
- **Hosting:** Streamlit Community Cloud
- **Database & Auth:** Supabase (PostgreSQL + Auth)
- **Auth Methods:** Email/Password \u00b7 Google OAuth \u00b7 Phone SMS OTP

## Account Features (Free vs Premium)

| Feature | Free | Logged In | Premium |
|---------|------|-----------|---------|
| Dashboard (ASPI/SL20) | \u2705 | \u2705 | \u2705 |
| CSE Market (15-min data) | \u2705 | \u2705 | \u2014 |
| CSE Market (Live 1-min) | \u2014 | \u2014 | \u2705 |
| Gold & Silver | \u2705 | \u2705 | \u2705 |
| Global Markets | \u2705 | \u2705 | \u2705 |
| News Feed | \u2705 | \u2705 | \u2705 |
| AI Briefing | \u2014 | \u2705 | \u2705 |
| Watchlist | \u2014 | \u2705 | \u2705 |
| My Reports & Notes | \u2014 | \u2705 | \u2705 |
| CSE Price Recording (DB) | \u2014 | \u2705 | \u2705 |

## Disclaimer

InvestSmart is for **informational purposes only**. Nothing on this platform constitutes
investment advice. Always do your own research and consult a licensed financial advisor
before making investment decisions.

*Built for Sri Lankan investors \u00b7 v2.0 \u2014 with Authentication*
""")
daily AI briefings to help you make better-informed investment decisions.

## Data Sources

| Source | What We Use It For |
|--------|--------------------|
| Yahoo Finance | 40+ tickers — gold, silver, CSE (.LK stocks), indices, forex, global markets |
| FRED (Federal Reserve) | US macro data: interest rates, inflation, yield curve |
| World Bank Open API | Sri Lanka macro: GDP, CPI, FDI, remittances |
| NewsAPI | 6 categories of financial news |

## AI Technology

| Priority | Model | Purpose |
|----------|-------|---------|
| 1st | claude-sonnet-4-6 (Anthropic) | Daily briefings, sector analysis |
| 2nd | GPT-4o (OpenAI) | Fallback for briefings |
| 3rd | Gemini 1.5 Flash (Google) | Free fallback |

## Platform Architecture

- **Frontend:** Streamlit (Python)
- **Hosting:** Streamlit Community Cloud
- **Database & Auth:** Supabase (PostgreSQL + Auth)
- **Auth Methods:** Email/Password · Google OAuth · Phone SMS OTP

## Account Features (Free vs Premium)

| Feature | Free | Logged In | Premium |
|---------|------|-----------|---------|
| Dashboard (ASPI/SL20) | ✅ | ✅ | ✅ |
| CSE Market (15-min data) | ✅ | ✅ | — |
| CSE Market (Live 1-min) | — | — | ✅ |
| Gold & Silver | ✅ | ✅ | ✅ |
| Global Markets | ✅ | ✅ | ✅ |
| News Feed | ✅ | ✅ | ✅ |
| AI Briefing | — | ✅ | ✅ |
| Watchlist | — | ✅ | ✅ |
| My Reports & Notes | — | ✅ | ✅ |
| CSE Price Recording (DB) | — | ✅ | ✅ |

## Disclaimer

InvestSmart is for **informational purposes only**. Nothing on this platform constitutes
investment advice. Always do your own research and consult a licensed financial advisor
before making investment decisions.

*Built for Sri Lankan investors · v2.0 — with Authentication*
""")
 making investment decisions.

*Built for Sri Lankan investors · v2.0 — with Authentication*
""")

""")
