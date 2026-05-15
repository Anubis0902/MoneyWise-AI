from __future__ import annotations

"""
services/transaction_service.py

LangChain @tool functions for Transactions CRUD + savings calculation.
Refactored for security, user isolation, and production readiness.
"""

from datetime import date
from typing import Optional, List, Union
from langchain_core.tools import tool
import streamlit as st

from database.connection import get_connection
from utils.type_helpers import _infer_type
from utils.logger import get_logger
from utils.backup_trigger import trigger_backup_if_needed

logger = get_logger(__name__)


def _null_str(val) -> bool:
    """Returns True if val should be treated as absent/null.

    Handles: Python None, strings 'null', 'none', 'nan', empty string.
    Fixes: str(None)='None' != 'null' — the old check silently missed Python None.
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
ALLOWED_TRANSACTION_FIELDS = {
    "Title": "Title",
    "Amount": "Amount",
    "Category": "Category",
    "Mode": "Mode",
    "Type": "Type",
    "Date": "Date"
}

# ── Internal helper (not a tool) ────────────────────────────────────────────

def get_transactions_raw(
    user_id: int,
    Title: str = None, Amount: float = None, Type: str = None, 
    Category: str = None, Mode: str = None,
    Date: str = None, Month: str = None, Year: str = None, 
    DateFrom: str = None, DateTo: str = None,
    AmountMin: float = None, AmountMax: float = None,
) -> List[tuple]:
    """
    Low-level query builder for the Transactions table.
    Enforces user isolation via user_id.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT Id, Date, Title, Amount, Type, Category, Mode FROM Transactions WHERE User_Id = ?"
        values = [user_id]

        if Date:
            query += " AND Date = ?"
            values.append(Date)
        if Month:
            query += " AND strftime('%Y-%m', Date) = ?"
            values.append(Month)
        if Year:
            query += " AND strftime('%Y', Date) = ?"
            values.append(Year)
        if DateFrom:
            query += " AND Date >= ?"
            values.append(DateFrom)
        if DateTo:
            query += " AND Date <= ?"
            values.append(DateTo)
        if Title:
            query += " AND LOWER(Title) LIKE LOWER(?)"
            values.append(f"%{Title}%")
        if Amount is not None:
            query += " AND Amount = ?"
            values.append(Amount)
        if AmountMin is not None:
            query += " AND Amount >= ?"
            values.append(AmountMin)
        if AmountMax is not None:
            query += " AND Amount <= ?"
            values.append(AmountMax)
        if Type:
            query += " AND LOWER(Type) = LOWER(?)"
            values.append(Type)
        if Category:
            query += " AND LOWER(Category) LIKE LOWER(?)"
            values.append(f"%{Category}%")
        if Mode:
            query += " AND LOWER(Mode) LIKE LOWER(?)"
            values.append(f"%{Mode}%")

        cursor.execute(query, values)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        logger.error(f"Error in get_transactions_raw: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()


# ── Public @tool functions ───────────────────────────────────────────────────

@tool(return_direct=True)
def add_transaction(
    Title: str,
    Amount: Optional[Union[float, str]] = None,
    Category: str = "Other",
    Type: str = None,
    Mode: str = "Online",
    user_id: Optional[Union[int, str]] = None,
) -> str:
    """
    Add a new financial transaction.
    
    Args:
        Title: Name of transaction.
        Amount: Transaction amount (numeric).
        Type: 'Income' or 'Expense'.
        Category: Category name.
        Mode: Payment mode.
        user_id: Provided automatically or via session.
    """
    u_id = _resolve_uid(user_id)
    if not u_id:
        return "Error: Authentication required."

    if Amount is None:
        return "Error: Amount is required."

    resolved_type = _infer_type(Type, Category)
    if not resolved_type:
        return "Error: Could not determine transaction type (Income/Expense)."

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO Transactions (User_Id, Date, Title, Amount, Type, Category, Mode)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (u_id, date.today().isoformat(), Title, Amount, resolved_type, Category, Mode or "Online"),
        )
        conn.commit()
        trigger_backup_if_needed()
        return "Transaction added successfully."
    except Exception as e:
        logger.error(f"Failed to add transaction for user {u_id}: {e}")
        return f"Error: Failed to save transaction."
    finally:
        if 'conn' in locals():
            conn.close()


