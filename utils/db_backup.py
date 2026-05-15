"""
utils/db_backup.py

GitHub-backed SQLite backup/restore for MoneyWise AI.

Strategy
--------
* The .db file is stored as a Base64-encoded blob in a dedicated GitHub repo
  via the GitHub Contents API.
* On startup  → restore_db_from_github() — downloads latest backup if the
                 local file is missing OR effectively empty (< 8 KB).
* After writes → backup_db_to_github()   — uploads the current .db file,
                 skipping if content hasn't changed (SHA comparison).
* GitHub Actions keep_alive.yml pings the app every 6 h via Playwright.
* GitHub Actions db_backup_check.yml validates backup freshness on schedule.

Required Streamlit secrets (secrets.toml / Streamlit Cloud secrets):
    GITHUB_TOKEN        Personal Access Token with "repo" scope
    GITHUB_REPO         "username/repo-name" — where the DB backup lives
    GITHUB_DB_PATH      path inside that repo, e.g. "MoneyWise.db"
    GITHUB_BRANCH       branch to read/write, usually "main"

All four keys must be present; missing any makes every function a silent
no-op so local development continues to work without configuration.
"""

import base64
import hashlib
import logging
import os
import shutil
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# ── Resolve local DB path (same logic as connection.py) ───────────────────────
_DB_PATH = Path(__file__).resolve().parent.parent / "MoneyWise.db"

# SQLite files smaller than this are considered "empty schema only" and will
# be overwritten by a restore even if the file technically exists.
_DB_MIN_VALID_BYTES = 8 * 1024  # 8 KB

# ── GitHub API base ────────────────────────────────────────────────────────────
_GH_API = "https://api.github.com"


def _get_config() -> dict | None:
    """
    Reads GitHub credentials from Streamlit secrets or environment variables.
    Returns a dict with keys: token, repo, db_path, branch.
    Returns None if any required key is missing (silently disables backup).
    """
    try:
        import streamlit as st
        secrets = st.secrets
        token    = secrets.get("GITHUB_TOKEN",   os.getenv("GITHUB_TOKEN", ""))
        repo     = secrets.get("GITHUB_REPO",    os.getenv("GITHUB_REPO", ""))
        db_path  = secrets.get("GITHUB_DB_PATH", os.getenv("GITHUB_DB_PATH", "MoneyWise.db"))
        branch   = secrets.get("GITHUB_BRANCH",  os.getenv("GITHUB_BRANCH", "main"))
    except Exception:
        # Fallback for non-Streamlit contexts (e.g. GitHub Actions)
        token    = os.getenv("GITHUB_TOKEN", "")
        repo     = os.getenv("GITHUB_REPO", "")
        db_path  = os.getenv("GITHUB_DB_PATH", "MoneyWise.db")
        branch   = os.getenv("GITHUB_BRANCH", "main")

    if not token or not repo:
        return None

    return {"token": token, "repo": repo, "db_path": db_path, "branch": branch}


