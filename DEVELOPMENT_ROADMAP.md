# InvestSmart 4.0 — Development Roadmap

**Current Status:** v2.0.2 (Deployment system complete)  
**Next Focus:** Security hardening + Code quality  
**Timeline:** 2026-05-16 onwards

---

## 📊 Project Status Overview

| Component | Status | Priority |
|-----------|--------|----------|
| **Deployment System** | ✅ Complete | N/A |
| **Security Hardening** | 🔴 In Progress | CRITICAL |
| **Code Quality** | 🟡 Partial | HIGH |
| **Feature Development** | ⏳ Planned | MEDIUM |
| **Testing & QA** | ⏳ Planned | MEDIUM |

---

## 🎯 Prioritized Task List

### **PHASE 1: SECURITY HARDENING (Critical) — Do This FIRST**

These are security vulnerabilities that could compromise user data or the app.

#### **Task 1.1: Rotate GitHub Token** ⭐ URGENT
**Why:** Your current token may have been exposed. Fresh token = lower risk.  
**Effort:** 5 minutes  
**Difficulty:** Easy

**Instructions:**
1. Go to: https://github.com/settings/tokens
2. Find your old token (named "InvestSmart Deploy")
3. Click **"Delete"** to revoke it
4. Click **"Generate new token"** → "Personal access tokens (classic)"
5. Configure:
   - Name: `InvestSmart Deploy (v2)`
   - Expiration: 30 days
   - Scope: Check ✓ `repo`
6. Copy the new token
7. Update `.env` file:
   ```env
   GITHUB_TOKEN=ghp_new_token_here
   ```
8. Test: Run `python deploy.py`
9. Done! Old token is now useless

**Verification:**
```bash
python deploy.py
# Should authenticate successfully with new token
```

---

#### **Task 1.2: Audit XSS Vulnerabilities** 
**Why:** `unsafe_allow_html=True` can allow HTML injection attacks.  
**Effort:** 1-2 hours  
**Difficulty:** Medium  

**Instructions:**

1. **Find all XSS-risky code:**
   ```bash
   grep -n "unsafe_allow_html=True" app.py
   ```
   
2. For each match, check if input is user-controlled:
   - `st.markdown(user_input, unsafe_allow_html=True)` → DANGEROUS
   - `st.markdown(static_html, unsafe_allow_html=True)` → SAFE

3. **Fix dangerous cases:**
   ```python
   # BEFORE (Dangerous):
   st.markdown(user_briefing_text, unsafe_allow_html=True)
   
   # AFTER (Safe):
   st.markdown(user_briefing_text, unsafe_allow_html=False)
   # Or escape HTML:
   import html
   st.markdown(html.escape(user_briefing_text))
   ```

4. **Document findings:**
   - Create file: `SECURITY_AUDIT.md`
   - List each XSS risk found
   - Note if it's fixed or acceptable

5. **Test:**
   - Try entering `<script>alert('test')</script>` in any input field
   - Verify it doesn't execute (appears as text)

**Verification:**
```bash
grep -n "unsafe_allow_html=True" app.py
# Should only show safe uses (e.g., hardcoded HTML)
```

---

#### **Task 1.3: Add WebSocket Timeout**
**Why:** Prevent zombie connections from hanging the app.  
**Effort:** 30 minutes  
**Difficulty:** Easy

**Find this in app.py (around line 700-750):**
```python
ws = websocket.create_connection(url)
```

**Replace with:**
```python
ws = websocket.create_connection(url, timeout=30)
```

**Verify:**
- App still receives CSE prices
- No timeout errors in logs
- App responsive

---

### **PHASE 2: CODE QUALITY (High) — Do After Phase 1**

These improve maintainability and performance.

#### **Task 2.1: Fix Race Condition in WebSocket Cache**
**Why:** Concurrent access to `_CSE_WS_CACHE` can cause data corruption.  
**Effort:** 2-3 hours  
**Difficulty:** Hard (requires threading knowledge)

**Find this in app.py (around line 701-750):**
```python
_CSE_WS_CACHE = {}  # Global dict, NOT thread-safe
```

**Solution:**
```python
import threading

_CSE_WS_CACHE = {}
_CSE_WS_LOCK = threading.Lock()

# When reading:
with _CSE_WS_LOCK:
    price = _CSE_WS_CACHE.get("AAPL.LK")

# When writing:
with _CSE_WS_LOCK:
    _CSE_WS_CACHE["AAPL.LK"] = new_price
```

