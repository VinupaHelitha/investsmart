#!/usr/bin/env python3
"""
InvestSmart GitHub Auto-Deploy
Permanent solution for pushing updates to GitHub
Handles authentication, batching, and error recovery
"""

import os
import sys
import json
import base64
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime

try:
    import requests
except ImportError:
    print("Installing requests library...")
    os.system(f"{sys.executable} -m pip install requests --break-system-packages -q")
    import requests

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Config:
    """Deployment configuration from environment or .env file"""
    github_token: str
    github_repo: str  # e.g., "VinupaHelitha/investsmart"
    github_branch: str = "main"
    files_to_push: List[str] = None

    def __post_init__(self):
        if not self.files_to_push:
            self.files_to_push = ["app.py", "requirements.txt"]

# ═══════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════════

def setup_logging(log_file: str = "deploy.log") -> logging.Logger:
    """Configure logging to file and console"""
    logger = logging.getLogger("investsmart.deploy")
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

logger = setup_logging()

# ═══════════════════════════════════════════════════════════════════
# ENVIRONMENT LOADING
# ═══════════════════════════════════════════════════════════════════

def load_env_file(env_path: Path = None) -> Dict[str, str]:
    """Load .env file if it exists"""
    if env_path is None:
        env_path = Path(__file__).parent / ".env"

    env_vars = {}
    if env_path.exists():
        logger.info(f"Loading environment from {env_path}")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        env_vars[key.strip()] = val.strip()

    return env_vars

def get_config() -> Config:
    """Load configuration from environment variables and .env file"""
    # Load .env file first
    env_vars = load_env_file()

    # Merge with OS environment (OS env takes precedence)
    for key, val in env_vars.items():
        if key not in os.environ:
            os.environ[key] = val

    # Read required variables
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("❌ GITHUB_TOKEN not set!")
        logger.error("\nTo fix:")
        logger.error("  1. Create .env file in this directory")
        logger.error("  2. Add: GITHUB_TOKEN=your_token_here")
        logger.error("  3. Get token from: https://github.com/settings/tokens")
        sys.exit(1)

    repo = os.getenv("GITHUB_REPO")
    if not repo:
        logger.error("❌ GITHUB_REPO not set!")
        logger.error("\nTo fix:")
        logger.error("  1. Edit .env file")
        logger.error("  2. Add: GITHUB_REPO=username/reponame")
        sys.exit(1)

    branch = os.getenv("GITHUB_BRANCH", "main")
    files_str = os.getenv("FILES_TO_PUSH", "app.py,requirements.txt")
    files = [f.strip() for f in files_str.split(",")]

    return Config(
        github_token=token,
        github_repo=repo,
        github_branch=branch,
        files_to_push=files
    )

# ═══════════════════════════════════════════════════════════════════
# GITHUB API FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

