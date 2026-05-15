# 🛠️ MoneyWise AI — Tools Documentation

All AI-callable tools are decorated with LangChain's `@tool` decorator and registered in `agents/moneywise_agent.py`. They are split across three service files.

---

## 📁 File Structure

```
agents/
└── moneywise_agent.py       ← Agent assembler & system prompt
services/
├── transaction_service.py   ← Tools: add, get, update, delete transactions + savings
├── goal_service.py          ← Tools: create, get, update, delete goals
└── sql_service.py           ← Tool: natural language → SQL analytics
```

---

## 🤖 Agent — `agents/moneywise_agent.py`

This file assembles the LangChain `AgentExecutor`. It is **not a tool itself**, but it wires all tools to the LLM.

### Key Points
- Uses **ChatGroq** (`llama-3.3-70b-versatile`) for authenticated users
- Uses **ChatNVIDIA** (`meta/llama-3.3-70b-instruct`) for guest/demo users
- `max_iterations=5` prevents infinite tool-call loops
- Today's date is injected into the system prompt at runtime

### Registered Tools
```python
_TOOLS = [
    generate_and_execute_sql,
    add_transaction,
    delete_transactions,
    update_transactions,
    get_transactions,
    get_savings,
    create_goal,
    delete_goal,
    update_goals,
    get_goals,
]
```

### `get_agent()` Function
```python
def get_agent():
    """
    Returns a fresh AgentExecutor using the correct API KEY.
    For demo users, uses ChatNVIDIA and NVIDIA_API_KEY.
    For real users, uses ChatGroq and GROQ_API_KEY.
    """
    import streamlit as st
    is_guest = st.session_state.get("is_guest", False)

    if is_guest:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        api_key = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY", "")
        llm = ChatNVIDIA(model="meta/llama-3.3-70b-instruct", api_key=api_key, temperature=0)
    else:
        from langchain_groq import ChatGroq
        api_key = st.session_state.get("api_key") or os.getenv("GROQ_API_KEY", "")
        llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key, temperature=0)

    agent = create_tool_calling_agent(llm, _TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=_TOOLS, verbose=True, max_iterations=5)
```

---

## 💸 Transaction Tools — `services/transaction_service.py`

### Helper: `_null_str(val)`
Utility that detects "empty" values — handles Python `None`, strings like `"null"`, `"none"`, `"nan"`, and `""`.

### Helper: `_resolve_uid(user_id)`
Coerces `user_id` to int. Falls back to `st.session_state['user_id']` if not passed by the agent.

### Helper: `_resolve_id(id_val)`
Coerces an `Id` argument to int. Returns `None` if invalid or ≤ 0.

### Helper: `get_transactions_raw(...)`
Internal (non-tool) query builder. Builds a parameterized `SELECT` query with optional filters and enforces `User_Id` isolation.

---

### Tool 1: `add_transaction`

```python
@tool(return_direct=True)
def add_transaction(
    Title: str,
    Amount: Optional[Union[float, str]] = None,
    Category: str = "Other",
    Type: str = None,
    Mode: str = "Online",
    user_id: Optional[Union[int, str]] = None,
) -> str:
```

**Purpose:** Adds a new financial transaction to the database.

**How it works:**
1. Resolves user from session state
2. Infers `Type` (Income/Expense) from Category if not provided, using `_infer_type()`
3. Inserts a row into `Transactions` with today's date
4. Triggers a GitHub backup after write

**Returns:** `"Transaction added successfully."` or an error string.

**Agent intent triggers:** `spent`, `bought`, `paid`, `received`

---

### Tool 2: `get_transactions`

```python
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
```

**Purpose:** Retrieves filtered transactions for the current user.

**How it works:**
1. Sanitizes amount fields (null-string guards + float conversion)
2. Calls `get_transactions_raw()` with all filters
3. Formats results as a numbered list with ID, date, title, amount, type, category, mode

**Returns:** A formatted string list of transactions or `"No transactions found."`.

**Agent intent triggers:** `show`, `list`, `fetch`, `get`, `history`

---

### Tool 3: `delete_transactions`

```python
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
```

**Purpose:** Deletes transactions securely with user ownership enforcement.

**How it works (priority order):**
1. **Bulk by IDs:** If `Ids=[1,2,3]` is given, deletes all in one query
2. **Single by ID:** If `Id=5` is given, deletes that specific row
3. **By filters:** Searches matching rows — if exactly 1 found, deletes it
4. **Disambiguation:** If multiple matches found, returns a Markdown table asking the user to pick an ID. **Never auto-deletes.**

**Returns:** Success string, error string, or a disambiguation table (⚠️ prefix).

**Agent intent triggers:** `delete`, `remove`

---

### Tool 4: `update_transactions`

```python
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
```

**Purpose:** Updates a specific field of a transaction.

**Security:** Uses a whitelist (`ALLOWED_TRANSACTION_FIELDS`) to prevent SQL injection via the field name:
```python
ALLOWED_TRANSACTION_FIELDS = {
    "Title", "Amount", "Category", "Mode", "Type", "Date"
}
```

**How it works:**
1. Validates `field` against whitelist
2. If `Id` given → direct update
3. If filters given → find match; if 1 row → update; if multiple → disambiguation table

**Returns:** `"Transaction updated successfully."` or error/disambiguation.

**Agent intent triggers:** `update`, `change`, `edit`

---

### Tool 5: `get_savings`

```python
@tool
def get_savings(
    Month: str = None,
    DateFrom: str = None,
    DateTo: str = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
```