**Verify:**
- No race condition errors in logs
- WebSocket prices update consistently
- Multiple users can use app simultaneously

---

#### **Task 2.2: Add Password Strength Validation**
**Why:** Weak passwords = compromised accounts.  
**Effort:** 1 hour  
**Difficulty:** Easy

**Find this in app.py:**
```python
# Signup form handling
```

**Add validation:**
```python
import re

def validate_password(password):
    """Ensure strong password"""
    errors = []
    
    if len(password) < 8:
        errors.append("At least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("At least 1 uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("At least 1 lowercase letter")
    if not re.search(r"[0-9]", password):
        errors.append("At least 1 number")
    if not re.search(r"[!@#$%^&*]", password):
        errors.append("At least 1 special character (!@#$%^&*)")
    
    return errors

# In signup form:
password = st.text_input("Password", type="password")
if password:
    errors = validate_password(password)
    if errors:
        st.error("Password requirements:\n" + "\n".join(errors))
    else:
        st.success("Strong password ✓")
```

**Verify:**
- Weak passwords show error messages
- Strong passwords are accepted
- Error messages are helpful

---

#### **Task 2.3: Clean Up Unused Imports**
**Why:** Reduces code clutter and potential security issues.  
**Effort:** 30 minutes  
**Difficulty:** Easy

**Find these in app.py:**
```python
import random  # Remove if unused
from streamlit.components import v1 as _components_v1  # Remove if unused
```

**Instructions:**
1. Search for uses of `random` in app.py:
   ```bash
   grep -n "random\." app.py
   ```
   If no results → Remove `import random`

2. Search for uses of `_components_v1`:
   ```bash
   grep -n "_components_v1" app.py
   ```
   If no results → Remove the import

3. Verify app still works:
   ```bash
   python deploy.py
   ```

**Verification:**
```bash
grep -n "^import random" app.py
grep -n "_components_v1" app.py
# Should return nothing
```

---

### **PHASE 3: INFRASTRUCTURE (Medium) — Do After Phase 2**

These improve configuration and dependency management.

#### **Task 3.1: Pin Dependency Versions**
**Why:** Prevents breaking changes from new versions.  
**Effort:** 1 hour  
**Difficulty:** Easy

**Current `requirements.txt`:**
```
streamlit>=1.35.0
pandas>=2.0.0
numpy>=1.24.0
```

**Better approach:**
```
streamlit==1.35.0
pandas==2.0.0
numpy==1.24.0
requests==2.31.0
```

**Instructions:**
1. Get current versions:
   ```bash
   pip list
   ```

2. Update `requirements.txt` with exact versions
3. Test:
   ```bash
   pip install -r requirements.txt
   python deploy.py
   ```

**Verification:**
- All dependencies install successfully
- App runs without errors
- Versions are specific (no `>=`)

---

#### **Task 3.2: Move `APP_URL` to Environment Variable**
**Why:** Different environments need different URLs (dev vs prod).  
**Effort:** 30 minutes  
**Difficulty:** Easy

**Find this in app.py (line 56):**
```python
APP_URL = "https://your-streamlit-app.streamlit.app"  # Hardcoded
```

**Change to:**
```python
APP_URL = os.getenv("APP_URL", "http://localhost:8501")
```

**Update `.env`:**
```env
APP_URL=https://your-streamlit-app.streamlit.app
```

**Verification:**
- App loads without errors
- URLs work correctly
- Different environments can use different URLs

---

### **PHASE 4: FEATURE DEVELOPMENT (Medium) — After Infrastructure**

These add new capabilities to the app.

#### **Task 4.1: Add CSE Sector Analysis**
**Why:** Help users understand which sectors are performing well.  
**Effort:** 3-4 hours  
**Difficulty:** Medium

**Scope:**
- Dashboard showing sector performance
- Heatmap: sectors vs performance metrics
- Filter stocks by sector
- Sector-specific briefings

**Implementation:** To be detailed when you reach this task

---

#### **Task 4.2: Add Price Alerts**
**Why:** Notify users when stock prices hit targets.  
**Effort:** 4-5 hours  
**Difficulty:** Medium

**Scope:**
- Set price alerts in Supabase
- Background job to check prices
- Email/SMS notifications
- Manage alerts in dashboard

---

#### **Task 4.3: Add Portfolio Tracking**
**Why:** Help users track their holdings.  
**Effort:** 5-6 hours  
**Difficulty:** Hard

