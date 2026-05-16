# Race Condition Analysis — Task 2.1

**Date:** 2026-05-16  
**Status:** ✅ Already Properly Implemented

---

## Issue Summary

The `_CSE_WS_CACHE` global dictionary is accessed by:
1. **Writer:** `_cse_ws_worker()` thread (WebSocket callback)
2. **Readers:** Multiple Streamlit pages fetching prices

Without proper synchronization, this could cause:
- Dictionary corruption during concurrent read/write
- Lost updates (race condition)
- Iterator errors mid-iteration

---

## Current Implementation Status

### ✅ Lock Properly Declared

**Line 737:** 
```python
_CSE_WS_LOCK = _threading.Lock()
```

### ✅ Write Operations Protected

**Lines 775-779** (in `on_message` callback):
```python
with _CSE_WS_LOCK:
    for item in data:
        entry = dict(item)
        entry["ts"] = now
        _CSE_WS_CACHE[item["symbol"]] = entry
```

**Lines 783-785** (ASPI data update):
```python
with _CSE_WS_LOCK:
    _CSE_WS_ASPI.clear()
    _CSE_WS_ASPI.update(aspi_data)
```

### ✅ Read Operations Protected

**Lines 831-833** (check if cache has data):
```python
with _CSE_WS_LOCK:
    if _CSE_WS_CACHE:
        break
```

**Lines 837-838** (snapshot for iteration):
```python
with _CSE_WS_LOCK:
    snapshot = dict(_CSE_WS_CACHE)
```

**Lines 886-889** (ASPI data read):
```python
with _CSE_WS_LOCK:
    if _CSE_WS_ASPI:
        aspi = dict(_CSE_WS_ASPI)
        break
```

### ✅ Safe Iteration Pattern

**Lines 844-847** (iterate snapshot, not original):
```python
for sym, d in snapshot.items():
    if sym.startswith(base + "."):
        best = d
        break
```

The critical pattern: **Take a snapshot inside the lock, iterate outside the lock**. This prevents holding the lock during expensive I/O.

---

## Threat Model Verification

| Operation | Location | Protection | Safe? |
|-----------|----------|-----------|-------|
| **Dictionary write** | Line 779 | `with _CSE_WS_LOCK:` | ✅ YES |
| **Dictionary clear** | Line 784 | `with _CSE_WS_LOCK:` | ✅ YES |
| **Dictionary update** | Line 785 | `with _CSE_WS_LOCK:` | ✅ YES |
| **Cache check (if)** | Line 832 | `with _CSE_WS_LOCK:` | ✅ YES |
| **Cache snapshot** | Line 838 | `with _CSE_WS_LOCK:` | ✅ YES |
| **Snapshot iteration** | Lines 844-847 | No lock (safe - snapshot) | ✅ YES |
| **ASPI check** | Line 887 | `with _CSE_WS_LOCK:` | ✅ YES |
| **ASPI snapshot** | Line 888 | `with _CSE_WS_LOCK:` | ✅ YES |

---

## Best Practice Verification

✅ **Lock granularity:** Minimal - only held during dict access, not during iteration/processing  
✅ **Deadlock prevention:** No nested locks on same resource  
✅ **Copy-on-read pattern:** Snapshots created while locked, processed outside lock  
✅ **Exception safety:** Operations complete before lock release  
✅ **Error handling:** Exceptions in `on_message` don't leave lock in bad state

---

## Conclusion

**Status:** ✅ **NO CHANGES NEEDED**

The implementation is **thread-safe and follows best practices**. The lock is:
- ✅ Properly initialized as `_threading.Lock()`
- ✅ Held during all dictionary modifications
- ✅ Held during critical read checks
- ✅ Released before expensive operations
- ✅ Never nested (deadlock-safe)

**Verdict:** Task 2.1 is already complete. The race condition was properly prevented during development.

---

## Recommendation

**Document this in code comments** to make it clear for future maintainers. Add a comment above the lock declaration explaining the thread-safety pattern used.

