from __future__ import annotations

"""
ui/transactions_page.py

Transactions tab — two sections:
  A) Transaction table with year/month filter, search, category/type filters, metrics, CSV download
  B) AI Finance Assistant chat with separate history (txn_chat_history)
     Suggestions fill the text box instead of auto-executing.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import os
from typing import Any, Optional, Dict, List

from database.connection import get_connection
from utils.logger import get_logger
from utils.formatters import format_indian_currency, format_indian_shorthand

logger = get_logger(__name__)


# ── DB helpers ────────────────────────────────────────────────────────────────

def _load_transactions(user_id: int, month: str = None) -> pd.DataFrame:
    conn = get_connection()
    cur  = conn.cursor()
    if month:
        cur.execute(
            "SELECT Id, Date, Type, Category, Title, Amount, Mode "
            "FROM Transactions WHERE User_Id=? AND strftime('%Y-%m', Date)=? "
            "ORDER BY Date DESC",
            (user_id, month),
        )
    else:
        cur.execute(
            "SELECT Id, Date, Type, Category, Title, Amount, Mode "
            "FROM Transactions WHERE User_Id=? ORDER BY Date DESC",
            (user_id,),
        )
    rows = cur.fetchall()
    conn.close()

    cols = ["ID", "Date", "Type", "Category", "Description", "Amount", "Mode"]
    if not rows:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(rows, columns=cols)
    df["#"]    = range(1, len(df) + 1)
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%d-%m-%Y")
    return df[["#", "Date", "Type", "Category", "Description", "Amount", "Mode"]]


def _get_month_options(user_id: int):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT DISTINCT strftime('%Y-%m', Date) FROM Transactions "
        "WHERE User_Id=? ORDER BY 1 DESC",
        (user_id,),
    )
    rows = [r[0] for r in cur.fetchall() if r[0]]
    conn.close()
    return rows


# ── Agent call ─────────────────────────────────────────────────────────────────

def _invoke_agent(query: str) -> str:
    import os
    import streamlit as st
    
    is_guest = st.session_state.get("is_guest", False)
    if is_guest:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        # Check environment first, then streamlit secrets
        api_key = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY", "")
        if not api_key:
            return (
                "**NVIDIA API key not set.**\n\n"
                "To enable Demo Mode AI, please add `NVIDIA_API_KEY` to your environment variables "
                "or your Streamlit Secrets dashboard."
            )
    else:
        # For real users, we check st.session_state (from sidebar) or environment
        api_key = st.session_state.get("api_key") or os.getenv("GROQ_API_KEY", "")
        if not api_key:
            return (
                "**Groq API key not set.**\n\n"
                "Please expand the **AI API Key** section in the sidebar and paste your Groq key.\n"
                "Get a free key at [console.groq.com](https://console.groq.com)."
            )

    from agents.moneywise_agent import get_agent
    try:
        agent = get_agent()
        chat_history = []
        history = st.session_state.get("txn_chat_history", [])
        for msg in history[-6:]:
            chat_history.append((msg["role"], msg["content"]))

        # Use st.status to show real-time agent progress
        with st.status("AI is working...", expanded=True) as status:
            from langchain_community.callbacks import StreamlitCallbackHandler
            st_callback = StreamlitCallbackHandler(st.container())
            response = agent.invoke({
                "input": query,
                "chat_history": chat_history,
            }, {"callbacks": [st_callback]})
            status.update(label="Complete!", state="complete", expanded=False)
            
        return response.get("output", "Sorry, I couldn't process that.")

    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        err = str(e)
        if "failed_generation" in err or "Failed to call a function" in err or "ValidationError" in err:
            try:
                agent = get_agent()
                response = agent.invoke({"input": query, "chat_history": []})
                return response.get("output", "Sorry, I couldn't process that.")
            except Exception:
                return "The AI had trouble calling a tool. Try rephrasing your request."
        
        logger.error(f"AI Agent Error: {err}\n{err_trace}")
        return "I'm having trouble processing that request right now. Please try again or rephrase your question."


# ── Constants ─────────────────────────────────────────────────────────────────

CHAT_SUGGESTIONS = [
    "How much did I spend this month?",
    "Add ₹500 for dinner at Zomato",
    "Show my income history",
    "Update transaction 12 category to Travel",
    "Delete last transaction",
    "Show expenses above ₹5000",
    "Biggest expense in 2026?",
    "Total spent on Groceries?",
]

CATEGORY_OPTIONS = [
    "All", "Food", "Transport", "Shopping", "Rent", "Entertainment",
    "Salary", "Freelance", "Bills", "Healthcare", "Investments", "Travel",
    "Groceries", "Education", "Subscription", "Stationery", "Other",
]


# ── Main renderer ─────────────────────────────────────────────────────────────

def render_transactions_page():
    user_id = st.session_state.get("user_id")

    st.markdown("""
    <div class="mw-page-title">Transactions</div>
    <div class="mw-page-subtitle">Manage your income & expenses and chat with your AI assistant.</div>
    <div class="mw-page-subtitle">Scroll down to chat with your AI assistant.</div>
    """, unsafe_allow_html=True)

    # ── A: Transaction Table ──────────────────────────────────────
    st.markdown("<div class='mw-section-header'>Transaction History</div>",
                unsafe_allow_html=True)

    month_options = _get_month_options(user_id)
    if not month_options:
        st.info("No transactions found. Use the AI assistant below to add some!")
    else:
        # Year → Months mapping
        year_to_months = {}
        for ym in month_options:
            y, m = ym.split("-")
            if y not in year_to_months:
                year_to_months[y] = []
            year_to_months[y].append(m)

        years = sorted(year_to_months.keys(), reverse=True)

        c_year, c_month, c_search, c_cat, c_type = st.columns([1, 1.5, 2, 1.5, 1])

        with c_year:
            sel_year = st.selectbox("Year", years, key="txn_year_sel")

        with c_month:
            available_months = sorted(year_to_months[sel_year], reverse=True)
            cur_m = date.today().strftime("%m")
            def_m_idx = available_months.index(cur_m) if cur_m in available_months else 0

            def _m_label(m_str):
                return datetime.strptime(f"2000-{m_str}-01", "%Y-%m-%d").strftime("%B")

            sel_m_str = st.selectbox("Month", available_months,
                                     index=def_m_idx, format_func=_m_label,
                                     key="txn_month_sel")

        sel_month = f"{sel_year}-{sel_m_str}"

        with c_search:
            search = st.text_input("Search", placeholder="e.g. Zomato, Rent...",
                                   key="txn_search")
        with c_cat:
            cat_f = st.selectbox("Category", CATEGORY_OPTIONS, key="txn_cat_f")
        with c_type:
            type_f = st.selectbox("Type", ["All", "Income", "Expense"], key="txn_type_f")

        df = _load_transactions(user_id, sel_month)

        if not df.empty:
            if search:
                df = df[df["Description"].str.contains(search, case=False, na=False)]
            if cat_f != "All":
                df = df[df["Category"].str.lower() == cat_f.lower()]
            if type_f != "All":
                df = df[df["Type"] == type_f]

        # Metrics
        if not df.empty:
            inc  = df[df["Type"] == "Income"]["Amount"].sum()
            exp  = df[df["Type"] == "Expense"]["Amount"].sum()
            sav  = inc - exp
            cnt  = len(df)
            sav_color = "var(--green)" if sav >= 0 else "var(--red)"

            m1, m2, m3, m4 = st.columns(4)
            _metric(m1, "💰", format_indian_shorthand(inc),  "Income",  "var(--green)")
            _metric(m2, "💸", format_indian_shorthand(exp),  "Expenses", "var(--red)")
            _metric(m3, "📈", format_indian_shorthand(sav),  "Net Savings", sav_color)
            _metric(m4, "🔢", str(cnt),          "Transactions", "var(--accent)")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            def style_type(val):
                if val == "Income":
                    return "color:#10b981;font-weight:600;"
                if val == "Expense":
                    return "color:#ef4444;font-weight:600;"
                return ""

            styled = (
                df.style
                .map(style_type, subset=["Type"])
                .format({"Amount": lambda x: format_indian_currency(x)})
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv,
                               f"transactions_{sel_month}.csv", "text/csv",
                               key="txn_dl")
        else:
            st.info("No transactions match the current filters.")

    # ── B: AI Chat ────────────────────────────────────────────────
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='mw-section-header'>AI Finance Assistant</div>",
                unsafe_allow_html=True)

    # Suggestion buttons — minimal ghost style, fill textbox
    st.markdown("<div style='font-size:13px;color:var(--text-secondary);margin-bottom:8px;'>Try asking:</div>",
                unsafe_allow_html=True)

    st.markdown("<div class='mw-ghost-btn'>", unsafe_allow_html=True)
    cols_per_row = 4
    for i in range(0, len(CHAT_SUGGESTIONS), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(CHAT_SUGGESTIONS):
                suggestion = CHAT_SUGGESTIONS[idx]
                if col.button(suggestion, key=f"txn_sugg_{idx}", use_container_width=True):
                    st.session_state.txn_chat_input = suggestion
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Initialize chat history
    if "txn_chat_history" not in st.session_state:
        st.session_state.txn_chat_history = []

    # Display chat history
    if not st.session_state.txn_chat_history:
        st.markdown("""
        <div style="text-align:center;padding:28px 0;color:var(--text-muted);">
            <div style="font-size:28px;">💬</div>
            <div style="font-size:14px;margin-top:6px;">
                No messages yet. Type below or click a suggestion.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.txn_chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Deferred clear flag to reset input cleanly BEFORE rendering
    if st.session_state.pop("clear_txn_input", False):
        st.session_state.txn_chat_input = ""

    form_col, clear_col = st.columns([22, 1])
    with form_col:
        with st.form(key="txn_chat_form", clear_on_submit=False):
            in_col, btn_col = st.columns([20, 1], vertical_alignment="center")
            with in_col:
                user_msg = st.text_input(
                    "chat_input_label",
                    key="txn_chat_input",
                    label_visibility="collapsed",
                    placeholder="Ask anything about your finances...",
                )
            with btn_col:
                send_clicked = st.form_submit_button("\u27a4", use_container_width=True)

    with clear_col:
        if st.button("\U0001f5d1\ufe0f", key="txn_clear_chat", use_container_width=True):
            st.session_state.txn_chat_history = []
            st.session_state.clear_txn_input = True
            st.rerun()

    if send_clicked and user_msg:
        st.session_state.txn_chat_history.append({"role": "user", "content": user_msg})
        reply = _invoke_agent(user_msg)
        st.session_state.txn_chat_history.append({"role": "assistant", "content": reply})
        st.session_state.clear_txn_input = True
        st.rerun()


# ── Metric card helper ────────────────────────────────────────────────────────

def _metric(col, icon: str, value: str, label: str, color: str = "var(--accent)"):
    with col:
        st.markdown(f"""
        <div class="mw-metric">
            <div class="mw-metric-icon">{icon}</div>
            <div class="mw-metric-value" style="color:{color};">
                {value}
            </div>
            <div class="mw-metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)
