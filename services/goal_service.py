from __future__ import annotations

"""
services/goal_service.py

LangChain @tool functions for Goals CRUD.
Refactored for security, user isolation, and production readiness.
"""

from datetime import date
from typing import Optional, List, Union
from langchain_core.tools import tool
import streamlit as st

from database.connection import get_connection
from utils.logger import get_logger
from utils.backup_trigger import trigger_backup_if_needed

logger = get_logger(__name__)


def _null_str(val) -> bool:
    """Returns True if val should be treated as absent/null.
    Handles: Python None, 'null', 'none', 'nan', empty string.
    """
    if val is None:
        return True
    return str(val).strip().lower() in ("null", "none", "nan", "")


def _resolve_uid(user_id) -> Optional[int]:
    """Coerce user_id to int, falling back to session_state. Handles str/None/'None'/null."""
    if user_id is not None:
        try:
            uid = int(user_id)
            if uid > 0:
                return uid
        except (ValueError, TypeError):
            pass
    try:
        uid = st.session_state.get('user_id')
        return int(uid) if uid is not None else None
    except Exception:
        return None


def _resolve_id(id_val) -> Optional[int]:
    """Coerce Id to int. Returns None if invalid/null."""
    if id_val is None:
        return None
    try:
        val = int(id_val)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None

# ── Whitelist for updates ──────────────────────────────────────────────────
ALLOWED_GOAL_FIELDS = {
    "Title": "Title",
    "Started_At": "Started_At",
    "Deadline": "Deadline",
    "Target_Amount": "Target_Amount",
    "Saved_Amount": "Saved_Amount",
    "Status": "Status"
}

# ── Internal helper (not a tool) ────────────────────────────────────────────

