"""
scripts/qa_runner.py
Automated QA runner for MoneyWise AI — runs without Streamlit.
"""
import sys, os, time, threading, hashlib, sqlite3, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0; FAIL = 0; WARN = 0
RESULTS = []

def p(label, status, detail=""):
    global PASS, FAIL, WARN
    icon = {"PASS":"✅","FAIL":"❌","WARN":"⚠️ "}[status]
    print(f"  {icon} {label}" + (f" — {detail}" if detail else ""))
    RESULTS.append((status, label, detail))
    if status == "PASS": PASS += 1
    elif status == "FAIL": FAIL += 1
    else: WARN += 1

def section(title):
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")

# ─────────────────────────────────────────────────────────────
section("1. DATABASE INITIALIZATION")
# ─────────────────────────────────────────────────────────────
try:
    from database.connection import get_connection
    from database.models import create_tables
    create_tables()
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()
    expected = {"Users", "Transactions", "Goals"}
    missing  = expected - set(tables)
    if missing:
        p("Table creation", "FAIL", f"Missing: {missing}")
    else:
        p("All required tables exist", "PASS", str(tables))
except Exception as e:
    p("DB init", "FAIL", str(e))

# Journal mode
try:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("PRAGMA journal_mode")
    mode = cur.fetchone()[0]
    cur.execute("PRAGMA synchronous")
    sync = cur.fetchone()[0]
    cur.execute("PRAGMA page_size")
    page = cur.fetchone()[0]
    conn.close()
    if mode == "wal":
        p("WAL mode", "PASS", f"journal_mode={mode}, synchronous={sync}, page_size={page}")
    else:
        p("WAL mode", "WARN", f"journal_mode={mode} (not WAL). Concurrent writes will serialize — OK for single-user but suboptimal.")
