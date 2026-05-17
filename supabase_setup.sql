-- ============================================================
-- InvestSmart — Supabase Database Setup
-- ============================================================
-- HOW TO USE:
-- 1. Go to https://supabase.com → Your Project → SQL Editor
-- 2. Paste this entire file and click "Run"
-- 3. All 7 tables will be created automatically
-- ============================================================

-- ── Table 1: Daily Prices (OHLCV for all 40+ tickers) ───────
CREATE TABLE IF NOT EXISTS daily_prices (
    id            BIGSERIAL PRIMARY KEY,
    date          DATE NOT NULL,
    ticker_name   TEXT NOT NULL,
    ticker_symbol TEXT,
    open          NUMERIC,
    high          NUMERIC,
    low           NUMERIC,
    close         NUMERIC NOT NULL,
    volume        BIGINT,
    change_pct    NUMERIC,
    collected_at  TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (date, ticker_name)
);

CREATE INDEX IF NOT EXISTS idx_daily_prices_date   ON daily_prices(date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_prices_ticker ON daily_prices(ticker_name);


-- ── Table 2: Macro Data (FRED + World Bank indicators) ──────
CREATE TABLE IF NOT EXISTS macro_data (
    id           BIGSERIAL PRIMARY KEY,
    date         DATE NOT NULL,
    source       TEXT NOT NULL,       -- 'FRED' or 'WorldBank'
    series_name  TEXT NOT NULL,
    series_id    TEXT,
    value        NUMERIC,
    collected_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (date, series_name)
);

CREATE INDEX IF NOT EXISTS idx_macro_date   ON macro_data(date DESC);
CREATE INDEX IF NOT EXISTS idx_macro_series ON macro_data(series_name);


-- ── Table 3: News Articles ───────────────────────────────────
CREATE TABLE IF NOT EXISTS news_items (
    id           BIGSERIAL PRIMARY KEY,
    date         DATE NOT NULL,
    category     TEXT,
    title        TEXT NOT NULL,
    url          TEXT UNIQUE NOT NULL,
    source_name  TEXT,
    description  TEXT,
    published_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_date     ON news_items(date DESC);
CREATE INDEX IF NOT EXISTS idx_news_category ON news_items(category);


-- ── Table 4: Daily AI Briefings ──────────────────────────────
CREATE TABLE IF NOT EXISTS daily_briefings (
    id            BIGSERIAL PRIMARY KEY,
    date          DATE UNIQUE NOT NULL,
    briefing_text TEXT NOT NULL,
    data_summary  TEXT,
    model_used    TEXT,               -- 'claude-sonnet-4-6', 'gpt-4o', or 'gemini-1.5-flash'
    generated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_briefings_date ON daily_briefings(date DESC);


-- ── Table 5: Behaviour Predictions (geopolitical events) ────
CREATE TABLE IF NOT EXISTS behaviour_predictions (
    id          BIGSERIAL PRIMARY KEY,
    date        DATE NOT NULL,
    event       TEXT NOT NULL,
    prediction  TEXT NOT NULL,
    event_url   TEXT,
    model_used  TEXT,
    outcome     TEXT DEFAULT 'pending', -- updated later when actual outcome is known
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_date ON behaviour_predictions(date DESC);


-- ── Table 6: User Profiles (for SaaS multi-user) ────────────
CREATE TABLE IF NOT EXISTS user_profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email           TEXT,
    full_name       TEXT,
    subscription    TEXT DEFAULT 'free',    -- 'free', 'pro', 'enterprise'
    risk_tolerance  TEXT DEFAULT 'moderate',-- 'conservative', 'moderate', 'aggressive'
    portfolio_focus TEXT[],                  -- e.g. ['gold', 'cse', 'bonds']
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);


-- ── Table 7: User Financial Data (twice-weekly collection) ──
CREATE TABLE IF NOT EXISTS user_financial_data (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    date            DATE NOT NULL,
    asset_type      TEXT,                    -- 'stock', 'gold', 'bond', 'cash'
    asset_name      TEXT,
    quantity        NUMERIC,
    purchase_price  NUMERIC,
    current_value   NUMERIC,
    currency        TEXT DEFAULT 'LKR',
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (user_id, date, asset_name)
);

CREATE INDEX IF NOT EXISTS idx_user_financial_user ON user_financial_data(user_id);
CREATE INDEX IF NOT EXISTS idx_user_financial_date ON user_financial_data(date DESC);


-- ── Row Level Security (RLS) — isolates each user's data ────
-- Users can only see their OWN data, not other users' data.

ALTER TABLE user_profiles       ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_financial_data ENABLE ROW LEVEL SECURITY;

-- user_profiles: each user sees only their own profile
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id);

-- user_financial_data: each user sees only their own data
CREATE POLICY "Users can view own financial data"
    ON user_financial_data FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own financial data"
    ON user_financial_data FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own financial data"
    ON user_financial_data FOR UPDATE
    USING (auth.uid() = user_id);

-- Public tables (daily_prices, macro_data, news_items, daily_briefings)
-- are readable by all authenticated users (no RLS needed for read)
-- but only the service role (GitHub Actions) can write to them.

-- Done! All tables created successfully.
SELECT 'InvestSmart database setup complete! 7 tables created.' AS status;
