-- ============================================================
-- InvestSmart CSE Integration — Supabase Migration
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================================

-- 1. Add tier + is_paid to profiles table (if not already present)
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS tier TEXT NOT NULL DEFAULT 'free';
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_paid BOOLEAN NOT NULL DEFAULT false;

-- Keep them in sync via trigger
CREATE OR REPLACE FUNCTION sync_tier_is_paid()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.tier = 'premium' THEN
    NEW.is_paid := true;
  ELSE
    NEW.is_paid := false;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_tier_is_paid ON profiles;
CREATE TRIGGER trg_sync_tier_is_paid
  BEFORE INSERT OR UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION sync_tier_is_paid();

-- 2. CSE stocks master table
CREATE TABLE IF NOT EXISTS cse_stocks (
    symbol        TEXT PRIMARY KEY,
    company_name  TEXT NOT NULL,
    sector        TEXT,
    isin          TEXT,
    listing_date  DATE,
    market_cap    NUMERIC,
    description   TEXT,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. CSE price history (records every price fetch)
CREATE TABLE IF NOT EXISTS cse_price_history (
    id           BIGSERIAL PRIMARY KEY,
    symbol       TEXT NOT NULL,
    price_date   DATE NOT NULL,
    open_price   NUMERIC,
    high_price   NUMERIC,
    low_price    NUMERIC,
    close_price  NUMERIC NOT NULL,
    volume       BIGINT  NOT NULL DEFAULT 0,
    trade_count  INTEGER NOT NULL DEFAULT 0,
    source       TEXT    NOT NULL DEFAULT 'yahoo',
    recorded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT cse_price_history_uq UNIQUE (symbol, price_date)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_cse_hist_symbol      ON cse_price_history(symbol);
CREATE INDEX IF NOT EXISTS idx_cse_hist_date        ON cse_price_history(price_date DESC);
CREATE INDEX IF NOT EXISTS idx_cse_hist_symbol_date ON cse_price_history(symbol, price_date DESC);

-- 4. Row Level Security
ALTER TABLE cse_stocks        ENABLE ROW LEVEL SECURITY;
ALTER TABLE cse_price_history ENABLE ROW LEVEL SECURITY;

-- Anyone (including anonymous) can read CSE market data
DROP POLICY IF EXISTS "Public read cse_stocks"   ON cse_stocks;
DROP POLICY IF EXISTS "Public read cse_history"  ON cse_price_history;

CREATE POLICY "Public read cse_stocks"
    ON cse_stocks FOR SELECT USING (true);

CREATE POLICY "Public read cse_history"
    ON cse_price_history FOR SELECT USING (true);

-- Authenticated users can insert/update price records (app writes with anon key)
DROP POLICY IF EXISTS "Auth write cse_history" ON cse_price_history;
CREATE POLICY "Auth write cse_history"
    ON cse_price_history FOR INSERT
    WITH CHECK (auth.role() IN ('authenticated', 'service_role', 'anon'));

DROP POLICY IF EXISTS "Auth upsert cse_history" ON cse_price_history;
CREATE POLICY "Auth upsert cse_history"
    ON cse_price_history FOR UPDATE
    USING (auth.role() IN ('authenticated', 'service_role', 'anon'));

-- 5. Seed CSE stocks master data
INSERT INTO cse_stocks (symbol, company_name, sector) VALUES
-- Banking & Finance
('COMB.LK', 'Commercial Bank of Ceylon PLC',      'Banking'),
('HNB.LK',  'Hatton National Bank PLC',           'Banking'),
('SAMP.LK', 'Sampath Bank PLC',                   'Banking'),
('NDB.LK',  'NDB Bank PLC',                       'Banking'),
('DFCC.LK', 'DFCC Bank PLC',                      'Banking'),
('PABC.LK', 'Pan Asia Banking Corporation PLC',   'Banking'),
('UNION.LK','Union Bank of Colombo PLC',          'Banking'),
('LOLC.LK', 'LOLC Holdings PLC',                  'Finance'),
('CFIN.LK', 'Central Finance Company PLC',        'Finance'),
('LLUB.LK', 'Lanka ORIX Leasing Company PLC',     'Finance'),
('LOFC.LK', 'LOLC Finance PLC',                   'Finance'),
-- Diversified Holdings
('JKH.LK',  'John Keells Holdings PLC',           'Diversified'),
('CARG.LK', 'Cargills (Ceylon) PLC',              'Diversified'),
('HPWR.LK', 'Hemas Holdings PLC',                 'Diversified'),
-- Telecom
('DIAL.LK', 'Dialog Axiata PLC',                  'Telecom'),
('SLTL.LK', 'Sri Lanka Telecom PLC',              'Telecom'),
-- Manufacturing
('CTC.LK',  'Ceylon Tobacco Company PLC',         'Manufacturing'),
('DIPD.LK', 'Dipped Products PLC',                'Manufacturing'),
('REXP.LK', 'Richard Pieris Exports PLC',         'Manufacturing'),
('TJL.LK',  'Textured Jersey Lanka PLC',          'Manufacturing'),
('ACL.LK',  'ACL Cables PLC',                     'Manufacturing'),
('SELI.LK', 'Sierra Cables PLC',                  'Manufacturing'),
('LALU.LK', 'Lanka Aluminium Industries PLC',     'Manufacturing'),
-- Plantation
('AGAL.LK', 'Agalawatte Plantations PLC',         'Plantation'),
('MAST.LK', 'Maskeliya Plantations PLC',          'Plantation'),
('BUKI.LK', 'Bukit Darah PLC',                    'Plantation'),
('ELPL.LK', 'Elpitiya Plantations PLC',           'Plantation'),
('KZOO.LK', 'Kotagala Plantations PLC',           'Plantation'),
('NAMU.LK', 'Namunukula Plantations PLC',         'Plantation'),
-- Hotels & Leisure
('AHPL.LK', 'Asian Hotels and Properties PLC',    'Hotels'),
('BERU.LK', 'Beruwala Resorts PLC',               'Hotels'),
('AMSL.LK', 'Aitken Spence Hotel Holdings PLC',   'Hotels'),
-- Healthcare
('ASIR.LK', 'Asiri Hospital Holdings PLC',        'Healthcare'),
('NHSL.LK', 'Nawaloka Hospitals PLC',             'Healthcare'),
-- Energy
('LIOC.LK', 'Lanka IOC PLC',                      'Energy')
ON CONFLICT (symbol) DO UPDATE
  SET company_name = EXCLUDED.company_name,
      sector       = EXCLUDED.sector,
      updated_at   = NOW();

-- 6. Upgrade a user to premium (run manually per user)
-- UPDATE profiles SET tier = 'premium' WHERE id = '<supabase-user-uuid>';

-- Done!
SELECT 'CSE migration complete' AS status;