**Scope:**
- Add portfolio management UI
- Store holdings in Supabase
- Calculate returns (realized + unrealized)
- Show portfolio performance chart

---

### **PHASE 5: TESTING & QA (Low) — After Features**

These ensure quality before launch.

#### **Task 5.1: Unit Tests**
#### **Task 5.2: Integration Tests**
#### **Task 5.3: User Acceptance Testing**

---

## 📋 Quick Reference: Next 5 Tasks

**Do these in order:**

1. **[CRITICAL - 5 min]** Rotate GitHub token → Task 1.1
2. **[CRITICAL - 1-2 hrs]** Audit XSS vulnerabilities → Task 1.2
3. **[HIGH - 30 min]** Add WebSocket timeout → Task 1.3
4. **[HIGH - 2-3 hrs]** Fix WebSocket race condition → Task 2.1
5. **[HIGH - 1 hr]** Add password validation → Task 2.2

---

## 🛠️ How to Use This Roadmap

### **Starting a Task**
```bash
# 1. Read the task description above
# 2. Follow the instructions
# 3. When done, run:
python deploy.py

# 4. Update project docs
# Edit: CLAUDE.md (mark task as done)
# Edit: CHANGELOG.md (add what you changed)
# Run: graphify update . (if code changes)
```

### **Tracking Progress**
- ✅ = Complete
- 🟡 = In progress
- ⏳ = Not started
- 🔴 = Blocked

---

## 📚 Resources

| Resource | Where | Purpose |
|----------|-------|---------|
| CLAUDE.md | Root folder | Project status & quick reference |
| CHANGELOG.md | Root folder | Version history |
| PROJECT_LOG.md | Root folder | Detailed session history |
| graphify-out/obsidian/ | Root folder | Codebase map (107 notes) |
| app.py | Root folder | Main app (~2065 lines) |

---

## 🚀 Deployment Workflow

**Every time you make changes:**

```bash
# 1. Make your code changes
# 2. Test locally if possible
# 3. Commit mentally: "What changed?"
# 4. Deploy:
python deploy.py

# 5. Check GitHub:
# https://github.com/VinupaHelitha/Investing-agent/commits/main

# 6. Verify on live app (1-2 min for Streamlit Cloud to redeploy)
```

---

## 💡 Pro Tips

### **Tip 1: Use Graphify to Understand Code**
Before making changes, query the knowledge graph:
```bash
pip install graphifyy --break-system-packages -q
graphify query "How does WebSocket connection work?"
graphify explain "CSE_WS_CACHE"
graphify path "app.py" "get_cse_prices"
```

### **Tip 2: Update Documentation After Changes**
```bash
# After making code changes:
graphify update .  # Rebuilds the knowledge graph
# Then update CLAUDE.md and CHANGELOG.md
```

### **Tip 3: Test Before Deploying**
```bash
# Run the app locally to test:
streamlit run app.py

# Then deploy to GitHub:
python deploy.py
```

### **Tip 4: Keep a Development Notes File**
Create `DEVELOPMENT_NOTES.md` to track:
- What you're working on
- Issues encountered
- Solutions applied
- Next steps

---

## ❓ FAQ

**Q: Where do I start?**  
A: Task 1.1 (Rotate GitHub token) - 5 minutes

**Q: How long will all tasks take?**  
A: Phase 1-3 (Security + Quality): ~10-15 hours  
Phase 4 (Features): ~15-20 hours  
Phase 5 (Testing): ~10 hours

**Q: Can I skip tasks?**  
A: Not recommended. Phases should be done in order.

**Q: What if I'm stuck?**  
A: Use graphify to understand the code, then ask for help with specific questions.

**Q: How do I deploy changes?**  
A: Always: `python deploy.py`

---

## 📞 Ready to Begin?

**Your next task:**

### **Task 1.1: Rotate GitHub Token (5 minutes)**

**Step 1:** Go to https://github.com/settings/tokens  
**Step 2:** Delete old "InvestSmart Deploy" token  
**Step 3:** Create new token with same settings  
**Step 4:** Copy new token  
**Step 5:** Update `.env` file  
**Step 6:** Run `python deploy.py`  
**Step 7:** Done! ✓

---

**Status:** Ready to start Phase 1  
**Estimated Time:** ~10 hours for all critical/high tasks  
**Priority:** Security first, then code quality

Let's build! 🚀

---

**Created:** 2026-05-16  
**Version:** 1.0  
**Last Updated:** 2026-05-16
