"""
app.py â InvestSmart v2.0
Streamlit dashboard + full authentication for CSE & global market intelligence.

Pages (Free):    Dashboard Â· Gold & Silver Â· Global Markets Â· News Feed Â· About
Pages (Premium): AI Briefing Â· Watchlist Â· My Reports  (require login)

Auth:  Supabase â Email/Password Â· Google OAuth Â· Phone SMS OTP
"""

import os
import re
import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

try:
    from supabase import create_client
    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False

load_dotenv()

# âââââââââââââââââââââââââââââââââââââââââââââââââ
# SECRETS
# âââââââââââââââââââââââââââââââââââââââââââââââââ
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
APP_URL           = "https://investsmart-uznzrnzf4rdkmthkmtuofc.streamlit.app"

# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PAGE CONFIG
# âââââââââââââââââââââââââââââââââââââââââââââââââ
st.set_page_config(
    page_title="InvestSmart â CSE Intelligence",
    page_icon="ð",
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

  /* ââ Auth ââ */
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

# âââââââââââââââââââââââââââââââââââââââââââââââââ
# FORMATTERS
# âââââââââââââââââââââââââââââââââââââââââââââââââ
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

# âââââââââââââââââââââââââââââââââââââââââââââââââ
# SUPABASE CLIENT
# âââââââââââââââââââââââââââââââââââââââââââââââââ
@st.cache_resource
def _get_sb():
    if not _SUPABASE_OK or not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

_sb = _get_sb()

# ââ Auth state helpers âââââââââââââââââââââââââââââ
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
    except:
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
        except: pass
    for k in ["auth_user", "auth_session", "auth_profile"]:
        st.session_state[k] = None
    st.session_state["show_auth"] = False
    st.rerun()

# ââ DB helpers ââââââââââââââââââââââââââââââââââââ
def db_get_watchlist():
    user = get_user()
    if not user or not _sb: return []
    try:
        r = _sb.table("watchlist").select("*").eq("user_id", user.id).order("added_at", desc=True).execute()
        return r.data or []
    except: return []

def db_add_watchlist(ticker: str, name: str, category: str = "stock") -> bool:
    user = get_user()
    if not user or not _sb: return False
    try:
        _sb.table("watchlist").upsert({
            "user_id": user.id, "ticker": ticker,
            "ticker_name": name, "category": category
        }).execute()
        return True
    except: return False

def db_remove_watchlist(ticker: str):
    user = get_user()
    if not user or not _sb: return
    try:
        _sb.table("watchlist").delete().eq("user_id", user.id).eq("ticker", ticker).execute()
    except: pass

def db_save_briefing(title: str, content: str, model: str, sentiment: str = "") -> bool:
    user = get_user()
    if not user or not _sb: return False
    try:
        _sb.table("saved_briefings").insert({
            "user_id": user.id, "title": title,
            "content": content, "model_used": model, "sentiment": sentiment
        }).execute()
        return True
    except: return False

def db_get_briefings():
    user = get_user()
    if not user or not _sb: return []
    try:
        r = _sb.table("saved_briefings").select("*").eq("user_id", user.id)\
               .order("created_at", desc=True).limit(30).execute()
        return r.data or []
    except: return []

def db_delete_briefing(bid: int):
    user = get_user()
    if not user or not _sb: return
    try:
        _sb.table("saved_briefings").delete().eq("id", bid).eq("user_id", user.id).execute()
    except: pass

def db_get_notes():
    user = get_user()
    if not user or not _sb: return []
    try:
        r = _sb.table("user_notes").select("*").eq("user_id", user.id)\
               .order("is_pinned", desc=True).order("updated_at", desc=True).execute()
        return r.data or []
    except: return []

def db_save_note(title: str, content: str, tags=None, is_pinned: bool = False):
    user = get_user()
    if not user or not _sb: return None
    try:
        r = _sb.table("user_notes").insert({
            "user_id": user.id, "title": title,
            "content": content, "tags": tags or [], "is_pinned": is_pinned
        }).execute()
        return r.data[0] if r.data else None
    except: return None

def db_update_note(nid: int, **kwargs):
    user = get_user()
    if not user or not _sb: return
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    try:
        _sb.table("user_notes").update(kwargs).eq("id", nid).eq("user_id", user.id).execute()
    except: pass

def db_delete_note(nid: int):
    user = get_user()
    if not user or not _sb: return
    try:
        _sb.table("user_notes").delete().eq("id", nid).eq("user_id", user.id).execute()
    except: pass

# âââââââââââââââââââââââââââââââââââââââââââââââââ
# AUTH PAGE UI
# âââââââââââââââââââââââââââââââââââââââââââââââââ
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
    """Render Google OAuth button and return URL, or None if unavailable."""
    if not _sb: return
    try:
        g = _sb.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": APP_URL, "scopes": "email profile"}
        })
        st.markdown(f"""<div class="google-btn-wrap">
          <a href="{g.url}" target="_self">
            <div class="google-btn">{_G_ICON}&nbsp; {label}</div>
          </a></div>""", unsafe_allow_html=True)
    except:
        st.caption("Google sign-in not yet configured â use email or phone below.")

