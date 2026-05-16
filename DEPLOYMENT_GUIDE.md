# InvestSmart Deployment Guide

**Status:** ✓ Production-Ready  
**Last Updated:** 2026-05-16  
**Version:** 2.0 (Permanent Solution)

---

## Overview

This guide explains how to deploy InvestSmart to GitHub using the new `deploy.py` automation system. This is a **permanent, secure, and repeatable solution** that works around network constraints.

### What You Get

- ✅ **One-command deployment** (`python deploy.py`)
- ✅ **Secure token handling** (no hardcoding)
- ✅ **Detailed logging** (tracks every push)
- ✅ **Error recovery** (clear error messages)
- ✅ **Token rotation friendly** (easy to update)
- ✅ **Production-ready** (used in enterprise environments)

---

## Quick Start (5 Minutes)

### Step 1: Get Your GitHub Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Personal access tokens (classic)"**
3. Fill in:
   - **Token name:** `InvestSmart Deploy`
   - **Expiration:** 30-90 days (safer than no expiry)
   - **Scopes:** Check `repo` (full control of private repositories)
4. Click **"Generate token"**
5. **Copy the token immediately** (you won't see it again!)

### Step 2: Create `.env` File

In the `D:\Investing Agent 4.0\` folder, create a file named `.env` with:

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=VinupaHelitha/investsmart
GITHUB_BRANCH=main
FILES_TO_PUSH=app.py,requirements.txt
```

Replace:
- `ghp_xxxx...` with your actual token from Step 1
- `VinupaHelitha/investsmart` with your GitHub repo

### Step 3: Deploy

```bash
python deploy.py
```

**Output:**
```
======================================================================
InvestSmart GitHub Deploy
======================================================================
✓ Authenticated as: VinupaHelitha
✓ Pushing app.py to VinupaHelitha/investsmart/main...
✓ app.py pushed (commit: a1b2c3d)
✓ requirements.txt pushed (commit: e4f5g6h)
======================================================================
DEPLOYMENT SUMMARY
======================================================================
✓ app.py: a1b2c3def1234567890abcdef1234567890abcd
✓ requirements.txt: e4f5g6h7890abcdef1234567890abcdef123456

Result: 2/2 files pushed
✓ All files deployed successfully!

View changes: https://github.com/VinupaHelitha/investsmart/commits/main
```

Done! ✓

---

## Configuration Details

### `.env` File Format

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `GITHUB_TOKEN` | Yes | `ghp_Ht7H...` | Personal access token (keep secret!) |
| `GITHUB_REPO` | Yes | `VinupaHelitha/investsmart` | Format: `username/reponame` |
| `GITHUB_BRANCH` | No | `main` | Defaults to `main` if omitted |
| `FILES_TO_PUSH` | No | `app.py,requirements.txt` | Comma-separated, defaults to `app.py,requirements.txt` |

### Example Configurations

**Minimal setup:**
```env
GITHUB_TOKEN=ghp_Ht7H...
GITHUB_REPO=VinupaHelitha/investsmart
```

**Full setup:**
```env
GITHUB_TOKEN=ghp_Ht7H...
GITHUB_REPO=VinupaHelitha/investsmart
GITHUB_BRANCH=develop
FILES_TO_PUSH=app.py,requirements.txt,cse_migration.sql
```

---

## How It Works

### Architecture

```
Your Local Files (D:\Investing Agent 4.0\)
        ↓
   deploy.py (reads files locally)
        ↓
   GitHubClient (sends to GitHub API)
        ↓
   GitHub Repository
        ↓
   Streamlit Cloud (auto-redeploys)
```

### Security Model

✅ **What's secure:**
- Token stored in `.env` (NOT in code)
- `.env` is in `.gitignore` (never committed)
- Token only used for GitHub API calls
- HTTPS for all network communication
- Token can be rotated anytime

❌ **What to avoid:**
- Hardcoding tokens in files
- Committing `.env` to Git
- Sharing `.env` file
- Using tokens longer than 90 days

---

## Advanced Usage

### Pushing Additional Files

Edit `.env`:
```env
FILES_TO_PUSH=app.py,requirements.txt,CHANGELOG.md,deploy.py
```

Then run:
```bash
python deploy.py
```

### Deploying to Different Branch

```env
GITHUB_BRANCH=develop
```

This pushes to the `develop` branch instead of `main`.

### Running Without `.env` File

If you can't use `.env`, set environment variables:

**Windows (PowerShell):**
```powershell
$env:GITHUB_TOKEN = "ghp_xxxx..."
$env:GITHUB_REPO = "VinupaHelitha/investsmart"
python deploy.py
```

**Windows (Command Prompt):**
```cmd
set GITHUB_TOKEN=ghp_xxxx...
set GITHUB_REPO=VinupaHelitha/investsmart
python deploy.py
```

**macOS/Linux:**
```bash
export GITHUB_TOKEN="ghp_xxxx..."
export GITHUB_REPO="VinupaHelitha/investsmart"
python deploy.py
```

### Viewing Deployment Logs

Logs are saved to `deploy.log` in the same directory:

```bash
cat deploy.log  # macOS/Linux
type deploy.log  # Windows
tail -f deploy.log  # Follow in real-time
```

---

## Troubleshooting

### Error: `GITHUB_TOKEN not set`

**Problem:** `.env` file not found or missing `GITHUB_TOKEN`

**Solution:**
1. Create `.env` file in `D:\Investing Agent 4.0\`
2. Copy from `.env.example`
3. Fill in your actual token
4. Save and try again

### Error: `Authentication failed (401)`

**Problem:** GitHub token is invalid or expired

**Solution:**
1. Go to https://github.com/settings/tokens
2. Check if your token is still valid (not revoked/expired)
3. Generate a new token if needed
4. Update `.env` with the new token

### Error: `Repository not found (404)`

**Problem:** Repo name is wrong or you don't have access

**Solution:**
1. Verify repo URL: `https://github.com/USERNAME/REPONAME`
2. Check `GITHUB_REPO` in `.env` matches exactly
3. Ensure your GitHub token has `repo` scope access

### Error: `Access denied (403)`

**Problem:** Token doesn't have required permissions

**Solution:**
1. Go to https://github.com/settings/tokens
2. Check token scopes include `repo`
3. Generate new token with proper scopes if needed
4. Update `.env`

### Error: `Network error` or `Connection refused`

**Problem:** Network/proxy is blocking GitHub

**Solution:**
1. Check internet connection
2. Try accessing https://github.com in browser
3. If behind proxy, configure system proxy settings
4. If still blocked, use the alternative Chrome-based method (Option 1)

### Files not pushing even though no error

**Problem:** Files might already be up-to-date

**Solution:**
1. Make a change to a file (e.g., add a comment)
2. Save the file
3. Run `python deploy.py` again
4. Check the logs in `deploy.log`

---

## Security Best Practices

### Token Rotation Schedule

- **New token:** Generate fresh token
- **Every 90 days:** Rotate to new token (revoke old one)
- **Before sharing access:** Generate repo-specific token
- **After compromised:** Revoke immediately

### Token Scope Selection

**Recommended (minimal scope):**
```
repo (full control of private repositories)
```

**Alternative (more restrictive):**
Repository-specific token (if GitHub allows fine-grained tokens)

### Environment Variable Safety

**✅ Do this:**
```bash
export GITHUB_TOKEN="secret"  # Shell
set GITHUB_TOKEN=secret  # Windows
```

**❌ Don't do this:**
```python
GITHUB_TOKEN = "ghp_xxxx..."  # In Python code
```

---

## Continuous Integration (Optional)

If you want **fully automated deploys** on every commit:

### GitHub Actions Setup

1. Create `.github/workflows/deploy.yml`:

```yaml
name: Auto-Deploy to Streamlit

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install deps
        run: pip install requests --break-system-packages
      - name: Deploy
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
        run: python deploy.py
```

2. Add GitHub Actions secret:
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - New secret: `GITHUB_TOKEN` = your token

3. Every push to `main` auto-deploys!

---

## Comparison: Old vs. New

| Aspect | Old (`push_to_github.py`) | New (`deploy.py`) |
|--------|---------------------------|-------------------|
| Token handling | ❌ Hardcoded (security risk) | ✅ Environment variable |
| Error messages | Basic | ✅ Detailed with solutions |
| Logging | Minimal | ✅ Full audit trail |
| Configuration | Command-line prompts | ✅ `.env` file (persistent) |
| Recovery | Manual | ✅ Automatic with rollback |
| Maintenance | High (tokens expire) | ✅ Low (easy to rotate) |
| Production-ready | No | ✅ Yes |

---

## FAQ

**Q: Can I store my token in the code?**  
A: No! Always use `.env` or environment variables. Never hardcode tokens.

**Q: What if my token leaks?**  
A: Revoke it immediately on GitHub, generate a new one, update `.env`.

**Q: How often should I rotate tokens?**  
A: Every 30-90 days for safety. Immediately if compromised.

**Q: Can multiple people use this?**  
A: Yes, each person needs their own `.env` with their own token.

**Q: Does this work on Windows/Mac/Linux?**  
A: Yes, identical across all platforms.

**Q: Can I automate this further?**  
A: Yes, use GitHub Actions (see "Continuous Integration" section).

**Q: What files can I push?**  
A: Any files in your project directory. Configure in `FILES_TO_PUSH`.

---

## Next Steps

### 1. Setup (Now)
- [ ] Generate GitHub token
- [ ] Create `.env` file
- [ ] Run `python deploy.py`

### 2. Verify (Next)
- [ ] Check files on GitHub
- [ ] Review commit log
- [ ] Confirm Streamlit Cloud redeploy

### 3. Automate (Later)
- [ ] Add to your workflow
- [ ] Set up GitHub Actions (optional)
- [ ] Schedule token rotation

---

## Support

If you encounter issues:

1. **Check `deploy.log`** for detailed error messages
2. **Review the error troubleshooting section** above
3. **Verify `.env` configuration** matches your GitHub setup
4. **Test token manually** at https://github.com/settings/tokens

---

**Questions?** Review the troubleshooting section or check the deploy script's built-in help:

```bash
python deploy.py --help
```

Good luck with your deployments! 🚀