**Purpose:** Calculates net savings (Income − Expense) for a given period.

**How it works:**
1. Builds a `SUM(CASE WHEN Type='Income' ...)` SQL query
2. Subtracts expense sum from income sum
3. Returns a human-readable savings string

**Returns:** `"Your total savings are ₹X,XX,XXX.XX"` or error.

**Agent intent triggers:** `savings`, `how much saved`, `net balance`

---

## 🎯 Goal Tools — `services/goal_service.py`

### Helper: `get_goals_raw(...)`
Internal query builder for the `Goals` table with user isolation and optional filters (Title, Deadline, Status, etc.).

---

### Tool 6: `create_goal`

```python
@tool(return_direct=True)
def create_goal(
    Title: str,
    Target_amount: Union[float, str],
    Deadline: str = None,
    Saved_amount: Optional[Union[float, str]] = 0,
    Status: str = "Active",
    user_id: Optional[Union[int, str]] = None,
) -> str:
```

**Purpose:** Creates a new savings goal in the `Goals` table.

**How it works:**
1. Validates `Target_amount` is provided and numeric
2. Sets `Started_At` to today's date automatically
3. Inserts the goal and triggers a backup

**Returns:** `"Goal created successfully."` or error string.

**Agent intent triggers:** `create goal`, `save for`, `I want to save`

---

### Tool 7: `get_goals`

```python
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
```

**Purpose:** Retrieves goals for the current user with optional filters.

**Returns:** A formatted list showing: ID, Title, Started date, Deadline, Target, Saved amount, Status.

**Agent intent triggers:** `show goals`, `list goals`, `my goals`

---

### Tool 8: `delete_goal`

```python
@tool(return_direct=True)
def delete_goal(
    Title: str = None,
    Id: Optional[Union[int, str]] = None,
    Ids: Optional[List[int]] = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
```

**Purpose:** Deletes a goal securely.

**How it works (same priority as `delete_transactions`):**
1. Bulk delete by `Ids` list
2. Single delete by `Id`
3. Filter by Title → if unique, delete; if multiple, return disambiguation table

**Returns:** Success/error or disambiguation table.

---

### Tool 9: `update_goals`

```python
@tool(return_direct=True)
def update_goals(
    field: str,
    new_value: Union[str, float],
    Title: str = None,
    Id: Optional[Union[int, str]] = None,
    user_id: Optional[Union[int, str]] = None,
) -> str:
```

**Purpose:** Updates a goal field. Supports **incremental** `Saved_Amount` updates.

**Whitelist:**
```python
ALLOWED_GOAL_FIELDS = {
    "Title", "Started_At", "Deadline",
    "Target_Amount", "Saved_Amount", "Status"
}
```

**Special feature — Incremental save:**  
If `field="Saved_Amount"` and `new_value="+5000"`, it adds ₹5000 to the existing saved amount instead of replacing it:
```python
if clean_field == "Saved_Amount" and str(new_value).startswith("+"):
    cursor.execute("UPDATE Goals SET Saved_Amount = Saved_Amount + ? WHERE ...")
```

**Agent intent triggers:** `update goal`, `add to savings`, `change deadline`

---

## 🔍 SQL Analytics Tool — `services/sql_service.py`

### Tool 10: `generate_and_execute_sql`

```python
@tool
def generate_and_execute_sql(
    question: str,
    user_id: Optional[Union[int, str]] = None
):
```

**Purpose:** Converts a natural language question into a SQL query and executes it read-only.

**How it works:**
1. **LLM generates SQL** using a `ChatPromptTemplate` from `prompts/sql_prompt.py`
2. **Security Audit (4 Rules):**
   - **Rule A:** Blocks dangerous keywords: `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `PRAGMA`, `ATTACH`, `DETACH`
   - **Rule B:** Only allows queries starting with `SELECT` or `WITH`
   - **Rule C:** Blocks access to sensitive tables: `Users`, `sqlite_master`, etc.
   - **Rule D:** Force-injects `User_Id = X` if the LLM forgot to include it
3. **Executes** the sanitized query and returns results as a list of dicts

**Returns:** `{"query": ..., "status": "Success", "data": [...]}` or an error dict.

**Agent intent triggers:** `analytics`, `biggest`, `trend`, `compare`, `how much total`, `which category`

---

## 📊 Analytics Service — `services/analytics_service.py`

> These are **not AI tools** — they are Python functions called directly by the UI to render charts.

| Function | Description |
|---|---|
| `plot_income_vs_expense(year)` | Grouped bar chart — Income vs Expense per month |
| `plot_category_expense_donut(year, month)` | Donut pie chart — Expense breakdown by category |
| `plot_savings_trend(year)` | Line chart — Monthly savings trend |
| `plot_goal_progress()` | Horizontal bar chart — Goal % completion |

All functions:
- Accept optional `user_id`, falling back to session state
- Return a `matplotlib.figure.Figure` object (or `None` on error/empty data)
- Enforce user isolation at the database query level

---

## 🔒 Security Patterns Used Across All Tools

| Pattern | Implementation |
|---|---|
| **User Isolation** | Every SQL query includes `WHERE User_Id = ?` |
| **Whitelist Validation** | Only allowed field names can be updated |
| **Disambiguation** | Multiple-match writes return a table, never auto-act |
| **SQL Injection Prevention** | Parameterized queries + keyword blocklist for SQL tool |
| **Null-safe coercion** | `_null_str()`, `_resolve_uid()`, `_resolve_id()` helpers |
| **Backup on Write** | `trigger_backup_if_needed()` called after every write |
