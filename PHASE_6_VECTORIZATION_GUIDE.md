# Phase 6.5: Vectorization Optimization Guide
**Objective:** Replace 111 for loops with NumPy/Pandas vectorized operations  
**Expected Improvement:** 70-90% faster portfolio calculations

---

## Why Vectorization Matters

### ❌ SLOW: For Loop (1000 items)
```python
total_value = 0
for holding in portfolio:
    total_value += holding['shares'] * holding['price']
# Time: ~50ms for 1000 items
```

### ✅ FAST: Vectorized (1000 items)
```python
import pandas as pd
df = pd.DataFrame(portfolio)
total_value = (df['shares'] * df['price']).sum()
# Time: ~1ms for 1000 items - 50x faster!
```

---

## Common Patterns in app.py (111 for loops)

### Pattern 1: Aggregating Values
**Problem:**
```python
total_gain_loss = 0
for position in positions:
    total_gain_loss += position['current_value'] - position['cost_basis']
```

**Solution:**
```python
df = pd.DataFrame(positions)
total_gain_loss = (df['current_value'] - df['cost_basis']).sum()
```

### Pattern 2: Filtering Data
**Problem:**
```python
growth_stocks = []
for stock in all_stocks:
    if stock['pe_ratio'] < 20:
        growth_stocks.append(stock)
```

**Solution:**
```python
df = pd.DataFrame(all_stocks)
growth_stocks = df[df['pe_ratio'] < 20].to_dict('records')
```

### Pattern 3: Calculating Percentages
**Problem:**
```python
percentages = []
for value in values:
    pct = (value / sum(values)) * 100
    percentages.append(pct)
```

**Solution:**
```python
import numpy as np
percentages = (np.array(values) / np.sum(values)) * 100
```

### Pattern 4: Finding Max/Min
**Problem:**
```python
highest_price = 0
for stock in stocks:
    if stock['price'] > highest_price:
        highest_price = stock['price']
```

**Solution:**
```python
df = pd.DataFrame(stocks)
highest_price = df['price'].max()
```

### Pattern 5: Complex Calculations
**Problem:**
```python
returns = []
for year in historical_data:
    annual_return = ((year['end_value'] - year['start_value']) / year['start_value']) * 100
    returns.append(annual_return)
```

**Solution:**
```python
df = pd.DataFrame(historical_data)
returns = ((df['end_value'] - df['start_value']) / df['start_value']) * 100
```

---

## Portfolio Calculation Optimizations

### Current Loop-Based Calculation
```python
def calculate_portfolio(holdings):
    total_cost = 0
    total_value = 0
    gains_losses = []
    
    for holding in holdings:  # ❌ LOOP 1
        cost = holding['shares'] * holding['cost_per_share']
        value = holding['shares'] * holding['current_price']
        gain_loss = value - cost
        
        total_cost += cost  # ❌ LOOP 2
        total_value += value  # ❌ LOOP 3
        gains_losses.append(gain_loss)  # ❌ LOOP 4
        
    return {
        'total_cost': total_cost,
        'total_value': total_value,
        'gains_losses': gains_losses,
        'total_gain_loss': total_value - total_cost,
        'return_pct': ((total_value - total_cost) / total_cost) * 100
    }
```

### Optimized Vectorized Calculation
```python
def calculate_portfolio_vectorized(holdings_df):
    """Vectorized portfolio calculation - 10-50x faster"""
    
    # Calculate all metrics at once using Pandas vectorization
    holdings_df['cost'] = holdings_df['shares'] * holdings_df['cost_per_share']
    holdings_df['current_value'] = holdings_df['shares'] * holdings_df['current_price']
    holdings_df['gain_loss'] = holdings_df['current_value'] - holdings_df['cost']
    
    # Aggregate using Pandas built-in functions (vectorized)
    total_cost = holdings_df['cost'].sum()
    total_value = holdings_df['current_value'].sum()
    total_gain_loss = holdings_df['gain_loss'].sum()
    return_pct = (total_gain_loss / total_cost) * 100
    
    return {
        'total_cost': total_cost,
        'total_value': total_value,
        'gains_losses': holdings_df['gain_loss'].tolist(),
        'total_gain_loss': total_gain_loss,
        'return_pct': return_pct
    }
```