def get_goals_raw(
    user_id: int,
    Title: str = None,
    Started_at: str = None,
    Deadline: str = None,
    Target_amount: float = None,
    Saved_amount: float = None,
    Status: str = None,
) -> List[tuple]:
    """
    Low-level query builder for the Goals table.
    Enforces user isolation via user_id.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT Id, Title, Started_At, Deadline, Target_Amount, Saved_Amount, Status FROM Goals WHERE User_Id = ?"
        values = [user_id]

        if Title:
            query += " AND LOWER(Title) LIKE LOWER(?)"
            values.append(f"%{Title}%")
        if Started_at:
            query += " AND Started_At LIKE ?"
            values.append(f"%{Started_at}%")
        if Deadline:
            query += " AND Deadline LIKE ?"
            values.append(f"%{Deadline}%")
        if Target_amount is not None:
            query += " AND Target_Amount = ?"
            values.append(Target_amount)
        if Saved_amount is not None:
            query += " AND Saved_Amount = ?"
            values.append(Saved_amount)
        if Status:
            query += " AND LOWER(Status) = LOWER(?)"
            values.append(Status)

        cursor.execute(query, values)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        logger.error(f"Error in get_goals_raw for user {user_id}: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


# ── Public @tool functions ───────────────────────────────────────────────────

@tool(return_direct=True)
def create_goal(
    Title: str,
    Target_amount: Union[float, str],
    Deadline: str = None,
    Saved_amount: Optional[Union[float, str]] = 0,
    Status: str = "Active",
    user_id: Optional[Union[int, str]] = None,
) -> str:
    """Create a new financial savings goal."""
    if _null_str(Target_amount): return "Error: Target_amount is required."
    if _null_str(Saved_amount):  Saved_amount = 0
    try:
        Target_amount = float(Target_amount)
        if Saved_amount is not None: Saved_amount = float(Saved_amount)
    except ValueError:
        return "Error: Amount fields must be numeric."
    u_id = _resolve_uid(user_id)
    if not u_id:
        return "Error: Authentication required."
        
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Goals (User_Id, Title, Started_At, Deadline, Target_Amount, Saved_Amount, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (u_id, Title, date.today().isoformat(), Deadline, Target_amount, Saved_amount, Status),
        )
        conn.commit()
        trigger_backup_if_needed()
        return "Goal created successfully."
    except Exception as e:
        logger.error(f"Failed to create goal for user {u_id}: {e}")
        return "Error: Failed to save goal."
    finally:
        if 'conn' in locals():
            conn.close()


@tool
def get_goals(
    Title: str = None,
    Started_at: str = None,
    Deadline: str = None,
    Target_amount: Optional[Union[float, str]] = None,
    Saved_amount: Optional[Union[float, str]] = None,
    Status: str = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
    """Retrieve goals for the current user."""
    if _null_str(Target_amount): Target_amount = None
    if _null_str(Saved_amount):  Saved_amount  = None
    try:
        if Target_amount is not None: Target_amount = float(Target_amount)
        if Saved_amount is not None: Saved_amount = float(Saved_amount)
    except ValueError:
        return "Error: Amount fields must be numeric."
    u_id = _resolve_uid(user_id)
    if not u_id:
        return "Error: Authentication required."

    rows = get_goals_raw(u_id, Title, Started_at, Deadline, Target_amount, Saved_amount, Status)
    if not rows:
        return "No goals found."

    lines = [f"Found {len(rows)} goal(s):"]
    for r in rows:
        # Id(0), Title(1), Started_At(2), Deadline(3), Target_Amount(4), Saved_Amount(5), Status(6)
        deadline_str = f" | Deadline: {r[3]}" if r[3] else ""
        target_amt = float(r[4]) if r[4] is not None else 0.0
        saved_amt = float(r[5]) if r[5] is not None else 0.0
        lines.append(
            f"  ID {r[0]} | {r[1]} | Started: {r[2]}{deadline_str} "
            f"| Target: ₹{target_amt:,.2f} | Saved: ₹{saved_amt:,.2f} | {r[6]}"
        )
    return "\n".join(lines)


@tool(return_direct=True)
def delete_goal(
    Title: str = None,
    Id: Optional[Union[int, str]] = None,
    Ids: Optional[List[int]] = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
    """
    Delete a goal securely ensuring user ownership.
    
    CRITICAL RULES:
    - If multiple matches are found by name/title, this tool returns a list of IDs.
      DO NOT call this tool again. Instead, show the list to the user and ask them
      which specific ID they want to delete.
    - To delete a specific goal: provide Id=<integer>.
    - To delete multiple specific goals: provide Ids=[id1, id2, ...].
    - NEVER delete by name alone if multiple records exist.
    """
    u_id = _resolve_uid(user_id)
    if not u_id:
        return "Error: Authentication required."

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if Ids and isinstance(Ids, list) and len(Ids) > 0:
            valid_ids = [int(i) for i in Ids if str(i).isdigit() or isinstance(i, int)]
            if valid_ids:
                placeholders = ",".join("?" * len(valid_ids))
                cursor.execute(f"DELETE FROM Goals WHERE Id IN ({placeholders}) AND User_Id=?", (*valid_ids, u_id))
                conn.commit()
                trigger_backup_if_needed()
                return f"{cursor.rowcount} goals deleted successfully."

        resolved_id = _resolve_id(Id)

        if resolved_id is not None:
            cursor.execute("DELETE FROM Goals WHERE Id=? AND User_Id=?", (resolved_id, u_id))
            if cursor.rowcount > 0:
                conn.commit()
                trigger_backup_if_needed()
                return "Goal deleted successfully."
            return "Error: Goal not found or access denied."

        rows = get_goals_raw(u_id, Title=Title)
        if not rows:
            return "No matching goals found."
        
        if len(rows) == 1:
            g_id = rows[0][0]
            cursor.execute("DELETE FROM Goals WHERE Id=? AND User_Id=?", (g_id, u_id))
            conn.commit()
            trigger_backup_if_needed()
            return "Goal deleted successfully."

        # Multiple matches — STOP and ask user. Never auto-delete.
        table = "⚠️ Multiple goals found with that name. Please tell me which **ID** to delete:\n\n"
        table += "| ID | Title | Target | Deadline |\n"
        table += "|---|---|---|---|\n"
        for r in rows:
            table += f"| {r[0]} | {r[1]} | ₹{r[4]:,.0f} | {r[3] or '—'} |\n"
        return table

    except Exception as e:
        logger.error(f"Error deleting goal for user {u_id}: {e}")
        return "Error: Deletion failed."
    finally:
        if 'conn' in locals():
            conn.close()


@tool(return_direct=True)
def update_goals(
    field: str,
    new_value: Union[str, float],
    Title: str = None,
    Id: Optional[Union[int, str]] = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
    """Update goals with whitelist validation and incremental Saved_Amount support."""
    u_id = _resolve_uid(user_id)
    if not u_id:
        return "Error: Authentication required."

    resolved_id = _resolve_id(Id)
    clean_field = ALLOWED_GOAL_FIELDS.get(field)
    if not clean_field:
        return f"Error: Field '{field}' is not editable. Allowed: {list(ALLOWED_GOAL_FIELDS.keys())}"

    try:
        conn = get_connection()
        cursor = conn.cursor()

        def _perform_update(goal_id):
            if clean_field == "Saved_Amount" and str(new_value).startswith("+"):
                inc = float(str(new_value).lstrip("+"))
                cursor.execute(
                    "UPDATE Goals SET Saved_Amount = Saved_Amount + ? WHERE Id = ? AND User_Id = ?",
                    (inc, goal_id, u_id)
                )
            else:
                cursor.execute(
                    f"UPDATE Goals SET {clean_field} = ? WHERE Id = ? AND User_Id = ?",
                    (new_value, goal_id, u_id)
                )
            return cursor.rowcount > 0

        if resolved_id is not None:
            if _perform_update(resolved_id):
                conn.commit()
                trigger_backup_if_needed()
                return "Goal updated successfully."
            return "Error: Goal not found or access denied."

        rows = get_goals_raw(u_id, Title=Title)
        if not rows:
            return "No matching goals found."
        
        if len(rows) == 1:
            if _perform_update(rows[0][0]):
                conn.commit()
                trigger_backup_if_needed()
                return "Goal updated successfully."
            return "Error: Update failed."

        # Multiple matches — STOP and ask user. Never auto-update.
        table = "⚠️ Multiple goals found with that name. Please tell me which **ID** to update:\n\n"
        table += "| ID | Title | Saved | Target |\n"
        table += "|---|---|---|---|\n"
        for r in rows:
            table += f"| {r[0]} | {r[1]} | ₹{r[5]:,.0f} | ₹{r[4]:,.0f} |\n"
        return table

    except Exception as e:
        logger.error(f"Update failed for user {u_id}: {e}")
        return "Error: Update failed."
    finally:
        if 'conn' in locals():
            conn.close()
