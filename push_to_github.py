"""
push_to_github.py  -  InvestSmart auto-deploy helper
Double-click this file (or run: python push_to_github.py) to push
the latest app.py and requirements.txt to your GitHub repo.
"""
import base64, json, os, sys
try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests")
    import requests

# -- CONFIG --
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    print("ERROR: GITHUB_TOKEN environment variable is not set.")
    print("Please set it before running this script.")
    sys.exit(1)
BRANCH = "main"
COMMIT_MSG = "fix: replace streamlit-autorefresh with native JS auto-refresh + premium tier"
# -------------

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

HERE = os.path.dirname(os.path.abspath(__file__))

def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_sha(repo, filepath):
    url = f"https://api.github.com/repos/{repo}/contents/{filepath}?ref={BRANCH}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 200:
        return r.json().get("sha")
    return None

def push_file(repo, filepath, local_path, msg):
    sha = get_sha(repo, filepath)
    payload = {
        "message": msg,
        "content": b64(local_path),
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha
    url = f"https://api.github.com/repos/{repo}/contents/{filepath}"
    r = requests.put(url, headers=HEADERS, data=json.dumps(payload))
    return r.status_code, r.json().get("commit", {}).get("sha", r.text[:120])

def main():
    me = requests.get("https://api.github.com/user", headers=HEADERS).json()
    login = me.get("login")
    if not login:
        print("ERROR: GitHub token invalid or expired.")
        print(me)
        input("Press Enter to exit...")
        sys.exit(1)
    print(f"Authenticated as: {login}")

    repos_r = requests.get(
        f"https://api.github.com/user/repos?per_page=100&sort=updated",
        headers=HEADERS).json()
    if not isinstance(repos_r, list):
        print("ERROR fetching repos:", repos_r)
        input("Press Enter to exit...")
        sys.exit(1)

    print(f"\nYour repos (most recently updated):")
    for i, repo in enumerate(repos_r[:15]):
        print(f"  [{i+1}] {repo['full_name']}")

    print()
    choice = input("Enter repo number from the list above: ").strip()
    try:
        repo_full = repos_r[int(choice) - 1]["full_name"]
    except Exception:
        print("Invalid choice.")
        input("Press Enter to exit...")
        sys.exit(1)

    print(f"\nTarget repo: {repo_full} (branch: {BRANCH})")
    confirm = input("Push app.py + requirements.txt? (yes/no): ").strip().lower()
    if confirm not in ("yes", "y"):
        print("Cancelled.")
        input("Press Enter to exit...")
        sys.exit(0)

    files_to_push = [
        ("app.py",           os.path.join(HERE, "app.py")),
        ("requirements.txt", os.path.join(HERE, "requirements.txt")),
    ]
    for gh_path, local_path in files_to_push:
        if not os.path.exists(local_path):
            print(f"  SKIP {gh_path} (file not found locally)")
            continue
        print(f"  Pushing {gh_path}...", end=" ", flush=True)
        status, sha = push_file(repo_full, gh_path, local_path, COMMIT_MSG)
        if status in (200, 201):
            print(f"OK  (commit: {sha[:10] if len(sha) >= 10 else sha})")
        else:
            print(f"FAILED (HTTP {status}): {sha}")

    print("\nDone! Streamlit Cloud will redeploy automatically in ~1-2 minutes.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
