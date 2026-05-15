import sqlite3
from pathlib import Path

# Always resolve the DB path relative to this file's location (project root/database/)
_DB_PATH = Path(__file__).resolve().parent.parent / "MoneyWise.db"


def get_connection() -> sqlite3.Connection:
    """
    Return a new SQLite connection to MoneyWise.db.

    Settings applied on every connection:
      - WAL journal mode   → concurrent reads during writes (no blocking)
      - synchronous=NORMAL → safe + faster than FULL (data survives OS crash)
      - busy_timeout=5000  → wait up to 5 s before raising OperationalError
                             on a locked DB instead of failing immediately

    Each caller is responsible for closing the connection when done.
    Using check_same_thread=False is safe because every function opens
    and closes its own short-lived connection.
    """
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn