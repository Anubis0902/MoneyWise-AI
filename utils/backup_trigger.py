"""
utils/backup_trigger.py

Non-blocking backup trigger for MoneyWise AI.

How it works:
- A counter in st.session_state tracks how many DB writes have occurred.
- When the counter hits BACKUP_EVERY_N_WRITES, OR when COOLDOWN_SECONDS
  have passed since the last backup, a backup is started in a daemon thread
  so the Streamlit UI is never blocked.
- Provides trigger_backup_if_needed() to call after any DB write, and
  trigger_backup_now() for the manual "Backup Now" sidebar button.

Usage (in any service / agent after a write):
    from utils.backup_trigger import trigger_backup_if_needed
    trigger_backup_if_needed()
"""

import logging
import threading
import time

import streamlit as st

logger = logging.getLogger(__name__)

# ── Tuneable constants ─────────────────────────────────────────────────────────
BACKUP_EVERY_N_WRITES = 10        # Fire after every 10 write operations
COOLDOWN_SECONDS      = 5 * 60   # Never backup more often than every 5 minutes


def _run_backup_in_background(reason: str = "auto") -> None:
    """Runs backup_db_to_github in a daemon thread so UI is never blocked."""
    def _worker():
        try:
            from utils.db_backup import backup_db_to_github
            backup_db_to_github(triggered_by=reason)
        except Exception as exc:
            logger.error(f"[BackupTrigger] Background backup failed: {exc}")

    t = threading.Thread(target=_worker, daemon=True, name="db-backup")
    t.start()
    logger.info(f"[BackupTrigger] Backup thread started (reason={reason})")


def _init_state() -> None:
    """Ensure session state keys exist."""
    if "backup_write_count" not in st.session_state:
        st.session_state["backup_write_count"] = 0
    if "backup_last_time" not in st.session_state:
        st.session_state["backup_last_time"] = 0.0
    if "backup_status_msg" not in st.session_state:
        st.session_state["backup_status_msg"] = ""


def trigger_backup_if_needed() -> None:
    """
    Call this after every DB write (transaction add/edit/delete, goal update, etc.).
    Fires a background backup when either:
      - write count reaches BACKUP_EVERY_N_WRITES, OR
      - COOLDOWN_SECONDS have passed since the last backup
    """
    _init_state()

    st.session_state["backup_write_count"] += 1
    count     = st.session_state["backup_write_count"]
    last_time = st.session_state["backup_last_time"]
    now       = time.time()

    count_threshold_hit = (count % BACKUP_EVERY_N_WRITES == 0)
    cooldown_expired    = (now - last_time) >= COOLDOWN_SECONDS

    if count_threshold_hit or (cooldown_expired and count > 0):
        reason = f"after-{count}-writes" if count_threshold_hit else "cooldown-expired"
        st.session_state["backup_last_time"] = now
        st.session_state["backup_status_msg"] = "⏳ Backup in progress…"
        _run_backup_in_background(reason=reason)


def trigger_backup_now() -> None:
    """
    Immediately fires a background backup (used by the manual sidebar button).
    """
    _init_state()
    st.session_state["backup_last_time"] = time.time()
    st.session_state["backup_status_msg"] = "⏳ Backup in progress…"
    _run_backup_in_background(reason="manual-button")
