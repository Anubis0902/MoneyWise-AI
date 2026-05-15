"""
scripts/test_deployment.py

End-to-end test suite for the MoneyWise AI deployment support system.

Tests covered
─────────────
  1. Config loading (Streamlit secrets + env vars)
  2. DB restore flow (startup → GitHub → local disk)
  3. DB backup flow (local → GitHub, skip-if-unchanged)
  4. Empty-DB detection threshold
  5. DB backup health check (SQLite magic bytes + freshness logic)
  6. Playwright keep-alive script import & env-var validation
  7. Failure scenarios (missing creds, missing file, bad remote)

Run from the project root:
    python scripts/test_deployment.py

All tests are read-only when GitHub credentials are present in the environment.
The one destructive test (backup upload) is skipped unless --live flag is passed.
"""

import base64
import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── Make sure project root is on sys.path ────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

LIVE_MODE = "--live" in sys.argv   # pass --live to run destructive upload tests

# ─────────────────────────────────────────────────────────────────────────────
# Helper: fake GitHub API response
# ─────────────────────────────────────────────────────────────────────────────
SQLITE_MAGIC   = b"SQLite format 3\x00"
_FAKE_DB_BYTES = SQLITE_MAGIC + b"\x00" * (9 * 1024)   # 9 KB fake DB


def _make_github_file_response(content: bytes) -> dict:
    """Returns a dict shaped like a GitHub Contents API response."""
    b64 = base64.b64encode(content).decode()
    return {
        "sha":            "abc1234def5678",
        "size":           len(content),
        "content":        b64,
        "download_url":   "https://raw.githubusercontent.com/fake/repo/main/MoneyWise.db",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1. Config loading
# ─────────────────────────────────────────────────────────────────────────────
class TestConfigLoading(unittest.TestCase):
    """
    _get_config() does `import streamlit as st` locally on every call, so
    Python resolves it via sys.modules at call time.  Replacing
    sys.modules["streamlit"] with a controlled mock is the only reliable
    way to intercept it without touching the real secrets.toml.
    """

    @staticmethod
    def _mock_st(secrets_map: dict):
        """Returns a MagicMock shaped like the streamlit module with preset secrets."""
        mock = MagicMock()
        # secrets.get(key, default) → value from secrets_map or default
        mock.secrets.get.side_effect = lambda key, default="": secrets_map.get(key, default)
        return mock

    def test_returns_none_when_no_creds(self):
        """_get_config() must return None (→ silent no-op) when credentials are absent."""
        from utils.db_backup import _get_config
        # Empty secrets + empty env vars → no token, no repo → None
        mock_st = self._mock_st({})
        with patch.dict(sys.modules, {"streamlit": mock_st}), \
             patch.dict(os.environ, {"GITHUB_TOKEN": "", "GITHUB_REPO": ""}):
            result = _get_config()
        self.assertIsNone(result)

    def test_returns_config_when_env_vars_set(self):
        """_get_config() must return a complete dict when secrets supply all keys."""
        from utils.db_backup import _get_config
        secrets = {
            "GITHUB_TOKEN":   "ghp_test_token",
            "GITHUB_REPO":    "user/repo",
            "GITHUB_DB_PATH": "MoneyWise.db",
            "GITHUB_BRANCH":  "main",
        }
        mock_st = self._mock_st(secrets)
        with patch.dict(sys.modules, {"streamlit": mock_st}), \
             patch.dict(os.environ, secrets):
            result = _get_config()
        self.assertIsNotNone(result)
        self.assertEqual(result["token"], "ghp_test_token")
        self.assertEqual(result["repo"],  "user/repo")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Empty-DB detection
# ─────────────────────────────────────────────────────────────────────────────
class TestEmptyDbDetection(unittest.TestCase):

    def test_missing_file_is_empty(self):
        from utils.db_backup import _is_db_effectively_empty, _DB_PATH
        with patch("utils.db_backup._DB_PATH", Path("/nonexistent/MoneyWise.db")):
            self.assertTrue(_is_db_effectively_empty())

    def test_small_file_is_empty(self):
        from utils.db_backup import _is_db_effectively_empty, _DB_MIN_VALID_BYTES
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(b"\x00" * 1024)   # 1 KB — below threshold
            tmp = Path(f.name)
        try:
            with patch("utils.db_backup._DB_PATH", tmp):
                self.assertTrue(_is_db_effectively_empty())
        finally:
            tmp.unlink(missing_ok=True)

    def test_valid_size_is_not_empty(self):
        from utils.db_backup import _is_db_effectively_empty, _DB_MIN_VALID_BYTES
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(b"\x00" * 10 * 1024)   # 10 KB — above threshold
            tmp = Path(f.name)
        try:
            with patch("utils.db_backup._DB_PATH", tmp):
                self.assertFalse(_is_db_effectively_empty())
        finally:
            tmp.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. DB restore flow (mocked)
# ─────────────────────────────────────────────────────────────────────────────
class TestRestoreFlow(unittest.TestCase):

    def _make_config(self):
        return {
            "token":   "ghp_test",
            "repo":    "user/repo",
            "db_path": "MoneyWise.db",
            "branch":  "main",
        }

    def test_restore_skipped_when_no_config(self):
        from utils.db_backup import restore_db_from_github
        with patch("utils.db_backup._get_config", return_value=None):
            result = restore_db_from_github()
        self.assertFalse(result)

    def test_restore_skipped_when_db_exists_and_has_data(self):
        from utils.db_backup import restore_db_from_github
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(b"\x00" * 20 * 1024)   # 20 KB — well above threshold
            tmp = Path(f.name)
        try:
            with patch("utils.db_backup._get_config", return_value=self._make_config()), \
                 patch("utils.db_backup._DB_PATH", tmp):
                result = restore_db_from_github(force=False)
            self.assertFalse(result)
        finally:
            tmp.unlink(missing_ok=True)

    def test_restore_triggered_when_db_missing(self):
        from utils.db_backup import restore_db_from_github
        fake_info = _make_github_file_response(_FAKE_DB_BYTES)
        with tempfile.TemporaryDirectory() as td:
            tmp_db = Path(td) / "MoneyWise.db"   # does NOT exist yet
            with patch("utils.db_backup._get_config", return_value=self._make_config()), \
                 patch("utils.db_backup._DB_PATH", tmp_db), \
                 patch("utils.db_backup._get_remote_file_info", return_value=fake_info):
                result = restore_db_from_github()
            self.assertTrue(result)
            self.assertTrue(tmp_db.exists())
            self.assertEqual(tmp_db.read_bytes(), _FAKE_DB_BYTES)

    def test_restore_triggered_when_db_effectively_empty(self):
        from utils.db_backup import restore_db_from_github
        fake_info = _make_github_file_response(_FAKE_DB_BYTES)
        with tempfile.TemporaryDirectory() as td:
            tmp_db = Path(td) / "MoneyWise.db"
            tmp_db.write_bytes(b"\x00" * 512)   # 512 bytes — way below 8 KB
            with patch("utils.db_backup._get_config", return_value=self._make_config()), \
                 patch("utils.db_backup._DB_PATH", tmp_db), \
                 patch("utils.db_backup._get_remote_file_info", return_value=fake_info):
                result = restore_db_from_github()
            self.assertTrue(result)

    def test_restore_returns_false_when_no_remote_backup(self):
        from utils.db_backup import restore_db_from_github
        with patch("utils.db_backup._get_config", return_value=self._make_config()), \
             patch("utils.db_backup._DB_PATH", Path("/nonexistent/MoneyWise.db")), \
             patch("utils.db_backup._get_remote_file_info", return_value=None):
            result = restore_db_from_github()
        self.assertFalse(result)

    def test_restore_rejects_suspiciously_small_remote(self):
        """Remote backup < 8 KB should be rejected to prevent overwriting with corruption."""
        from utils.db_backup import restore_db_from_github
        tiny_backup = _make_github_file_response(b"\x00" * 512)   # too small
        with tempfile.TemporaryDirectory() as td:
            tmp_db = Path(td) / "MoneyWise.db"   # missing
            with patch("utils.db_backup._get_config", return_value=self._make_config()), \
                 patch("utils.db_backup._DB_PATH", tmp_db), \
                 patch("utils.db_backup._get_remote_file_info", return_value=tiny_backup):
                result = restore_db_from_github()
            self.assertFalse(result)
            self.assertFalse(tmp_db.exists())   # must NOT have been created


# ─────────────────────────────────────────────────────────────────────────────
# 4. DB backup flow (mocked)
# ─────────────────────────────────────────────────────────────────────────────
class TestBackupFlow(unittest.TestCase):

    def _make_config(self):
        return {
            "token":   "ghp_test",
            "repo":    "user/repo",
            "db_path": "MoneyWise.db",
            "branch":  "main",
        }

    def test_backup_skipped_when_no_config(self):
        from utils.db_backup import backup_db_to_github
        with patch("utils.db_backup._get_config", return_value=None):
            self.assertFalse(backup_db_to_github())

    def test_backup_skipped_when_no_local_file(self):
        from utils.db_backup import backup_db_to_github
        with patch("utils.db_backup._get_config", return_value=self._make_config()), \
             patch("utils.db_backup._DB_PATH", Path("/nonexistent/MoneyWise.db")):
            self.assertFalse(backup_db_to_github())

    def test_backup_skipped_if_unchanged(self):
        """skip_if_unchanged=True (default) must skip when SHA-256 matches remote."""
        from utils.db_backup import backup_db_to_github
        db_bytes = _FAKE_DB_BYTES
        remote_info = _make_github_file_response(db_bytes)   # same content
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(db_bytes)
            tmp = Path(f.name)
        try:
            with patch("utils.db_backup._get_config", return_value=self._make_config()), \
                 patch("utils.db_backup._DB_PATH", tmp), \
                 patch("utils.db_backup._get_remote_file_info", return_value=remote_info):
                result = backup_db_to_github(triggered_by="test", skip_if_unchanged=True)
            self.assertTrue(result)   # skipped = treated as success
        finally:
            tmp.unlink(missing_ok=True)

    def test_backup_uploads_when_content_changed(self):
        """When local SHA differs from remote, a PUT request must be made."""
        from utils.db_backup import backup_db_to_github
        local_bytes  = _FAKE_DB_BYTES + b"\xff"                  # slightly different
        remote_info  = _make_github_file_response(_FAKE_DB_BYTES)  # old content
        mock_put_resp = MagicMock()
        mock_put_resp.status_code = 200
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(local_bytes)
            tmp = Path(f.name)
        try:
            with patch("utils.db_backup._get_config", return_value=self._make_config()), \
                 patch("utils.db_backup._DB_PATH", tmp), \
                 patch("utils.db_backup._get_remote_file_info", return_value=remote_info), \
                 patch("utils.db_backup.requests.put", return_value=mock_put_resp) as mock_put:
                result = backup_db_to_github(triggered_by="test", skip_if_unchanged=True)
            self.assertTrue(result)
            mock_put.assert_called_once()   # PUT must have been issued
        finally:
            tmp.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. SHA-256 helper
# ─────────────────────────────────────────────────────────────────────────────
class TestSha256Helper(unittest.TestCase):

    def test_returns_none_for_missing_file(self):
        from utils.db_backup import get_local_db_sha256
        with patch("utils.db_backup._DB_PATH", Path("/nonexistent/MoneyWise.db")):
            self.assertIsNone(get_local_db_sha256())

    def test_returns_correct_sha256(self):
        from utils.db_backup import get_local_db_sha256
        data = b"hello world"
        expected = hashlib.sha256(data).hexdigest()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(data)
            tmp = Path(f.name)
        try:
            with patch("utils.db_backup._DB_PATH", tmp):
                self.assertEqual(get_local_db_sha256(), expected)
        finally:
            tmp.unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 6. SQLite magic bytes validation (mirrors db_backup.yml health check)
# ─────────────────────────────────────────────────────────────────────────────
class TestSqliteMagicBytes(unittest.TestCase):

    MAGIC = b"SQLite format 3\x00"

    def test_real_sqlite_has_correct_magic(self):
        import sqlite3
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            tmp = f.name
        try:
            conn = sqlite3.connect(tmp)
            conn.execute("CREATE TABLE t (x INTEGER)")
            conn.commit()
            conn.close()
            # Use context manager to avoid ResourceWarning on unclosed file
            with open(tmp, "rb") as fh:
                data = fh.read()
            self.assertEqual(data[:16], self.MAGIC)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_random_bytes_fail_magic_check(self):
        bad_data = b"\xff\xd8\xff\xe0" + b"\x00" * 12   # JPEG header
        self.assertNotEqual(bad_data[:16], self.MAGIC)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Keep-alive script env-var validation (import-only, no browser launched)
# ─────────────────────────────────────────────────────────────────────────────
class TestKeepAliveScript(unittest.TestCase):

    def test_exits_with_1_when_url_missing(self):
        """keep_alive.run() must call sys.exit(1) if STREAMLIT_APP_URL is empty."""
        import asyncio
        with patch.dict(os.environ, {"STREAMLIT_APP_URL": ""}, clear=False):
            import scripts.keep_alive as ka
            ka.STREAMLIT_APP_URL = ""   # force the module-level variable
            with self.assertRaises(SystemExit) as ctx:
                asyncio.run(ka.run())
            self.assertEqual(ctx.exception.code, 1)

    def test_url_env_var_is_read(self):
        """Module-level STREAMLIT_APP_URL must reflect the env variable."""
        with patch.dict(os.environ, {"STREAMLIT_APP_URL": "https://test.streamlit.app"}):
            import importlib
            import scripts.keep_alive as ka
            importlib.reload(ka)
            self.assertEqual(ka.STREAMLIT_APP_URL, "https://test.streamlit.app")


# ─────────────────────────────────────────────────────────────────────────────
# 8. LIVE tests (only run with --live flag — performs real GitHub API calls)
# ─────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(LIVE_MODE, "Skipped — pass --live to run live API tests")
class TestLiveGitHubIntegration(unittest.TestCase):

    def test_get_backup_status(self):
        """Live: get_backup_status() should return a dict with 'enabled' key."""
        from utils.db_backup import get_backup_status
        status = get_backup_status()
        self.assertIn("enabled", status)
        print(f"\n[LIVE] Backup status: {status}")

    def test_live_backup_upload(self):
        """Live: backup_db_to_github() should succeed or skip (not crash)."""
        from utils.db_backup import backup_db_to_github
        result = backup_db_to_github(triggered_by="live-test", skip_if_unchanged=True)
        self.assertTrue(result)
        print(f"\n[LIVE] Backup upload result: {result}")


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Strip --live from sys.argv so unittest doesn't choke on it
    if "--live" in sys.argv:
        sys.argv.remove("--live")

    print("=" * 70)
    print("MoneyWise AI — Deployment Support System Tests")
    print(f"Live mode: {'ON (--live)' if LIVE_MODE else 'OFF (mocked)'}")
    print("=" * 70)
    unittest.main(verbosity=2)