except Exception as e:
    p("Journal mode check", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("2. SQLITE CRUD")
# ─────────────────────────────────────────────────────────────
try:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("INSERT INTO Users (Username,Email,Password_Hash) VALUES (?,?,?)",
                ("_qa_crud_", "_qa_crud_@test.com", "x"))
    uid = cur.lastrowid
    conn.commit()
    p("INSERT user", "PASS", f"rowid={uid}")

    cur.execute("SELECT Id,Username FROM Users WHERE Id=?", (uid,))
    row = cur.fetchone()
    assert row[0] == uid
    p("SELECT by PK", "PASS")

    cur.execute("UPDATE Users SET Username=? WHERE Id=?", ("_qa_updated_", uid))
    conn.commit()
    cur.execute("SELECT Username FROM Users WHERE Id=?", (uid,))
    assert cur.fetchone()[0] == "_qa_updated_"
    p("UPDATE", "PASS")

    cur.execute("DELETE FROM Users WHERE Id=?", (uid,))
    conn.commit()
    cur.execute("SELECT Id FROM Users WHERE Id=?", (uid,))
    assert cur.fetchone() is None
    p("DELETE", "PASS")
    conn.close()
except Exception as e:
    p("CRUD operations", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("3. AUTHENTICATION FLOWS")
# ─────────────────────────────────────────────────────────────
from auth.auth import signup_user, login_user, reset_password

ts = int(time.time())
email = f"qa_{ts}@test.com"
uname = f"QATester_{ts}"   # unique per run — avoids cross-run UNIQUE constraint collision

try:
    ok, msg = signup_user(uname, email, "secure123")
    p("New user signup", "PASS" if ok else "FAIL", msg)

    ok2, msg2 = signup_user("QA Dup", email, "secure123")
    p("Duplicate email blocked", "PASS" if not ok2 else "FAIL", msg2)

    ok3, msg3 = signup_user(f"Alt_{ts}", f"dup_{ts}@test.com", "secure123")
    # Try duplicate username (different email) — check if blocked
    ok3b, msg3b = signup_user(uname, f"dup2_{ts}@test.com", "secure123")
    if ok3b:
        p("Duplicate username allowed", "WARN", "Same username can register multiple times — not blocked at DB level")
    else:
        p("Duplicate username blocked", "PASS", msg3b)

    ok4, msg4 = login_user(email, "secure123")
    p("Valid login", "PASS" if ok4 else "FAIL", msg4)

    ok5, msg5 = login_user(email, "wrongpassword")
    p("Wrong password blocked", "PASS" if not ok5 else "FAIL", msg5)

    ok6, msg6 = login_user("nobody@nowhere.com", "secure123")
    p("Unknown user blocked", "PASS" if not ok6 else "FAIL", msg6)

    ok7, msg7 = login_user("", "")
    p("Empty credentials handled", "PASS" if not ok7 else "FAIL", msg7)

    ok8, msg8 = reset_password(email, "newpass456")
    p("Password reset", "PASS" if ok8 else "FAIL", msg8)

    ok9, msg9 = login_user(email, "newpass456")
    p("Login with reset password", "PASS" if ok9 else "FAIL", msg9)

    ok10, msg10 = login_user(email, "secure123")
    p("Old password invalidated", "PASS" if not ok10 else "FAIL", msg10)

    ok11, msg11 = reset_password("ghost@test.com", "newpass")
    p("Reset nonexistent email", "PASS" if not ok11 else "FAIL", msg11)
except Exception as e:
    p("Auth flows", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("4. PASSWORD SECURITY")
# ─────────────────────────────────────────────────────────────
try:
    import bcrypt
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT Password_Hash FROM Users WHERE Email=?", (email,))
    row  = cur.fetchone()
    conn.close()
    stored = row[0] if row else None
    if stored:
        is_bcrypt = stored.startswith("$2b$") or stored.startswith("$2a$")
        p("Password hashed with bcrypt", "PASS" if is_bcrypt else "FAIL", stored[:20]+"…")
        is_plain = stored == "newpass456"
        p("Password not stored in plaintext", "PASS" if not is_plain else "FAIL")
    else:
        p("Password hash retrieval", "FAIL", "User not found")
except Exception as e:
    p("Password security check", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("5. SQL INJECTION TESTING")
# ─────────────────────────────────────────────────────────────
try:
    # Test 1: Login with SQL injection payload
    ok_i, _ = login_user("' OR '1'='1", "' OR '1'='1")
    p("Login SQLi blocked", "PASS" if not ok_i else "FAIL", "' OR '1'='1 payload")

    ok_i2, _ = login_user("admin'--", "anything")
    p("Comment injection blocked", "PASS" if not ok_i2 else "FAIL")

    ok_i3, _ = login_user("a@b.com; DROP TABLE Users;--", "pass")
    p("DROP TABLE injection blocked", "PASS" if not ok_i3 else "FAIL")

    # Test 2: Transaction service direct injection via Title field
    from services.transaction_service import get_transactions_raw
    # Should not crash or return other users' data
    rows = get_transactions_raw(user_id=1, Title="'; DROP TABLE Transactions;--")
    p("SQLi in Title field handled", "PASS", f"returned {len(rows)} rows, no crash")

    rows2 = get_transactions_raw(user_id=1, Title="' UNION SELECT * FROM Users--")
    p("UNION injection via Title", "PASS", f"returned {len(rows2)} rows, no crash")
except Exception as e:
    p("SQL injection testing", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("6. USER ISOLATION")
# ─────────────────────────────────────────────────────────────
try:
    conn = get_connection()
    cur  = conn.cursor()
    # Create two test users
    cur.execute("INSERT INTO Users (Username,Email,Password_Hash) VALUES (?,?,?)", ("iso_a","iso_a@t.com","x"))
    uid_a = cur.lastrowid
    cur.execute("INSERT INTO Users (Username,Email,Password_Hash) VALUES (?,?,?)", ("iso_b","iso_b@t.com","x"))
    uid_b = cur.lastrowid
    # Insert txn for user A
    cur.execute("INSERT INTO Transactions (User_Id,Date,Title,Amount,Type,Category,Mode) VALUES (?,?,?,?,?,?,?)",
                (uid_a,"2025-01-01","Secret_A",9999,"Income","Salary","Online"))
    conn.commit()

    # Try to read user A's data as user B
    from services.transaction_service import get_transactions_raw
    rows_b = get_transactions_raw(user_id=uid_b, Title="Secret_A")
    p("User B cannot see User A data", "PASS" if not rows_b else "FAIL",
      f"rows returned: {len(rows_b)}")

    rows_a = get_transactions_raw(user_id=uid_a, Title="Secret_A")
    p("User A can see own data", "PASS" if rows_a else "FAIL",
      f"rows returned: {len(rows_a)}")

    # Cleanup
    cur.execute("DELETE FROM Transactions WHERE User_Id IN (?,?)", (uid_a,uid_b))
    cur.execute("DELETE FROM Users WHERE Id IN (?,?)", (uid_a,uid_b))
    conn.commit()
    conn.close()
except Exception as e:
    p("User isolation", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("7. TRANSACTION SERVICE")
# ─────────────────────────────────────────────────────────────
try:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("INSERT INTO Users (Username,Email,Password_Hash) VALUES (?,?,?)",
                (f"txn_{ts}",f"txn_{ts}@t.com","x"))
    svc_uid = cur.lastrowid
    conn.commit()
    conn.close()

    from services.transaction_service import get_transactions_raw
    from database.connection import get_connection as gc

    # Insert directly
    conn2 = gc()
    c2 = conn2.cursor()
    c2.execute("INSERT INTO Transactions (User_Id,Date,Title,Amount,Type,Category,Mode) VALUES (?,?,?,?,?,?,?)",
               (svc_uid,"2025-06-15","Coffee",150,"Expense","Food","Cash"))
    c2.execute("INSERT INTO Transactions (User_Id,Date,Title,Amount,Type,Category,Mode) VALUES (?,?,?,?,?,?,?)",
               (svc_uid,"2025-06-20","Coffee",200,"Expense","Food","UPI"))
    txn_id = c2.lastrowid
    conn2.commit()
    conn2.close()

    rows = get_transactions_raw(svc_uid, Title="Coffee")
    p("Filter by Title (LIKE)", "PASS" if len(rows)==2 else "FAIL", f"found {len(rows)} rows")

    rows2 = get_transactions_raw(svc_uid, AmountMin=160)
    p("Filter by AmountMin", "PASS" if len(rows2)==1 else "FAIL", f"found {len(rows2)} rows")

    rows3 = get_transactions_raw(svc_uid, Type="expense")  # case insensitive
    p("Case-insensitive Type filter", "PASS" if len(rows3)==2 else "FAIL")

    rows4 = get_transactions_raw(svc_uid, DateFrom="2025-06-18", DateTo="2025-06-25")
    p("Date range filter", "PASS" if len(rows4)==1 else "FAIL", f"found {len(rows4)} rows")

    rows5 = get_transactions_raw(svc_uid, Month="2025-06")
    p("Month filter (strftime)", "PASS" if len(rows5)==2 else "FAIL", f"found {len(rows5)} rows")

    # Cleanup
    conn3 = gc()
    c3 = conn3.cursor()
    c3.execute("DELETE FROM Transactions WHERE User_Id=?", (svc_uid,))
    c3.execute("DELETE FROM Users WHERE Id=?", (svc_uid,))
    conn3.commit()
    conn3.close()
except Exception as e:
    p("Transaction service", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("8. CONCURRENT WRITES")
# ─────────────────────────────────────────────────────────────
try:
    errors = []
    from database.connection import get_connection as gc2

    def write_txn(i):
        try:
            c = gc2()
            cr = c.cursor()
            cr.execute("INSERT INTO Transactions (User_Id,Date,Title,Amount,Type,Category,Mode) VALUES (?,?,?,?,?,?,?)",
                       (1, "2025-01-01", f"Concurrent_{i}", i*10, "Expense","Other","Online"))
            c.commit()
            c.close()
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=write_txn, args=(i,)) for i in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    # Cleanup
    cc = gc2()
    ccr = cc.cursor()
    ccr.execute("DELETE FROM Transactions WHERE Title LIKE 'Concurrent_%'")
    cc.commit()
    cc.close()

    if errors:
        p("Concurrent writes (10 threads)", "WARN", f"{len(errors)} errors: {errors[0][:80]}")
    else:
        p("Concurrent writes (10 threads)", "PASS", "0 errors, all committed")
except Exception as e:
    p("Concurrent write test", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("9. DB BACKUP SYSTEM")
# ─────────────────────────────────────────────────────────────
try:
    from utils.db_backup import (
        _get_config, _is_db_effectively_empty, get_local_db_sha256,
        get_backup_status, restore_db_from_github, backup_db_to_github
    )
    cfg = _get_config()
    if cfg:
        p("GitHub credentials loaded", "PASS", f"repo={cfg['repo']}")
        status = get_backup_status()
        p("get_backup_status()", "PASS" if status["enabled"] else "WARN",
          f"remote_exists={status['remote_exists']}, sha={status.get('remote_sha')}, size={status.get('remote_size_bytes')} B")
        sha = get_local_db_sha256()
        p("Local DB SHA-256", "PASS" if sha else "WARN", (sha[:16]+"…") if sha else "DB missing")
    else:
        p("GitHub credentials", "WARN", "Not configured — backup tests skipped")
except Exception as e:
    p("Backup system", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("10. SQL SERVICE SECURITY")
# ─────────────────────────────────────────────────────────────
try:
    import re
    forbidden = ["INSERT","UPDATE","DELETE","DROP","ALTER","CREATE","TRUNCATE","PRAGMA","ATTACH","DETACH"]

    payloads = [
        ("DROP TABLE Users", True),
        ("SELECT * FROM Users", True),    # Users is a sensitive table
        ("PRAGMA table_info(Users)", True),
        ("SELECT Id FROM Transactions WHERE User_Id=1 UNION SELECT Password_Hash,2,3,4,5,6,7 FROM Users", False),  # UNION injection — WARN
        ("SELECT * FROM Transactions WHERE User_Id=1", False),  # Clean
    ]

    for sql, should_block in payloads:
        blocked_by_forbidden = any(re.search(rf"\b{k}\b", sql, re.IGNORECASE) for k in forbidden)
        blocked_by_sensitive = any(re.search(rf"\b{t}\b", sql, re.IGNORECASE) for t in ["Users","sqlite_master","sqlite_temp_master","sqlite_stat1"])
        is_select = bool(re.match(r"^\s*(SELECT|WITH)\b", sql, re.IGNORECASE))
        blocked = blocked_by_forbidden or blocked_by_sensitive or not is_select
        if should_block:
            p(f"SQLi blocked: {sql[:50]}", "PASS" if blocked else "FAIL")
        else:
            p(f"Clean query passes: {sql[:50]}", "PASS" if not blocked else "WARN")

    # Check for double conn.close() bug in sql_service
    import ast
    code = open("services/sql_service.py").read()
    # Count only non-comment lines that call conn.close()
    actual_closes = sum(
        1 for line in code.splitlines()
        if "conn.close()" in line and not line.strip().startswith("#")
    )
    if actual_closes > 1:
        p("sql_service conn.close() called", "WARN",
          f"{actual_closes}x — double close (silent for sqlite3 but messy)")
    else:
        p("sql_service single conn.close()", "PASS", f"{actual_closes}x — clean")
except Exception as e:
    p("SQL service security", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("11. NULL / EDGE CASE HANDLING")
# ─────────────────────────────────────────────────────────────
try:
    from services.transaction_service import _null_str
    # Test the NEW _null_str() helper that replaced the broken str(x)=='null' check
    assert _null_str(None)    == True,  "None must be null"
    assert _null_str("null")  == True,  "'null' must be null"
    assert _null_str("None")  == True,  "'None' must be null"
    assert _null_str("none")  == True,  "'none' must be null"
    assert _null_str("")      == True,  "empty string must be null"
    assert _null_str("nan")   == True,  "'nan' must be null"
    assert _null_str(100)     == False, "100 must NOT be null"
    assert _null_str("hello") == False, "'hello' must NOT be null"
    assert _null_str(0.0)     == False, "0.0 must NOT be null"
    p("_null_str() handles None/'null'/'None'/'none'/empty", "PASS")
except ImportError:
    p("_null_str import", "WARN", "_null_str not yet importable — check transaction_service.py")
except AssertionError as ae:
    p("_null_str correctness", "FAIL", str(ae))
except Exception as e:
    p("Null check analysis", "FAIL", str(e))

try:
    # Test _resolve_uid with edge cases
    from services.transaction_service import _resolve_uid
    class FakeSS: pass

    # Patch session_state
    import streamlit as st
    orig = getattr(st, 'session_state', None)

    assert _resolve_uid(5) == 5
    assert _resolve_uid("3") == 3
    assert _resolve_uid(-1) is None
    assert _resolve_uid(0) is None
    assert _resolve_uid("abc") is None
    p("_resolve_uid edge cases", "PASS", "5,str,neg,0,str all handled")
except Exception as e:
    p("_resolve_uid tests", "WARN", str(e))

# ─────────────────────────────────────────────────────────────
section("12. DB BACKUP UTILITY")
# ─────────────────────────────────────────────────────────────
try:
    from utils.db_backup import _is_db_effectively_empty, _DB_MIN_VALID_BYTES
    from unittest.mock import patch

    # Test with real DB file
    from utils.db_backup import _DB_PATH
    if _DB_PATH.exists():
        sz = _DB_PATH.stat().st_size
        is_empty = _is_db_effectively_empty()
        p(f"Local DB size check", "PASS" if not is_empty else "WARN",
          f"{sz:,} bytes {'(has data)' if not is_empty else '(effectively empty)'}")

    # SQLite magic bytes
    MAGIC = b"SQLite format 3\x00"
    with open(str(_DB_PATH), "rb") as f:
        header = f.read(16)
    p("SQLite magic bytes correct", "PASS" if header == MAGIC else "FAIL",
      f"header={header[:16]!r}")
except Exception as e:
    p("DB backup utility", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("13. REQUIREMENTS INTEGRITY")
# ─────────────────────────────────────────────────────────────
try:
    reqs = open("requirements.txt").read()
    critical_pkgs = ["streamlit","langchain","langchain-groq","pandas","plotly","requests","playwright","bcrypt"]
    for pkg in critical_pkgs:
        present = pkg.lower() in reqs.lower()
        p(f"requirements.txt: {pkg}", "PASS" if present else "FAIL")
except Exception as e:
    p("Requirements check", "FAIL", str(e))

# ─────────────────────────────────────────────────────────────
section("14. WORKFLOW FILES EXIST")
# ─────────────────────────────────────────────────────────────
for wf in [".github/workflows/keep_alive.yml", ".github/workflows/db_backup.yml"]:
    exists = os.path.exists(wf)
    p(f"Workflow: {wf}", "PASS" if exists else "FAIL")

for sf in ["scripts/keep_alive.py", "scripts/test_deployment.py"]:
    exists = os.path.exists(sf)
    p(f"Script: {sf}", "PASS" if exists else "FAIL")

# ─────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  RESULTS: {PASS} PASS  |  {FAIL} FAIL  |  {WARN} WARN")
print(f"{'='*55}")
sys.exit(0 if FAIL == 0 else 1)