def _headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_remote_file_info(cfg: dict) -> dict | None:
    """
    Fetches the current file metadata (sha, download_url, content) from GitHub.
    Returns the JSON response dict or None if not found / error.
    """
    url = f"{_GH_API}/repos/{cfg['repo']}/contents/{cfg['db_path']}"
    params = {"ref": cfg["branch"]}
    try:
        resp = requests.get(url, headers=_headers(cfg["token"]), params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return None  # File doesn't exist yet — first-time backup
        else:
            logger.warning(f"[DB Backup] GitHub GET returned {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as exc:
        logger.error(f"[DB Backup] Failed to fetch remote file info: {exc}")
        return None


# ── Public API ─────────────────────────────────────────────────────────────────

def _is_db_effectively_empty() -> bool:
    """Returns True if the local DB file is missing or too small to contain real data."""
    if not _DB_PATH.exists():
        return True
    size = _DB_PATH.stat().st_size
    if size < _DB_MIN_VALID_BYTES:
        logger.info(
            f"[DB Backup] Local DB is {size:,} bytes (< {_DB_MIN_VALID_BYTES:,}) "
            "— treating as effectively empty."
        )
        return True
    return False


def get_local_db_sha256() -> str | None:
    """Returns hex SHA-256 of the local DB file, or None if it doesn't exist."""
    if not _DB_PATH.exists():
        return None
    try:
        data = _DB_PATH.read_bytes()
        return hashlib.sha256(data).hexdigest()
    except Exception:
        return None


def restore_db_from_github(force: bool = False) -> bool:
    """
    Downloads the latest DB backup from GitHub and saves it as MoneyWise.db.

    Triggers a restore if ANY of the following are true:
    - ``force=True``
    - The local file does not exist
    - The local file is < 8 KB (empty schema only — no real data)

    Returns True if a restore was performed, False otherwise.
    """
    cfg = _get_config()
    if cfg is None:
        logger.info("[DB Backup] No GitHub credentials found — skipping restore.")
        return False

    if not force and not _is_db_effectively_empty():
        logger.info(
            f"[DB Backup] Local DB exists and has data "
            f"({_DB_PATH.stat().st_size:,} bytes) — skipping restore."
        )
        return False

    logger.info(f"[DB Backup] Restoring DB from GitHub ({cfg['repo']} / {cfg['db_path']})…")
    info = _get_remote_file_info(cfg)

    if info is None:
        logger.warning("[DB Backup] No remote backup found. Starting with a fresh database.")
        return False

    try:
        content_b64 = info["content"]  # Base64 with newlines from GitHub API
        db_bytes = base64.b64decode(content_b64)

        if len(db_bytes) < _DB_MIN_VALID_BYTES:
            logger.warning(
                f"[DB Backup] Remote backup is suspiciously small ({len(db_bytes):,} bytes). "
                "Skipping restore to avoid overwriting with corrupted data."
            )
            return False

        # Atomic write: temp file → rename
        tmp_path = _DB_PATH.with_suffix(".db.tmp")
        tmp_path.write_bytes(db_bytes)
        shutil.move(str(tmp_path), str(_DB_PATH))

        logger.info(
            f"[DB Backup] ✅ Restore complete — {len(db_bytes):,} bytes written to {_DB_PATH.name}"
        )
        return True

    except Exception as exc:
        logger.error(f"[DB Backup] ❌ Restore failed: {exc}")
        return False


def backup_db_to_github(triggered_by: str = "manual", skip_if_unchanged: bool = True) -> bool:
    """
    Uploads the current MoneyWise.db to GitHub as a binary blob.

    Args:
        triggered_by:      Label included in the commit message for traceability.
        skip_if_unchanged: If True (default), compares local SHA-256 against the
                           content already on GitHub and skips the upload when they
                           match, avoiding unnecessary commits.

    Returns True on success (or when skipped as unchanged), False on failure.
    """
    cfg = _get_config()
    if cfg is None:
        logger.info("[DB Backup] No GitHub credentials found — skipping backup.")
        return False

    if not _DB_PATH.exists():
        logger.warning("[DB Backup] Local DB file not found — nothing to back up.")
        return False

    logger.info(f"[DB Backup] Backing up DB to GitHub (triggered_by={triggered_by})…")

    try:
        db_bytes = _DB_PATH.read_bytes()
        content_b64 = base64.b64encode(db_bytes).decode("utf-8")
        local_sha256 = hashlib.sha256(db_bytes).hexdigest()
    except Exception as exc:
        logger.error(f"[DB Backup] Failed to read local DB: {exc}")
        return False

    # ── Skip-if-unchanged check ───────────────────────────────────────────────
    info = _get_remote_file_info(cfg)  # None → first upload
    existing_sha = info["sha"] if info else None  # GitHub blob SHA (for PUT)

    if skip_if_unchanged and info:
        try:
            remote_bytes = base64.b64decode(info["content"])
            remote_sha256 = hashlib.sha256(remote_bytes).hexdigest()
            if local_sha256 == remote_sha256:
                logger.info(
                    f"[DB Backup] ⏭️  Content unchanged (SHA256 {local_sha256[:12]}…) "
                    "— skipping upload."
                )
                return True  # Nothing to do — treat as success
        except Exception:
            pass  # If comparison fails, proceed with upload

    commit_message = (
        f"chore: db-backup [{triggered_by}] "
        f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} "
        f"sha256:{local_sha256[:12]}"
    )

    payload: dict = {
        "message": commit_message,
        "content": content_b64,
        "branch": cfg["branch"],
    }
    if existing_sha:
        payload["sha"] = existing_sha  # Required for updates; omit for first create

    url = f"{_GH_API}/repos/{cfg['repo']}/contents/{cfg['db_path']}"
    try:
        resp = requests.put(
            url,
            headers=_headers(cfg["token"]),
            json=payload,
            timeout=60,
        )
        if resp.status_code in (200, 201):
            logger.info(
                f"[DB Backup] ✅ Backup successful — "
                f"{len(db_bytes):,} bytes → {cfg['repo']}/{cfg['db_path']}"
            )
            return True
        else:
            logger.error(
                f"[DB Backup] ❌ GitHub PUT returned {resp.status_code}: {resp.text[:400]}"
            )
            return False

    except Exception as exc:
        logger.error(f"[DB Backup] ❌ Backup request failed: {exc}")
        return False


def get_backup_status() -> dict:
    """
    Returns a status dict useful for displaying in the UI.
    Keys: enabled (bool), remote_exists (bool), remote_sha (str|None),
          remote_size_bytes (int|None), error (str|None)
    """
    cfg = _get_config()
    if cfg is None:
        return {"enabled": False, "remote_exists": False, "remote_sha": None,
                "remote_size_bytes": None, "error": "GitHub credentials not configured"}

    info = _get_remote_file_info(cfg)
    if info:
        return {
            "enabled": True,
            "remote_exists": True,
            "remote_sha": info.get("sha", "")[:7],
            "remote_size_bytes": info.get("size"),
            "error": None,
        }
    else:
        return {
            "enabled": True,
            "remote_exists": False,
            "remote_sha": None,
            "remote_size_bytes": None,
            "error": None,
        }
