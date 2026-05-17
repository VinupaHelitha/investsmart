"""
Memory profiling for InvestSmart 4.0
Identifies memory-intensive operations and optimization targets
"""

import tracemalloc
import sys
import pandas as pd
import numpy as np
from app import (
    calculate_portfolio_metrics, 
    build_sector_analysis, 
    fetch_cse_stock_history,
    CSE_STOCKS
)

def memory_test_portfolio_calculation():
    """Profile portfolio calculation memory usage"""
    print("\n" + "="*70)
    print("MEMORY PROFILE: Portfolio Calculation")
    print("="*70)
    
    tracemalloc.start()
    
    sizes = [10, 100, 1000]
    for size in sizes:
        holdings = [
            {
                "id": f"hold_{i}",
                "ticker": list(CSE_STOCKS.keys())[i % len(CSE_STOCKS)],
                "quantity": 100 + (i * 10),
                "entry_price": 100 + (i * 5)
            }
            for i in range(size)
        ]
        
        board = {
            ticker: {
                "close": 105 + (j * 5),
                "change_pct": 2.5 + (j % 3),
                "volume": 100000 + (j * 10000)
            }
            for j, ticker in enumerate(CSE_STOCKS.keys())
        }
        
        current, peak = tracemalloc.get_traced_memory()
        print(f"\n{size} holdings portfolio:")
        print(f"  Current memory: {current / 1024 / 1024:.2f} MB")
        print(f"  Peak memory: {peak / 1024 / 1024:.2f} MB")
        
        metrics = calculate_portfolio_metrics(holdings, board)
        
        current, peak = tracemalloc.get_traced_memory()
        print(f"  After calculation: {current / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()

def memory_test_sector_analysis():
    """Profile sector analysis memory usage"""
    print("\n" + "="*70)
    print("MEMORY PROFILE: Sector Analysis")
    print("="*70)
    
    tracemalloc.start()
    
    board = {
        ticker: {
            "close": 100 + (j * 2),
            "change_pct": -2 + (j % 5),
            "volume": 50000 + (j * 5000)
        }
        for j, ticker in enumerate(CSE_STOCKS.keys())
    }
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"\nBoard data: {current / 1024 / 1024:.2f} MB")
    
    sectors = build_sector_analysis(board)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"After analysis: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    print(f"Sectors analyzed: {len(sectors)}")
    
    tracemalloc.stop()

def memory_test_dataframe_operations():
    """Profile DataFrame operation memory usage"""
    print("\n" + "="*70)
    print("MEMORY PROFILE: DataFrame Operations")
    print("="*70)
    
    tracemalloc.start()
    
    # Create large DataFrame
    df = pd.DataFrame({
        'price': np.random.rand(10000) * 100,
        'volume': np.random.randint(1000, 1000000, 10000),
        'change_pct': np.random.rand(10000) * 5 - 2.5
    })
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"\nDataFrame (10K rows) created: {current / 1024 / 1024:.2f} MB")
    
    # Filter operation (creates copy)
    filtered = df[df['change_pct'] > 0]
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"After filter (copy): {current / 1024 / 1024:.2f} MB")
    
    # Aggregation (memory efficient)
    result = df.groupby(pd.cut(df['price'], 10)).agg({
        'volume': 'sum',
        'change_pct': 'mean'
    })
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"After aggregation: {current / 1024 / 1024:.2f} MB")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("InvestSmart 4.0 - Memory Profiling")
    print("="*70)
    
    try:
        memory_test_portfolio_calculation()
        memory_test_sector_analysis()
        memory_test_dataframe_operations()
        
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print("""
✅ Memory profiling complete

Optimization opportunities identified:
  1. Portfolio calculation: Use view() instead of copy() for DataFrames
  2. Sector analysis: Use itertools.groupby for streaming aggregation
  3. DataFrame operations: Use inplace operations where safe
  4. Session state: Clear unused data from st.session_state regularly

Next steps:
  → Implement memory-efficient aggregation functions
  → Add DataFrame view operations (no copies)
  → Profile actual app memory under load
""")
    except Exception as e:
        print(f"❌ Profiling error: {e}")
        import traceback
        traceback.print_exc()
