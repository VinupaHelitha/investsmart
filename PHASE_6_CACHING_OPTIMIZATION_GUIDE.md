# Phase 6.2: Caching Optimization Guide
**Objective:** Reduce API calls and improve data fetch performance  
**Target:** 50-70% reduction in redundant API calls  
**Baseline:** Currently 4 direct `requests.get()` calls, 8 cache decorators

---

## Current Caching Analysis

### ✅ What's Already Cached (8 decorators)
- Dashboard data
- CSE ticker lists
- Historical price data
- Global market indices
- User portfolio data
- AI briefing results
- News feed data
- Economic indicators

### ⚠️ What Needs Review
- **Cache Duration:** Verify each is appropriate (short-lived vs stable data)
- **Cache Invalidation:** Ensure cache clears when data should refresh
- **Duplicate Requests:** Check for redundant API calls in same session
- **Streaming Data:** Real-time data (CSE WebSocket) shouldn't be cached

---

## Caching Strategy by Data Type

### 1. Real-Time Data (< 1 minute cache)
**Examples:** CSE live prices, USD/LKR exchange rate, Gold/Silver spot prices
```python
@st.cache_data(ttl=30)  # Refresh every 30 seconds
def fetch_cse_live_data():
    # WebSocket or live API call
    pass
```

### 2. Frequently-Updated Data (5-15 minute cache)
**Examples:** Daily market summaries, sector trends, portfolio values
```python
@st.cache_data(ttl=600)  # 10 minute refresh
def fetch_daily_summary():
    pass
```

### 3. Stable Historical Data (1-24 hour cache)
**Examples:** Historical prices, analyst reports, company fundamentals
```python
@st.cache_data(ttl=86400)  # 24 hour refresh
def fetch_historical_prices(ticker):
    pass
```

### 4. Reference Data (Never expires or weekly)
**Examples:** CSE ticker list, company details, country info
```python
@st.cache_data(ttl=604800)  # Weekly refresh
def fetch_ticker_list():
    pass
```

---

## Optimization Actions

### Action 1: Add Smart Cache Invalidation
**Problem:** Cache might serve stale data  
**Solution:** Add user-triggered refresh buttons

```python
st.sidebar.button("🔄 Refresh Data")  # Users can force refresh
```

### Action 2: Batch Multiple API Calls
**Problem:** 4 direct API calls happen separately  
**Solution:** Combine where possible

```python
# ❌ BEFORE: 4 separate calls
stocks = fetch_stocks()
gold = fetch_gold()
currencies = fetch_currencies()
news = fetch_news()

# ✅ AFTER: 1 combined call with batching
market_data = fetch_all_market_data()  # Returns {stocks, gold, currencies, news}
```

### Action 3: Implement Request Deduplication
**Problem:** Same data might be requested multiple times per session  
**Solution:** Use Python dictionaries to cache within session

```python
@st.cache_data(ttl=300)  # 5 min cache
def fetch_stock_price(ticker):
    # If called twice with same ticker in 5 mins, uses cached value
    return requests.get(f"https://api.example.com/price/{ticker}").json()
```

### Action 4: Add Lazy Loading
**Problem:** All data loads upfront  
**Solution:** Load only when user views section

```python
# ✅ Lazy load tabs
with st.tabs(["Markets", "Portfolio", "Analysis"]):
    with st.tab("Markets"):
        st.write(fetch_markets())  # Only loads when user clicks tab
    with st.tab("Portfolio"):
        st.write(fetch_portfolio())  # Only loads when user clicks tab
    with st.tab("Analysis"):
        st.write(fetch_analysis())  # Only loads when user clicks tab
```

### Action 5: Monitor Cache Hit Rates
**Problem:** Don't know if caching is effective  
**Solution:** Add telemetry

```python
@st.cache_data(ttl=600)
def fetch_data_with_tracking(endpoint):
    # Track cache hits vs misses
    if 'cache_hits' not in st.session_state:
        st.session_state.cache_hits = 0
    st.session_state.cache_hits += 1
    
    return requests.get(endpoint).json()
```

---

## Implementation Checklist

### Phase 6.2 Checklist:

- [ ] **Review existing cache decorators** - Check each for appropriate TTL
- [ ] **Add batch API calls** - Combine the 4 direct requests.get() calls
- [ ] **Implement request deduplication** - Prevent redundant calls in same session
- [ ] **Add lazy loading** - Use st.tabs for non-critical sections
- [ ] **Add cache invalidation buttons** - Users can force refresh
- [ ] **Measure improvement** - Compare API call count before/after
- [ ] **Document cache strategy** - Update code comments with TTLs

---

## Expected Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| API calls per session | ~50 | ~15 | 70% reduction |
| Data fetch time | 5-8s | 1-2s | 60-75% faster |
| User experience | Wait for data | Instant (cached) | Immediate response |

---

## Code Changes Required

### In app.py:

**1. Extend cache TTLs** (lines ~200-250)
```python
# Review and update existing decorators
@st.cache_data(ttl=86400)  # Increase from 3600 to 86400 for stable data
def fetch_cse_tickers():
    pass
```

**2. Batch API calls** (lines ~400-450)
```python
# Combine multiple requests
def fetch_all_market_data():
    return {
        'stocks': fetch_stocks(),
        'gold': fetch_gold(),
        'currencies': fetch_currencies()
    }
```

**3. Add refresh buttons** (sidebar)
```python
st.sidebar.button("🔄 Refresh All Data", help="Force reload market data")
```

---

## Performance Impact

**Estimated Time Savings Per User Session:**
- Dashboard load: 5s → 2s (60% faster)
- Data fetch: 8s → 2s (75% faster)
- Portfolio calculations: 500ms → 200ms (60% faster)

**Server Load Reduction:**
- API calls reduced by 70%
- Database queries reduced by 40%
- Network bandwidth reduced by 65%

---

## Status

**Task 6.2 Ready to Execute**

Next: Execute caching optimizations in app.py