class GitHubClient:
    """GitHub API client with retry and error handling"""

    def __init__(self, token: str, repo: str, branch: str = "main"):
        self.token = token
        self.repo = repo
        self.branch = branch
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "InvestSmart-Deploy/2.0"
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"

        try:
            resp = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Network error: {e}")
            logger.error("   Check your internet connection and proxy settings")
            raise
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 401:
                logger.error("❌ Authentication failed!")
                logger.error("   Your GitHub token is invalid or expired")
                logger.error("   Generate a new one: https://github.com/settings/tokens")
            elif resp.status_code == 403:
                logger.error("❌ Access denied!")
                logger.error("   Check repo permissions and token scopes")
            elif resp.status_code == 404:
                logger.error("❌ Repository not found!")
                logger.error(f"   Repo: {self.repo}, Branch: {self.branch}")
            else:
                logger.error(f"❌ HTTP {resp.status_code}: {e}")
            raise

    def verify_auth(self) -> str:
        """Verify token is valid and return username"""
        try:
            resp = self._request("GET", "/user")
            data = resp.json()
            return data.get("login", "unknown")
        except Exception as e:
            logger.error(f"Failed to verify authentication: {e}")
            raise

    def get_file_sha(self, filepath: str) -> Optional[str]:
        """Get SHA of file (needed for updates)"""
        try:
            resp = self._request(
                "GET",
                f"/repos/{self.repo}/contents/{filepath}",
                params={"ref": self.branch}
            )
            return resp.json().get("sha")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None  # File doesn't exist yet
            raise

    def push_file(
        self,
        filepath: str,
        local_path: str,
        commit_msg: str
    ) -> Tuple[bool, str]:
        """Push file to GitHub"""
        logger.info(f"Reading {filepath}...")

        # Read local file
        if not Path(local_path).exists():
            logger.warning(f"⚠️  File not found: {filepath}")
            return False, "File not found"

        with open(local_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        # Get current SHA (if file exists)
        sha = self.get_file_sha(filepath)

        # Prepare payload
        payload = {
            "message": commit_msg,
            "content": content,
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha

        # Push
        try:
            logger.info(f"Pushing {filepath} to {self.repo}/{self.branch}...")
            resp = self._request(
                "PUT",
                f"/repos/{self.repo}/contents/{filepath}",
                json=payload
            )

            commit_data = resp.json()
            commit_sha = commit_data.get("commit", {}).get("sha", "unknown")
            commit_sha_short = commit_sha[:7] if len(commit_sha) > 7 else commit_sha

            logger.info(f"✓ {filepath} pushed (commit: {commit_sha_short})")
            return True, commit_sha

        except Exception as e:
            logger.error(f"Failed to push {filepath}: {e}")
            return False, str(e)

# ═══════════════════════════════════════════════════════════════════
# DEPLOYMENT WORKFLOW
# ═══════════════════════════════════════════════════════════════════

def deploy(config: Config) -> bool:
    """Execute deployment"""
    logger.info("=" * 70)
    logger.info("InvestSmart GitHub Deploy")
    logger.info("=" * 70)

    # Verify auth
    try:
        logger.info("Verifying GitHub authentication...")
        client = GitHubClient(config.github_token, config.github_repo, config.github_branch)
        username = client.verify_auth()
        logger.info(f"✓ Authenticated as: {username}")
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return False

    # Deploy files
    results = {}
    base_dir = Path(__file__).parent

    for filename in config.files_to_push:
        local_path = base_dir / filename
        commit_msg = f"Update {filename} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"

        success, sha = client.push_file(filename, str(local_path), commit_msg)
        results[filename] = {"success": success, "sha": sha}

    # Summary
    logger.info("=" * 70)
    logger.info("DEPLOYMENT SUMMARY")
    logger.info("=" * 70)

    success_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)

    for filename, result in results.items():
        status = "✓" if result["success"] else "✗"
        logger.info(f"{status} {filename}: {result['sha'][:40]}")

    logger.info(f"\nResult: {success_count}/{total_count} files pushed")

    if success_count == total_count:
        logger.info("✓ All files deployed successfully!")
        logger.info(f"\nView changes: https://github.com/{config.github_repo}/commits/{config.github_branch}")
        return True
    else:
        logger.error(f"✗ {total_count - success_count} file(s) failed")
        return False

# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

def print_setup_instructions():
    """Print setup guide"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║           InvestSmart GitHub Deploy — First Time Setup             ║
╚════════════════════════════════════════════════════════════════════╝

1. CREATE .env FILE
   Create a file named '.env' in this directory:

   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
   GITHUB_REPO=your-username/investsmart
   GITHUB_BRANCH=main
   FILES_TO_PUSH=app.py,requirements.txt

2. GET YOUR GITHUB TOKEN
   Go to: https://github.com/settings/tokens

   Click "Generate new token" → "Personal access tokens (classic)"

   Name: InvestSmart Deploy
   Scopes: Check 'repo' (full control)
   Expiry: 30-90 days

   Copy the token immediately (you won't see it again!)

3. SET YOUR REPO
   Replace 'your-username/investsmart' with your actual GitHub repo

   Example: VinupaHelitha/investsmart

4. RUN THIS SCRIPT
   python deploy.py

5. VIEW CHANGES
   https://github.com/your-username/investsmart/commits/main

═══════════════════════════════════════════════════════════════════════
⚠️  SECURITY TIPS:
  • Never commit .env to GitHub
  • Keep GitHub token secret
  • Rotate tokens every 30-90 days
  • Use repo-specific tokens if possible
═══════════════════════════════════════════════════════════════════════
    """)

def main():
    """Main entry point"""
    # Check if .env exists
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print_setup_instructions()
        print("\n✓ Next: Create .env file with your settings, then run this script again\n")
        sys.exit(0)

    try:
        config = get_config()
        success = deploy(config)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nDeploy cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Deploy failed: {e}")
        logger.error("\nCheck deploy.log for details")
        sys.exit(1)

if __name__ == "__main__":
    main()