**Performance:** 1000 holdings  
- Loop-based: ~50-100ms  
- Vectorized: ~1-3ms  
- **Improvement: 30-50x faster**

---

## Sector Analysis Optimization

### Current Loop
```python
sector_data = []
for sector in sectors:
    sector_sum = 0
    for holding in holdings:
        if holding['sector'] == sector:
            sector_sum += holding['value']
    sector_data.append({
        'sector': sector,
        'value': sector_sum,
        'pct': (sector_sum / total_value) * 100
    })
```

### Optimized Vectorized
```python
# Groupby is highly optimized vectorized operation
sector_data = holdings_df.groupby('sector')['value'].sum()
sector_data = sector_data / total_value * 100  # Vectorized percentage
sector_data = sector_data.reset_index(name='pct').to_dict('records')
```

**Improvement:** 5-10x faster with 100+ holdings

---

## Implementation Checklist

### Vectorization Opportunities:

- [ ] **Portfolio calculation functions** (HIGH PRIORITY - biggest impact)
  - [ ] Cost basis calculations
  - [ ] Gain/loss calculations
  - [ ] Return percentage calculations
  
- [ ] **Sector analysis** (HIGH PRIORITY)
  - [ ] Sector aggregations
  - [ ] Sector percentages
  - [ ] Sector comparisons
  
- [ ] **Market data processing** (MEDIUM PRIORITY)
  - [ ] Price calculations
  - [ ] Moving averages
  - [ ] Price change calculations
  
- [ ] **Data filtering** (MEDIUM PRIORITY)
  - [ ] Filter by criteria
  - [ ] Sort operations
  - [ ] Search functions
  
- [ ] **Reporting** (MEDIUM PRIORITY)
  - [ ] Summary calculations
  - [ ] Statistical measures
  - [ ] Performance metrics

---

## Before/After Code Templates

### Template 1: Summing Values
```python
# ❌ BEFORE
total = 0
for item in items:
    total += item['value']

# ✅ AFTER
import pandas as pd
df = pd.DataFrame(items)
total = df['value'].sum()
```

### Template 2: Conditional Filtering
```python
# ❌ BEFORE
filtered = []
for item in items:
    if item['price'] > 100:
        filtered.append(item)

# ✅ AFTER
df = pd.DataFrame(items)
filtered = df[df['price'] > 100].to_dict('records')
```

### Template 3: Transforming Values
```python
# ❌ BEFORE
doubled = []
for item in items:
    doubled.append(item['value'] * 2)

# ✅ AFTER
import numpy as np
doubled = np.array([item['value'] for item in items]) * 2
```

### Template 4: Complex Calculations
```python
# ❌ BEFORE (3 loops!)
results = []
for item in items:
    base = item['a'] * item['b']
    adjusted = base + (item['c'] / item['d'])
    results.append(adjusted)

# ✅ AFTER (1 vectorized operation!)
df = pd.DataFrame(items)
results = df['a'] * df['b'] + (df['c'] / df['d'])
```

---

## Performance Impact

### Typical Improvements

| Operation | Items | Loop Time | Vectorized | Speedup |
|-----------|-------|-----------|-----------|---------|
| Portfolio calc | 100 | 10ms | 0.5ms | 20x |
| Portfolio calc | 1000 | 100ms | 3ms | 33x |
| Sector analysis | 50 | 20ms | 1ms | 20x |
| Price filtering | 500 | 15ms | 1ms | 15x |
| Return calculations | 1000 | 80ms | 2ms | 40x |

**Total App Speedup:** 10-30x for computation-heavy operations

---

## Integration with Phase 6 Plan

1. **Phase 6.1:** Profile (✅ DONE) - Identified 111 loops
2. **Phase 6.2:** Caching (→ NEXT) - Reduce API calls
3. **Phase 6.5:** Vectorization (→ HIGHEST IMPACT) - Speed up calculations
4. **Phase 6.3:** Database optimization - Reduce queries
5. **Phase 6.4:** Frontend optimization - Improve UI rendering
6. **Phase 6.6:** Memory optimization - Reduce memory usage
7. **Phase 6.7:** Testing & verification - Confirm targets met

---

## Status

**Ready to implement vectorization improvements**

Expected timeline for complete vectorization: 2-3 hours