def show_auth_page():
    """Full-screen auth page: Sign In Â· Create Account Â· Phone Â· Reset."""
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        # Logo
        st.markdown("""
        <div class="auth-logo">
          <div class="icon">ð</div>
          <div class="brand">InvestSmart</div>
          <div class="tagline">CSE Intelligence Platform</div>
        </div>""", unsafe_allow_html=True)

        # Inline error/success
        if st.session_state.get("auth_error"):
            st.error(st.session_state.pop("auth_error"))
        if st.session_state.get("auth_success"):
            st.success(st.session_state.pop("auth_success"))

        tab_si, tab_su, tab_ph, tab_pw = st.tabs(
            ["ð Sign In", "â¨ Create Account", "ð± Phone OTP", "ð Reset Password"]
        )

        # ââ SIGN IN ââââââââââââââââââââââââââââââââââ
        with tab_si:
            _google_btn("Continue with Google")
            st.markdown('<div class="or-divider">or sign in with email</div>',
                        unsafe_allow_html=True)

            with st.form("f_signin"):
                email    = st.text_input("Email address", placeholder="you@example.com",
                                         key="si_email")
                password = st.text_input("Password", type="password",
                                         placeholder="Your password", key="si_pw")
                ok = st.form_submit_button("Sign In â", use_container_width=True,
                                           type="primary")
            if ok:
                if not email or not password:
                    st.error("Enter both email and password.")
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
                            st.error("â Invalid email or password.")
                        elif "not confirmed" in err:
                            st.warning("ð§ Please verify your email before signing in.")
                        else:
                            st.error(f"Sign-in failed: {e}")

        # ââ CREATE ACCOUNT ââââââââââââââââââââââââââââ
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
                sub = st.form_submit_button("Create Account â",
                                            use_container_width=True, type="primary")
            if sub:
                if not name or not s_email or not s_pw:
                    st.error("Please fill all fields.")
                elif s_pw != s_pw2:
                    st.error("Passwords don't match.")
                elif len(s_pw) < 8:
                    st.error("Password must be at least 8 characters.")
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
                                "â Account created! Check your email to verify, then sign in.")
                        else:
                            st.error("Sign-up failed. Email may already be registered.")
                    except Exception as e:
                        st.error(f"Sign-up failed: {e}")

        # ââ PHONE OTP ââââââââââââââââââââââââââââââââ
        with tab_ph:
            st.caption("Enter your mobile number â we'll send a 6-digit SMS code.")
            st.info("Include country code Â· e.g. **+94 77 123 4567** for Sri Lanka")

            if st.session_state.get("phone_step", 1) == 1:
                with st.form("f_phone"):
                    ph = st.text_input("Mobile number", placeholder="+94771234567",
                                       value=st.session_state.get("phone_number", ""))
                    send = st.form_submit_button("Send SMS Code â",
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
                    verify = st.form_submit_button("Verify & Sign In â",
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
                if st.button("â Change number"):
                    st.session_state["phone_step"] = 1
                    st.rerun()

        # ââ RESET PASSWORD âââââââââââââââââââââââââââ
        with tab_pw:
            st.caption("We'll email you a link to reset your password.")
            with st.form("f_reset"):
                r_email = st.text_input("Registered email", placeholder="you@example.com")
                send_r  = st.form_submit_button("Send Reset Link â",
                                                use_container_width=True, type="primary")
            if send_r:
                if not r_email:
                    st.error("Enter your email address.")
                elif _sb:
                    try:
                        _sb.auth.reset_password_email(
                            r_email, options={"redirect_to": APP_URL})
                        st.success("â Reset link sent! Check your inbox.")
                    except Exception as e:
                        st.error(f"Failed: {e}")

        st.markdown("")
        if st.button("â Back to App", use_container_width=True):
            st.session_state["show_auth"] = False
            st.rerun()


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PREMIUM GATE
# âââââââââââââââââââââââââââââââââââââââââââââââââ
def show_premium_gate(feature: str = "this feature"):
    st.markdown(f"""
    <div class="premium-gate">
      <h2>ð Login Required</h2>
      <p>Please sign in to access {feature}.</p>
    </div>""", unsafe_allow_html=True)
    if st.button("ð Sign In / Create Account", type="primary", use_container_width=False):
        st.session_state["show_auth"] = True
        st.rerun()


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# DATA FETCHING (cached)
# âââââââââââââââââââââââââââââââââââââââââââââââââ
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
    except: return None

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
        obs = r.json().get("observations", [])
        return float(obs[0]["value"]) if obs and obs[0]["value"] != "." else None
    except: return None

@st.cache_data(ttl=1800)
def fetch_news(query: str, n: int = 8) -> list:
    if not NEWS_API_KEY: return []
    try:
        r = requests.get("https://newsapi.org/v2/top-headlines",
                         params={"q": query, "apiKey": NEWS_API_KEY,
                                 "pageSize": n, "language": "en"}, timeout=10)
        articles = r.json().get("articles", [])
        if not articles:
            r2 = requests.get("https://newsapi.org/v2/everything",
                              params={"q": query, "apiKey": NEWS_API_KEY,
                                      "pageSize": n, "language": "en",
                                      "sortBy": "publishedAt",
                                      "from": str(date.today() - timedelta(days=7))},
                              timeout=10)
            articles = r2.json().get("articles", [])
        return [a for a in articles if "[Removed]" not in (a.get("title") or "")][:n]
    except: return []

@st.cache_data(ttl=21600)
def fetch_worldbank(indicator: str, country: str = "LK") -> dict:
    try:
        r = requests.get(
            f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}",
            params={"format": "json", "mrv": 1}, timeout=10)
        data = r.json()
        if len(data) > 1 and data[1]:
            item = data[1][0]
            return {"value": item.get("value"), "year": item.get("date", "")}
        return {}
    except: return {}


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# AI BRIEFING
# âââââââââââââââââââââââââââââââââââââââââââââââââ
def call_claude_briefing(prompt: str) -> tuple[str, str]:
    if ANTHROPIC_API_KEY:
        try:
            import anthropic
            c = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            m = c.messages.create(model="claude-sonnet-4-6", max_tokens=2500,
                                  messages=[{"role": "user", "content": prompt}])
            return m.content[0].text, "Claude (claude-sonnet-4-6)"
        except Exception as e:
            st.warning(f"Claude unavailable ({e}) â trying OpenAJâ¨¦")
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
            st.warning(f"OpenAI unavailable ({e}) â trying Geminiâ¦")
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
    gold_usd = md.get("gold",   {}).get("close")
    usd_lkr  = md.get("usd_lkr", {}).get("close")
    gold_lkr = (gold_usd * usd_lkr) if gold_usd and usd_lkr else None

    def fmt(d, prefix=""):
        if d and d.get("close"):
            c, pct = d["close"], d.get("change_pct", 0) or 0
            return f"{prefix}{c:,.2f}  {'â°' if pct>=0 else 'â¼'}{pct:+,2f}%"
        return "N/A"

    prompt = f"""You are a senior investment analyst with deep expertise in the Colombo Stock Exchange (CSE), Sri Lankan markets, and global macro investing. Write a concise but complete daily market briefing for Sri Lankan retail investors.

TODAY: {today}

MARKET DATA:
â¢ Gold (USD/oz):      {fmt(md.get('gold'),    '$')}
â¢ Gold (LKR/oz):      {(f"LKR {gold_lkr:,.0f}") if gold_lkr else 'N/A'}
â¢ Silver (USD/oz):    {fmt(md.get('silver'),  '$')}
â¢ Oil Brent:          {fmt(md.get('oil'),     '$')}
â¢ S&P 500:            {fmt(md.get('sp500'))}
â¢ VIX:                {fmt(md.get('vix'))}
â¢ USD/LKR:            {fmt(md.get('usd_lkr'))}
â¢ USD Index (DXY):    {fmt(md.get('dxy'))}
â¢ BSE Sensex:         {fmt(md.get('sensex'))}
â¢ Nifty 50:           {fmt(md.get('nifty'))}

Write a structured briefing:
1. CSE Outlook â how today's data affects the Colombo Stock Exchange
2. Gold & Silver in LKR â critical for Sri Lankan investors
3. Global Macro Summary â US markets, Asia, forex
4. Key Risks & Opportunities
5. Sentiment Score: BULLISH / NEUTRAL / BEARISH for CSE, Gold, USD/LKR

Reference actual numbers. 2â3 sentences per section. End with:
*Not investment advice â for information only.*"""
    return call_claude_briefing(prompt)


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# INIT + SIDEBAR
# âââââââââââââââââââââââââââââââââââââââââââââââââ
_init_state()
if _sb: _handle_oauth_callback()

with st.sidebar:
    st.markdown("## ð InvestSmart")
    st.markdown("*CSE Intelligence Platform*")
    st.markdown("---")

    # ââ User card (logged in) ââ
    if is_logged_in():
        profile = get_profile()
        user    = get_user()
        name    = (profile.get("full_name") or
                   (user.email.split("@")[0].title() if user.email else "User"))
        avatar  = profile.get("avatar_url", "")
        tier    = profile.get("tier", "free")
        email_s = (user.email or "")[:30] + ("â¦" if len(user.email or "") > 30 else "")

        if avatar:
            avatar_html = f'<img src="{avatar}" width="38" style="border-radius:50%;flex-shrink:0"/>'
        else:
            initials    = name[0].upper() if name else "U"
            avatar_html = f'<div class="user-avatar">{initials}</div>'

        st.markdown(
            f'<div class="user-card">{avatar_html}'
            f'<div><div class="user-name">{name}</div>'
            f'<div class="user-email">{email_s}</div></div></div>',
            unsafe_allow_html=True)

        badge = (f'<span class="badge-premium">â­ Premium</span>'
                 if tier == "premium"
                 else f'<span class="badge-free">ð Free Plan</span>')
        st.markdown(badge, unsafe_allow_html=True)
        st.markdown("")

    # ââ Navigation ââ
    free_pages = ["ð  Dashboard", "ð¥ Gold & Silver", "ð Global Markets", "ð° News Feed"]
    if is_logged_in():
        nav_pages = free_pages + ["ð¤ AI Briefing", "â­ Watchlist", "ð My Reports", "â¹ï¸ About"]
    else:
        nav_pages = free_pages + ["ð AI Briefing", "ð Watchlist", "â¹ï¸ About"]

    page = st.radio("Navigate", nav_pages, label_visibility="collapsed")

    st.markdown("---")
    st.markdown(f"**Last updated:** {datetime.now().strftime('%H:%M:%S')}")
    if st.button("ð Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    if is_logged_in():
        if st.button("ðª Sign Out", use_container_width=True):
            do_logout()
    else:
        if st.button("ð Sign In / Sign Up", type="primary", use_container_width=True):
            st.session_state["show_auth"] = True
            st.rerun()

    st.markdown("")
    st.caption("Data: Yahoo Finance Â· FRED Â· World Bank Â· NewsAPI")
    st.caption("AI: Claude Â· OpenAI Â· Gemini")

# ââ Redirect locked pages to auth ââââââââââââââââââ
if page in ["ð AI Briefing", "ð Watchlist"]:
    st.session_state["show_auth"] = True

# ââ Show auth page if requested ââââââââââââââââââââ
if st.session_state.get("show_auth") and not is_logged_in():
    show_auth_page()
    st.stop()


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PAGE: DASHBOARD
# âââââââââââââââââââââââââââââââââââââââââââââââââ
if page == "ð  Dashboard":
    st.title("ð Market Dashboard")
    st.caption(f"Real-time overview Â· {datetime.now().strftime('%A, %d %B %Y %H:%M')}")

    with st.spinner("Loading market dataâ¦"):
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

    st.markdown("### ð Key Indicators")
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

    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**ð US Markets**")
        for label, d in [("S&P 500", sp500), ("Brent Oil", oil)]:
            v = d.get("close"); p = d.get("change_pct") or 0
            c = "positive" if p >= 0 else "negative"
            prefix = "$" if "Oil" in label else ""
            st.markdown(f"{label}: `{prefix}{v:,.2f}` <span class='{c}'>{p:+.2f}%</span>"
                        if v else f"{label}: N/A", unsafe_allow_html=True)
    with col_b:
        st.markdown("**ð Asian Markets**")
        for label, d in [("BSE Sensex", sensex), ("Nifty 50", nifty)]:
            v = d.get("close"); p = d.get("change_pct") or 0
            c = "positive" if p >= 0 else "negative"
            st.markdown(f"{label}: `{v:,.0f}` <span class='{c}'>{p:+.2f}%</span>"
                        if v else f"{label}: N/A", unsafe_allow_html=True)
    with col_c:
        st.markdown("**ð° Precious Metals**")
        for label, d, prefix in [("Silver", silver, "$"), ("Gold", gold, "$")]:
            v = d.get("close"); p = d.get("change_pct") or 0
            c = "positive" if p >= 0 else "negative"
            st.markdown(f"{label}: `{prefix}{v:,.2f}/oz` <span class='{c}'>{p:+.2f}%</span>"
                        if v else f"{label}: N/A", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ð 30-Day Performance Comparison")
    with st.spinner("Loading chartâ¦"):
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


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PAGE: GOLD & SILVER
# âââââââââââââââââââââââââââââââââââââââââââââââââ
elif page == "ð¥ Gold & Silver":
    st.title("ð¥ Gold & Silver")
    st.caption("Precious metals â priced in USD and Sri Lankan Rupees")

    with st.spinner("Loading pricesâ¦"):
        gold   = current_price("GC=F")
        silver = current_price("SI=F")
        usd_lkr_data = current_price("LKR=X")

    usd_lkr_rate = usd_lkr_data.get("close") or 312

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

    st.caption("Gold (LKR) = Gold (USD/oz) Ã USD/LKR rate. LKR depreciation amplifies gold returns.")

    st.markdown("---")
    st.markdown("### 1-Month Price Chart")
    choice = st.selectbox("Choose metal", ["Gold (GC=F)", "Silver (SI=F)"])
    ticker = "GC=F" if "Gold" in choice else "SI=F"
    with st.spinner("Loading chartâ¦"):
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
    with st.spinner("Loading World Bank dataâ¦"):
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


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PAGE: GLOBAL MARKETS
# âââââââââââââââââââââââââââââââââââââââââââââââââ
elif page == "ð Global Markets":
    st.title("ð Global Markets")
    st.caption("US, Asian, and European indices â with Sri Lanka context")

    with st.spinner("Fetching indicesâ¦"):
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
    with st.spinner("Loading chartâ¦"):
        df = fetch_price(tmap.get(market_choice, "^GSPC"), "1mo")
        if df is not None and not df.empty:
            fig = go.Figure(go.Scatter(x=df.index, y=df["Close"], fill="tozeroy",
                                       line=dict(color="#3b82f6", width=2)))
            fig.update_layout(template="plotly_dark", height=350,
                              margin=dict(l=20, r=20, t=30, b=20),
                              paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### ð± Forex â Sri Lanka Relevant Pairs")
    with st.spinner("Loading forexâ¦"):
        forex = {"USD/LKR": current_price("LKR=X"),  "EUR/LKR": current_price("EURLKR=X"),
                 "GBP/LKR": current_price("GBPLKR=X"), "AED/LKR": current_price("AEDLKR=X"),
                 "JPY/LKR": current_price("JPYLKR=X"), "USD/EUR":  current_price("EURUSD=X")}
    fx_cols = st.columns(len(forex))
    for col, (pair, d) in zip(fx_cols, forex.items()):
        v = d.get("close"); p = d.get("change_pct")
        col.metric(pair, f"{v:,.4f}" if v else "N/A", f"{p:+.2f}%" if p is not None else None)


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PAGE: NEWS FEED
# âââââââââââââââââââââââââââââââââââââââââââââââââ
elif page == "ð° News Feed":
    st.title("ð° News Feed")
    st.caption("Latest financial news â categorised for Sri Lankan investors")

    categories = {
        "Sri Lanka":     "Sri Lanka",
        "Gold & Silver": "gold silver price precious metals",
        "US Economy":    "Federal Reserve inflation US economy",
        "Asian Markets": "India China Asian stock market",
        "Oil & Energy":  "oil price OPEC energy commodity",
        "Geopolitical":  "geopolitical risk war sanctions",
    }
    tabs = st.tabs(["ð´ Sri Lanka", "ð¥ Gold & Silver", "ðµ US Economy",
                    "ð Asian Markets", "â¡ Oil & Energy", "ð Geopolitical"])

    for tab, (cat_name, query) in zip(tabs, categories.items()):
        with tab:
            with st.spinner(f"Loading {cat_name} newsâ¦"):
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
                        st.caption(f"{source} Â· {pub_at}")
                        st.markdown("---")


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PAGE: AI BRIEFING  (Premium)
# âââââââââââââââââââââââââââââââââââââââââââââââââ
elif page == "ð¤ AI Briefing":
    if not is_logged_in():
        show_premium_gate("AI Market Briefing")
        st.stop()

    st.title("ð¤ AI Market Briefing")
    st.caption("Daily market analysis powered by Claude AI (with OpenAI and Gemini fallback)")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        gen_btn = st.button("â¨ Generate Today's Briefing", type="primary",
                            use_container_width=True)
    with col_info:
        if st.session_state.get("briefing"):
            st.success("Today's briefing is ready â scroll down to read it, or regenerate.")
        else:
            st.info("Click to generate today's AI market briefing (takes ~30â60 seconds).")

    with st.expander("AI Provider Status"):
        st.markdown(f"ð¢ **Claude (Primary):** {'Configured â' if ANTHROPIC_API_KEY else 'â Missing ANTHROPIC_API_KEY'}")
        st.markdown(f"ð¡ **OpenAI (Secondary):** {'Configured â' if OPENAI_API_KEY else 'â Missing OPENAI_API_KEY'}")
        st.markdown(f"ð  **Gemini (Fallback):** {'Configured â' if GEMINI_API_KEY else 'â Missing GEMINI_API_KEY'}")

    if gen_btn:
        with st.spinner("ð§  Fetching market data and generating briefingâ¦"):
            md = {k: current_price(t) for k, t in {
                "gold": "GC=F", "silver": "SI=F", "usd_lkr": "LKR=X",
                "sp500": "^GSPC", "vix": "^VIX", "oil": "BZ=F",
                "sensex": "^BSESN", "nifty": "^NSEI",
                "dxy": "DX-Y.NYB", "nasdaq": "^IXIC"}.items()}
            briefing_text, model_used = generate_briefing(md)

        if briefing_text and "failed" not in briefing_text.lower()[:50]:
            st.success(f"â Generated by **{model_used}**")
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
            if st.button("ð¾ Save to My Reports", use_container_width=True):
                if db_save_briefing(save_title, briefing_to_show, model_label, sent):
                    st.success("Saved!")
                else:
                    st.error("Save failed â make sure you're logged in.")


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PAGE: WATCHLIST  (Premium)
# âââââââââââââââââââââââââââââââââââââââââââââââââ
elif page == "â­ Watchlist":
    if not is_logged_in():
        show_premium_gate("Watchlist")
        st.stop()

    st.title("â­ My Watchlist")
    st.caption("Track your favourite tickers â CSE stocks, global indices, commodities")

    # ââ Add ticker ââ
    with st.expander("â Add Ticker", expanded=False):
        ac1, ac2, ac3, ac4 = st.columns([2, 2, 1.5, 1])
        with ac1: new_t = st.text_input("Ticker symbol", placeholder="JKH.N0000 or ^GSPC")
        with ac2: new_n = st.text_input("Display name",  placeholder="John Keells")
        with ac3: cat   = st.selectbox("Category", ["stock", "index", "commodity", "forex"])
        with ac4:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            if st.button("Add â", type="primary"):
                if new_t and new_n:
                    if db_add_watchlist(new_t.strip().upper(), new_n.strip(), cat):
                        st.success(f"â {new_t.upper()} added!")
                        st.rerun()
                else:
                    st.warning("Enter ticker and name.")

    # ââ Display ââ
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
                         f'{item.get("category","").upper()}</span>')

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1.5, 0.8])
            with c1:
                st.markdown(f"**{item['ticker_name']}** {cat_badge}",
                            unsafe_allow_html=True)
                st.caption(ticker)
            with c2:
                st.markdown(f"**{v:,.2f}**" if v else "â")
            with c3:
                if p is not None:
                    arrow = "â²" if p >= 0 else "â¼"
                    cls   = "positive" if p >= 0 else "negative"
                    st.markdown(f'<span class="{cls}">{arrow} {abs(p):.2f}%</span>',
                                unsafe_allow_html=True)
                else:
                    st.markdown("â")
            with c4:
                st.caption(item.get("added_at", "")[:10])
            with c5:
                if st.button("â", key=f"rm_{ticker}"):
                    db_remove_watchlist(ticker)
                    st.rerun()
            st.markdown("---")


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PAGE: MY REPORTS  (Premium)
# âââââââââââââââââââââââââââââââââââââââââââââââââ
elif page == "ð My Reports":
    if not is_logged_in():
        show_premium_gate("My Reports")
        st.stop()

    st.title("ð My Reports")
    st.caption("Saved AI briefings and personal investment notes")

    tab_b, tab_n = st.tabs(["ð¤ Saved Briefings", "ð My Notes"])

    # ââ SAVED BRIEFINGS ââ
    with tab_b:
        briefings = db_get_briefings()
        if not briefings:
            st.info("No saved briefings yet. Generate one on the AI Briefing page and tap 'Save'.")
        else:
            st.markdown(f"**{len(briefings)} briefings saved**")
            for b in briefings:
                sent  = b.get("sentiment", "")
                sent_badge = {"BULLISH": "ð¢", "BEARISH": "ð´", "NEUTRAL": "ð¡"}.get(sent, "âª")
                title = b.get("title", "Briefing")
                dt    = b.get("created_at", "")[:10]
                with st.expander(f"{sent_badge} {title} â {dt}"):
                    st.markdown(b.get("content", ""))
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.caption(f"Model: {b.get('model_used','?')} Â· Sentiment: {sent or 'N/A'}")
                    with c2:
                        if st.button("ð Delete", key=f"del_b_{b['id']}"):
                            db_delete_briefing(b["id"])
                            st.rerun()

    # ââ MY NOTES ââ
    with tab_n:
        # New note form
        with st.expander("âï¸ Write New Note", expanded=False):
            nc1, nc2 = st.columns([3, 1])
            with nc1: n_title = st.text_input("Note title", placeholder="My CSE Analysis")
            with nc2: n_pinned = st.checkbox("ð Pin")
            n_content = st.text_area("Content", height=140,
                                     placeholder="Your thoughts, analysis, remindersâ¦")
            n_tags = st.text_input("Tags (comma separated)",
                                   placeholder="CSE, gold, weekly-review")
            if st.button("ð¾ Save Note", type="primary"):
                if n_title and n_content:
                    tags = [t.strip() for t in n_tags.split(",") if t.strip()]
                    db_save_note(n_title, n_content, tags, n_pinned)
                    st.success("â Note saved!")
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
                pin_icon = "ð " if n.get("is_pinned") else ""
                tags_html = " ".join(
                    f'<span style="background:#1e2440;color:#7b8cde;'
                    f'padding:1px 8px;border-radius:4px;font-size:0.72rem">{t}</span>'
                    for t in (n.get("tags") or []))
                label = f"{pin_icon}{n.get('title','Note')} â {n.get('updated_at','')[:10]}"
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
                        if st.button("ð¾ Save", key=f"sv_{n['id']}"):
                            db_update_note(n["id"], content=edited)
                            st.success("Saved!")
                            st.rerun()
                    with ec3:
                        if st.button("ð Del", key=f"dn_{n['id']}"):
                            db_delete_note(n["id"])
                            st.rerun()


# âââââââââââââââââââââââââââââââââââââââââââââââââ
# PAGE: ABOUT
# âââââââââââââââââââââââââââââââââââââââââââââââââ
elif page == "â¹ï¸ About":
    st.title("â¹ï¸ About InvestSmart")
    st.markdown("""
## What is InvestSmart?

InvestSmart is an AI-powered investment intelligence platform built specifically for Sri Lankan investors.
It monitors global market factors that affect the Colombo Stock Exchange (CSE), gold, silver, and bonds â
and generates daily AI briefings to help you make better-informed investment decisions.

## Data Sources

| Source | What We Use It For |
|--------|--------------------|
| Yahoo Finance | 40+ tickers â gold, silver, CSE indices, forex, global markets |
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

- **Frontend:** Streamlit (Python)
- **Hosting:** Streamlit Community Cloud
- **Database & Auth:** Supabase (PostgreSQL + Auth)
- **Auth Methods:** Email/Password Â· Google OAuth Â· Phone SMS OTP

## Account Features (Free vs Premium)

| Feature | Free | Logged In |
|---------|------|-----------|
| Dashboard | â | â |
| Gold & Silver | â | â |
| Global Markets | â | â |
| News Feed | â | â |
| AI Briefing | â | â |
| Watchlist | â | â |
| My Reports & Notes | â | â |

## Disclaimer

InvestSmart is for **informational purposes only**. Nothing on this platform constitutes
investment advice. Always do your own research and consult a licensed financial advisor
before making investment decisions.

*Built for Sri Lankan investors Â· v2.0 â with Authentication*
""")
