"""
prompts/sql_prompt.py

ChatPromptTemplate and DB schema string for the
generate_and_execute_sql tool.
"""

from langchain_core.prompts import ChatPromptTemplate

# ── Database schema exposed to the LLM ─────────────────────────────────────

schema = """
Table: Transactions

Columns:
- Id       INTEGER
- User_Id  INTEGER
- Title    TEXT
- Amount   REAL
- Category TEXT
- Type     TEXT
- Mode     TEXT
- Date     TEXT

Table: Goals

Columns:
- Id            INTEGER
- User_Id       INTEGER
- Title         TEXT
- Started_At    TEXT
- Deadline      TEXT
- Target_Amount INTEGER
- Saved_Amount  INTEGER
- Status        TEXT
"""

# ── Prompt template ─────────────────────────────────────────────────────────

template3 = ChatPromptTemplate.from_template(
    """
You are a SQLite expert.

Database Schema:
{schema}

Current User ID: {user_id}

Rules:
- Only generate SQLite SQL
- Only use SELECT queries
- Do not use DELETE, DROP, UPDATE, ALTER
- ALWAYS filter by User_Id = {user_id} in every query to ensure privacy
- Return ONLY SQL query
- No markdown

User Question:
{question}
"""
)
