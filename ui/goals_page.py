"""
ui/goals_page.py

Goals tab — summary metrics, Plotly progress chart, goal detail cards,
and AI chat with separate history (goal_chat_history).
Suggestions fill text box instead of auto-executing.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from database.connection import get_connection
from utils.logger import get_logger
from utils.formatters import format_indian_currency, format_indian_shorthand
import os

logger = get_logger(__name__)


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
        history = st.session_state.get("goal_chat_history", [])
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
        if "401" in err or "Invalid API Key" in err or "authentication" in err.lower():
            return "⚠️ **Invalid API Key.** Please check your Groq or NVIDIA API key in the sidebar or environment settings."

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
    "Create a goal for MacBook worth ₹1.2L",
    "Show my current goals",
    "Add ₹10k to Emergency Fund",
    "Update MacBook goal deadline to Dec 2026",
    "Delete goal ID 3",
    "Which goals are near completion?",
    "Set status of 'Goa Trip' to Paused",
    "What is my total saved amount?",
]

# ── Colour map ────────────────────────────────────────────────────────────────
STATUS_COLOR = {
    "Completed": "#10b981",
    "Active":    "#3b82f6",
    "Failed":    "#ef4444",
    "Paused":    "#f59e0b",
}
STATUS_ICON = {"Completed": "✅", "Active": "🎯", "Failed": "❌", "Paused": "⏸️"}

# ── Data loader ───────────────────────────────────────────────────────────────

def _load_goals(user_id: int) -> pd.DataFrame:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT Id, Title, Started_At, Deadline, Target_Amount, Saved_Amount, Status "
        "FROM Goals WHERE User_Id=? ORDER BY Status, Deadline",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=[
        "Id", "Title", "Started_At", "Deadline",
        "Target_Amount", "Saved_Amount", "Status"
    ])

def _fmt_date(d):
    if not d or pd.isna(d):
        return "—"
    try:
        return pd.to_datetime(d).strftime("%d %b %Y")
    except Exception:
        return str(d)

def _pct(saved, target):
    if not target or target == 0:
        return 0.0
    return min(round(saved / target * 100, 1), 100.0)

# ── Plotly progress chart ─────────────────────────────────────────────────────

def _goal_progress_chart(df: pd.DataFrame):
    df = df.copy()
    df["Progress"] = df.apply(lambda r: _pct(r["Saved_Amount"], r["Target_Amount"]), axis=1)
    df["Saved_Fmt"] = df["Saved_Amount"].apply(lambda x: format_indian_currency(x))
    df["Target_Fmt"] = df["Target_Amount"].apply(lambda x: format_indian_currency(x))
    df = df.sort_values("Progress", ascending=True)

    colors = ["#ef4444" if s == "Failed" else "#10b981" for s in df["Status"]]

    theme = st.session_state.get("theme", "dark")
    bg = "#111111" if theme == "dark" else "#ffffff"
    text_col = "#94a3b8" if theme == "dark" else "#64748b"
    grid_col = "#222222" if theme == "dark" else "#e2e8f0"

    fig = go.Figure()

    # Background bars (100%)
    fig.add_trace(go.Bar(
        x=[100] * len(df), y=df["Title"],
        orientation="h",
        marker_color="rgba(128,128,128,0.08)",
        showlegend=False,
        hoverinfo="skip",
    ))

    # Progress bars
    fig.add_trace(go.Bar(
        x=df["Progress"], y=df["Title"],
        orientation="h",
        marker_color=colors,
        text=[f"{p:.1f}%" for p in df["Progress"]],
        textposition="inside",
        textfont=dict(color="white", size=12, family="Inter"),
        customdata=df[["Saved_Fmt", "Target_Fmt", "Status"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Progress: %{x:.1f}%<br>"
            "Saved: %{customdata[0]}<br>"
            "Target: %{customdata[1]}<br>"
            "Status: %{customdata[2]}<extra></extra>"
        ),
        showlegend=False,
    ))

    fig.update_layout(
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        font_color=text_col,
        font_family="Inter",
        barmode="overlay",
        margin=dict(l=10, r=80, t=20, b=10),
        height=max(280, len(df) * 46 + 60),
        xaxis=dict(
            range=[0, 110], ticksuffix="%",
            gridcolor=grid_col, zerolinecolor=grid_col,
        ),
        yaxis=dict(gridcolor=grid_col),
    )
    return fig

# ── Main renderer ─────────────────────────────────────────────────────────────

def render_goals_page():
    user_id = st.session_state.get("user_id")

    st.markdown("""
    <div class="mw-page-title">Savings Goals</div>
    <div class="mw-page-subtitle">Track and manage your financial milestones.</div>
    <div class="mw-page-subtitle">Scroll down to chat with your AI assistant.</div>
    """, unsafe_allow_html=True)

    df = _load_goals(user_id)

    if df.empty:
        st.info("No goals yet! Use the AI assistant below to create one.\n\n"
                "Try: *\"Create a goal for MacBook worth ₹120000 by December 2026\"*")
        _render_chat_section()
        return

    # ── Summary metrics ───────────────────────────────────────────
    total_goals  = len(df)
    completed    = (df["Status"] == "Completed").sum()
    active       = (df["Status"] == "Active").sum()
    paused       = (df["Status"] == "Paused").sum()
    total_target = df["Target_Amount"].sum()
    total_saved  = df["Saved_Amount"].sum()
    overall_pct  = _pct(total_saved, total_target)

    m1, m2, m3, m4, m5 = st.columns(5)
    for col, icon, val, label, color in [
        (m1, "📋", str(total_goals),      "Total Goals",    "var(--accent)"),
        (m2, "✅", str(completed),         "Completed",      "var(--green)"),
        (m3, "🎯", str(active),            "Active",         "var(--purple)"),
        (m4, "⏸️", str(paused),            "Paused",         "var(--orange)"),
        (m5, "📊", f"{overall_pct:.1f}%",  "Overall",        "var(--orange)"),
    ]:
        with col:
            st.markdown(f"""
            <div class="mw-metric">
                <div class="mw-metric-icon">{icon}</div>
                <div class="mw-metric-value" style="color:{color};">{val}</div>
                <div class="mw-metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([2, 2, 3])
    with fc1:
        status_filter = st.selectbox("Status", ["All","Active","Completed","Paused","Failed"],
                                     key="goal_status_f")
    with fc2:
        search = st.text_input("Search", placeholder="Goal name...", key="goal_search")
    with fc3:
        sort_by = st.selectbox("Sort by", ["Progress ↓", "Progress ↑", "Target ↓", "Name A→Z"],
                               key="goal_sort")

    fdf = df.copy()
    fdf["Progress"] = fdf.apply(lambda r: _pct(r["Saved_Amount"], r["Target_Amount"]), axis=1)
    if status_filter != "All":
        fdf = fdf[fdf["Status"] == status_filter]
    if search:
        fdf = fdf[fdf["Title"].str.contains(search, case=False, na=False)]

    sort_map = {
        "Progress ↓": ("Progress", False),
        "Progress ↑": ("Progress", True),
        "Target ↓":   ("Target_Amount", False),
        "Name A→Z":   ("Title", True),
    }
    col_s, asc_s = sort_map[sort_by]
    fdf = fdf.sort_values(col_s, ascending=asc_s)

    if fdf.empty:
        st.info("No goals match your current filters.")
        _render_chat_section()
        return

    # ── Progress Chart ────────────────────────────────────────────
    st.markdown("<div class='mw-section-header'>Progress Overview</div>", unsafe_allow_html=True)
    fig = _goal_progress_chart(fdf)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Legend row ────────────────────────────────────────────────
    leg_cols = st.columns(4)
    for col, (status, color) in zip(leg_cols, STATUS_COLOR.items()):
        icon = STATUS_ICON.get(status, "●")
        cnt  = (df["Status"] == status).sum()
        col.markdown(
            f"<div style='display:flex;align-items:center;gap:6px;font-size:13px;"
            f"color:{color};'>"
            f"<div style='width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0;'></div>"
            f"{icon} {status}: <b>{cnt}</b></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Goal Cards ────────────────────────────────────────────────
    st.markdown("<div class='mw-section-header'>Goal Details</div>", unsafe_allow_html=True)

    rows_list = list(fdf.iterrows())
    for i in range(0, len(rows_list), 2):
        cols = st.columns(2, gap="medium")
        for j, col in enumerate(cols):
            if i + j >= len(rows_list):
                break
            _, row = rows_list[i + j]
            _render_goal_card_native(col, row)

    # ── AI Chat ───────────────────────────────────────────────────
    _render_chat_section()


def _render_chat_section():
    """AI chat section with separate goal_chat_history."""
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='mw-section-header'>AI Finance Assistant</div>",
                unsafe_allow_html=True)

    # Suggestion buttons — minimal ghost style
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
                if col.button(suggestion, key=f"goal_sugg_{idx}", use_container_width=True):
                    st.session_state.goal_chat_input = suggestion
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Initialize
    if "goal_chat_history" not in st.session_state:
        st.session_state.goal_chat_history = []

    # Display
    if not st.session_state.goal_chat_history:
        st.markdown("""
        <div style="text-align:center;padding:28px 0;color:var(--text-muted);">
            <div style="font-size:28px;">💬</div>
            <div style="font-size:14px;margin-top:6px;">
                No messages yet. Type below or click a suggestion.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.goal_chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Deferred clear flag to reset input cleanly BEFORE rendering
    if st.session_state.pop("clear_goal_input", False):
        st.session_state.goal_chat_input = ""

    form_col, clear_col = st.columns([22, 1])
    with form_col:
        with st.form(key="goal_chat_form", clear_on_submit=False):
            in_col, btn_col = st.columns([20, 1], vertical_alignment="center")
            with in_col:
                user_msg = st.text_input(
                    "goal_chat_input_label",
                    key="goal_chat_input",
                    label_visibility="collapsed",
                    placeholder="Ask anything about your goals or finances...",
                )
            with btn_col:
                send_clicked = st.form_submit_button("\u27a4", use_container_width=True)

    with clear_col:
        if st.button("\U0001f5d1\ufe0f", key="goal_clear_chat", use_container_width=True):
            st.session_state.goal_chat_history = []
            st.session_state.clear_goal_input = True
            st.rerun()


    if send_clicked and user_msg:
        st.session_state.goal_chat_history.append({"role": "user", "content": user_msg})
        reply = _invoke_agent(user_msg)
        st.session_state.goal_chat_history.append({"role": "assistant", "content": reply})
        st.session_state.clear_goal_input = True
        st.rerun()


def _render_goal_card_native(col, row):
    status  = row["Status"]
    color   = STATUS_COLOR.get(status, "#3b82f6")
    icon    = STATUS_ICON.get(status, "●")
    pct     = row["Progress"]
    saved   = int(row["Saved_Amount"])
    target  = int(row["Target_Amount"])
    remain  = max(target - saved, 0)
    near    = pct >= 80 and status == "Active"

    with col:
        with st.container(border=True):
            # Title row
            tc, pc = st.columns([3, 1])
            with tc:
                st.markdown(
                    f"<div style='font-size:16px;font-weight:700;color:var(--text-primary);"
                    f"margin-bottom:2px;'>{icon} {row['Title']}</div>",
                    unsafe_allow_html=True,
                )
                badge_bg  = f"rgba({','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.12)"
                near_html = (" <span style='font-size:10px;background:rgba(245,158,11,0.12);"
                             "color:#f59e0b;border:1px solid rgba(245,158,11,0.25);"
                             "border-radius:10px;padding:1px 6px;'>Near Goal</span>"
                             if near else "")
                st.markdown(
                    f"<span style='background:{badge_bg};color:{color};"
                    f"border:1px solid {color}40;border-radius:10px;"
                    f"font-size:11px;font-weight:600;padding:2px 8px;'>{status}</span>"
                    f"{near_html}",
                    unsafe_allow_html=True,
                )
            with pc:
                st.markdown(
                    f"<div style='text-align:right;'>"
                    f"<div style='font-size:22px;font-weight:800;color:{color};'>{pct:.1f}%</div>"
                    f"<div style='font-size:10px;color:var(--text-muted);text-transform:uppercase;'>done</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # Progress bar
            bar_color = "#ef4444" if status == "Failed" else "#10b981"
            st.markdown(
                f"""
                <div style="
                    background: var(--border);
                    border-radius: 8px;
                    height: 8px;
                    overflow: hidden;
                    margin: 10px 0 14px 0;
                ">
                    <div style="
                        background: {bar_color};
                        width: {pct}%;
                        height: 100%;
                        border-radius: 8px;
                        transition: width 0.6s ease;
                    "></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Amount row
            a1, a2, a3 = st.columns(3)
            a1.metric("Saved",     format_indian_shorthand(saved))
            a2.metric("Remaining", format_indian_shorthand(remain))
            a3.metric("Target",    format_indian_shorthand(target))

            # Date row
            d1, d2 = st.columns(2)
            d1.caption(f"Started: {_fmt_date(row['Started_At'])}")
            d2.caption(f"Deadline: {_fmt_date(row['Deadline'])}")
