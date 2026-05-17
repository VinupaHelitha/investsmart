#!/usr/bin/env python3
"""
push_to_github.py — InvestSmart GitHub Pusher
Run from D:\Investing Agent 4.0\ to push the new app.py to GitHub.
Usage: python push_to_github.py
"""
import os, sys, json, base64
from pathlib import Path

GITHUB_TOKEN = "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"
REPO         = "VinupaHelitha/investsmart"
BRANCH       = "main"
FILE_PATH    = "app.py"
COMMIT_MSG   = "fix: replace yfinance CSE data with direct CSE WebSocket live feed"

SCRIPT_DIR = Path(__file__).parent
B64_FILE   = SCRIPT_DIR / "app_b64_full.txt"
API_URL    = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
HEADERS    = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept":        "application/vnd.github.v3+json",
    "Content-Type":  "application/json",
}

def main():
    try:
        import requests
    except ImportError:
        print("Missing: pip install requests"); sys.exit(1)

    if not B64_FILE.exists():
        print(f"File not found: {B64_FILE}"); sys.exit(1)

    b64_content = B64_FILE.read_text(encoding="utf-8").strip()
    print(f"Loaded app_b64_full.txt — {len(b64_content):,} chars")

    decoded = base64.b64decode(b64_content)
    print(f"Decoded OK — {len(decoded):,} bytes")

    print(f"\nFetching current SHA from GitHub...")
    r = requests.get(API_URL, headers=HEADERS, params={"ref": BRANCH}, timeout=30)
    r.raise_for_status()
    current_sha = r.json()["sha"]
    print(f"Current SHA: {current_sha}")

    print(f"\nPushing new app.py to {REPO} ({BRANCH})...")
    payload = {"message": COMMIT_MSG, "content": b64_content, "sha": current_sha, "branch": BRANCH}
    r = requests.put(API_URL, headers=HEADERS, json=payload, timeout=60)

    if r.status_code in (200, 201):
        j = r.json()
        print(f"\nSUCCESS!")
        print(f"  Commit SHA : {j['commit']['sha']}")
        print(f"  Commit URL : {j['commit']['html_url']}")
        print(f"\napp.py is now live! Streamlit will redeploy automatically.")
    else:
        print(f"\nFAILED — HTTP {r.status_code}")
        print(json.dumps(r.json(), indent=2)); sys.exit(1)

if __name__ == "__main__":
    main()
