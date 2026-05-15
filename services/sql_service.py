"""
services/sql_service.py

LangChain @tool for secure Text2SQL.
Implements multi-layer security to prevent SQL injection and data leakage.
"""

import re
from typing import Optional, Union
from langchain_core.tools import tool
import streamlit as st

from database.connection import get_connection
from prompts.sql_prompt import template3, schema
from utils.logger import get_logger

logger = get_logger(__name__)


def _resolve_uid(user_id) -> Optional[int]:
    """Coerce user_id to int, falling back to session_state."""
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

@tool
def generate_and_execute_sql(question: str, user_id: Optional[Union[int, str]] = None):
    """
    Generates and executes a read-only SQL query from a natural language question.
    Only allows SELECT queries and enforces user isolation.
    """
    from config import get_client
    client = get_client()

    u_id = _resolve_uid(user_id)
    if not u_id:
        return {"error": "Authentication required."}

    try:
        # 1. Generate SQL via LLM
        chain = template3 | client
        response = chain.invoke({
            "schema": schema,
            "question": question,
            "user_id": u_id,
        })

        sql_query = response.content.strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        # 2. Runtime Security Audit (Task 3)
        
        # Rule A: Block dangerous keywords anywhere in the query
        forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "PRAGMA", "ATTACH", "DETACH"]
        if any(re.search(rf"\b{k}\b", sql_query, re.IGNORECASE) for k in forbidden):
            logger.warning(f"Blocked dangerous SQL from user {u_id}: {sql_query}")
            return {"error": "Dangerous operation detected. Only read-only queries are allowed."}

        # Rule B: Strictly allow only SELECT or WITH
        if not re.match(r"^\s*(SELECT|WITH)\b", sql_query, re.IGNORECASE):
            return {"error": "Only SELECT queries are allowed."}

        # Rule C: Block access to sensitive tables (security boundary)
        sensitive_tables = ["Users", "sqlite_master", "sqlite_temp_master", "sqlite_stat1"]
        if any(re.search(rf"\b{t}\b", sql_query, re.IGNORECASE) for t in sensitive_tables):
            logger.warning(f"Blocked attempt to access sensitive table/system table by user {u_id}")
            return {"error": "Access to system tables or restricted data is forbidden."}


        # Rule D: Force User_Id check (fallback enforcement)
        # Even if the LLM forgot 'User_Id = X', we ensure the string exists in the query.
        # This is a heuristic; a more robust way would be a SQL parser, 
        # but for SQLite/LLM, this catches most leaks.
        if f"User_Id = {u_id}" not in sql_query and f"User_Id={u_id}" not in sql_query:
            # Attempt to inject it if it's missing (naive but helpful)
            if "WHERE" in sql_query.upper():
                sql_query = sql_query.replace("WHERE", f"WHERE User_Id = {u_id} AND")
            else:
                # Add WHERE before GROUP BY, ORDER BY, or at the end
                if "GROUP BY" in sql_query.upper():
                    sql_query = sql_query.replace("GROUP BY", f"WHERE User_Id = {u_id} GROUP BY")
                elif "ORDER BY" in sql_query.upper():
                    sql_query = sql_query.replace("ORDER BY", f"WHERE User_Id = {u_id} ORDER BY")
                else:
                    sql_query += f" WHERE User_Id = {u_id}"
            
        # 3. Execution
        conn = get_connection()
        cursor = conn.cursor()
        
        logger.info(f"Executing Text2SQL for user {u_id}: {sql_query}")
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
        if not cursor.description:
            return {"query": sql_query, "result": "Query executed successfully (no results)."}
            
        columns = [desc[0] for desc in cursor.description]
        # Note: conn.close() is handled in the finally block below

        formatted_rows = [dict(zip(columns, row)) for row in rows]

        if not formatted_rows:
            return {"query": sql_query, "status": "No records found.", "data": []}

        return {"query": sql_query, "status": "Success: Data retrieved.", "data": formatted_rows}

    except Exception as e:
        logger.error(f"Text2SQL error for user {u_id}: {e}")
        return {"error": f"Failed to execute analytical query."}
    finally:
        if 'conn' in locals():
            conn.close()