@tool
def get_transactions(
    Title: str = None,
    Amount: Optional[Union[float, str]] = None,
    Type: str = None,
    Category: str = None,
    Mode: str = None,
    Date: str = None,
    Month: str = None,
    Year: str = None,
    DateFrom: str = None,
    DateTo: str = None,
    AmountMin: Optional[Union[float, str]] = None,
    AmountMax: Optional[Union[float, str]] = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
    """Retrieve filtered transactions for the current user."""
    if _null_str(Amount):   Amount    = None
    if _null_str(AmountMin): AmountMin = None
    if _null_str(AmountMax): AmountMax = None
    try:
        if Amount is not None: Amount = float(Amount)
        if AmountMin is not None: AmountMin = float(AmountMin)
        if AmountMax is not None: AmountMax = float(AmountMax)
    except ValueError:
        return "Error: Amount fields must be numeric."
    u_id = _resolve_uid(user_id)
    if not u_id:
        return "Error: Authentication required."

    rows = get_transactions_raw(
        user_id=u_id, Title=Title, Amount=Amount, Type=Type, Category=Category, Mode=Mode,
        Date=Date, Month=Month, Year=Year, DateFrom=DateFrom, DateTo=DateTo,
        AmountMin=AmountMin, AmountMax=AmountMax
    )

    if not rows:
        return "No transactions found."

    lines = [f"Found {len(rows)} transaction(s):"]
    for r in rows:
        # Expected: Id(0), Date(1), Title(2), Amount(3), Type(4), Category(5), Mode(6)
        amt = float(r[3]) if r[3] is not None else 0.0
        lines.append(f"  ID {r[0]} | {r[1]} | {r[2]} | ₹{amt:,.2f} | {r[4]} | {r[5]} | {r[6]}")
    return "\n".join(lines)


@tool(return_direct=True)
def delete_transactions(
    Title: str = None,
    Amount: Optional[Union[float, str]] = None,
    Type: str = None,
    Category: str = None,
    Mode: str = None,
    Id: Optional[Union[int, str]] = None,
    Ids: Optional[List[int]] = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
    """
    Delete transactions securely ensuring user ownership.
    
    CRITICAL RULES:
    - If multiple matches are found by name/title, this tool returns a list of IDs.
      DO NOT call this tool again. Instead, show the list to the user and ask them
      which specific ID they want to delete.
    - To delete a specific record: provide Id=<integer>.
    - To delete multiple specific records: provide Ids=[id1, id2, ...].
    - NEVER use this tool to delete by name alone if multiple records exist.
    """
    if _null_str(Amount): Amount = None
    if Amount is not None:
        try: Amount = float(Amount)
        except ValueError: return "Error: Amount must be a valid number."
    
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
                cursor.execute(f"DELETE FROM Transactions WHERE Id IN ({placeholders}) AND User_Id=?", (*valid_ids, u_id))
                conn.commit()
                trigger_backup_if_needed()
                return f"{cursor.rowcount} transactions deleted successfully."
            
        resolved_id = _resolve_id(Id)

        if resolved_id is not None:
            cursor.execute("DELETE FROM Transactions WHERE Id=? AND User_Id=?", (resolved_id, u_id))
            if cursor.rowcount > 0:
                conn.commit()
                trigger_backup_if_needed()
                return "Transaction deleted successfully."
            return "Error: Transaction not found or access denied."

        rows = get_transactions_raw(u_id, Title, Amount, Type, Category, Mode)
        if not rows:
            return "No matching transactions found."
        
        if len(rows) == 1:
            t_id = rows[0][0]
            cursor.execute("DELETE FROM Transactions WHERE Id=? AND User_Id=?", (t_id, u_id))
            conn.commit()
            trigger_backup_if_needed()
            return "Transaction deleted successfully."
        
        # Multiple matches — STOP and ask user. Never auto-delete.
        table = "⚠️ Multiple transactions found with that name. Please tell me which **ID** to delete:\n\n"
        table += "| ID | Title | Amount | Date |\n"
        table += "|---|---|---|---|\n"
        for r in rows:
            table += f"| {r[0]} | {r[2]} | ₹{r[3]:,.0f} | {r[1]} |\n"
        return table

    except Exception as e:
        logger.error(f"Error deleting transaction for user {u_id}: {e}")
        return "Error: Deletion failed."
    finally:
        if 'conn' in locals():
            conn.close()


@tool(return_direct=True)
def update_transactions(
    field: str,
    new_value: Union[str, float],
    Title: str = None,
    Amount: float = None,
    Category: str = None,
    Mode: str = None,
    Type: str = None,
    Id: Optional[Union[int, str]] = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
    """Update transactions using whitelist validation and user isolation."""
    u_id = _resolve_uid(user_id)
    if not u_id:
        return "Error: Authentication required."

    resolved_id = _resolve_id(Id)

    # Task 2: Whitelist validation
    clean_field = ALLOWED_TRANSACTION_FIELDS.get(field)
    if not clean_field:
        return f"Error: Field '{field}' is not editable. Allowed: {list(ALLOWED_TRANSACTION_FIELDS.keys())}"

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if resolved_id is not None:
            # Use parameterized query for both value AND ensured user isolation
            cursor.execute(
                f"UPDATE Transactions SET {clean_field} = ? WHERE Id = ? AND User_Id = ?",
                (new_value, resolved_id, u_id)
            )
            if cursor.rowcount > 0:
                conn.commit()
                trigger_backup_if_needed()
                return "Transaction updated successfully."
            return "Error: Transaction not found or access denied."

        rows = get_transactions_raw(u_id, Title, Amount, Type, Category, Mode)
        if not rows:
            return "No matching transactions found."
        
        if len(rows) == 1:
            t_id = rows[0][0]
            cursor.execute(
                f"UPDATE Transactions SET {clean_field} = ? WHERE Id = ? AND User_Id = ?",
                (new_value, t_id, u_id)
            )
            conn.commit()
            trigger_backup_if_needed()
            return "Transaction updated successfully."

        # Multiple matches — STOP and ask user. Never auto-update.
        table = "⚠️ Multiple transactions found with that name. Please tell me which **ID** to update:\n\n"
        table += "| ID | Title | Amount | Date |\n"
        table += "|---|---|---|---|\n"
        for r in rows:
            table += f"| {r[0]} | {r[2]} | ₹{r[3]:,.0f} | {r[1]} |\n"
        return table

    except Exception as e:
        logger.error(f"Update failed for user {u_id}: {e}")
        return "Error: Update failed."
    finally:
        if 'conn' in locals():
            conn.close()


@tool
def get_savings(
    Month: str = None,
    DateFrom: str = None,
    DateTo: str = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
    """Calculate savings securely with user isolation."""
    u_id = _resolve_uid(user_id)
    if not u_id:
        return "Error: Authentication required."
        
    try:
        where = "User_Id = ?"
        values = [u_id]

        if Month:
            where += " AND strftime('%Y-%m', Date) = ?"
            values.append(Month)
        if DateFrom:
            where += " AND Date >= ?"
            values.append(DateFrom)
        if DateTo:
            where += " AND Date <= ?"
            values.append(DateTo)

        query = f"""
        SELECT 
            COUNT(*),
            COALESCE(SUM(CASE WHEN Type='Income'  THEN Amount END), 0) -
            COALESCE(SUM(CASE WHEN Type='Expense' THEN Amount END), 0)
        FROM Transactions
        WHERE {where}
        """

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, values)
        count, savings = cursor.fetchone()
        
        if count == 0:
            return "No transactions found for the given period."

        label = f"for {Month}" if Month else f"from {DateFrom} to {DateTo}" if DateFrom else "total"
        return f"Your {label} savings are ₹{savings:,.2f}"

    except Exception as e:
        logger.error(f"Savings calculation failed for user {u_id}: {e}")
        return "Error: Could not calculate savings."
    finally:
        if 'conn' in locals():
            conn.close()
