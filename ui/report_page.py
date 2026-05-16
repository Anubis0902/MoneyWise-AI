"""
ui/report_page.py

Report Generation tab:
  - Full CSV export of all transactions
  - AI-powered monthly email report
    • Normal user  → shows registered email, current-month button
    • Demo profile → email input + historical month/year selector
"""

import calendar
from datetime import date

import pandas as pd
import streamlit as st

from database.connection import get_connection


def _load_all_transactions(user_id: int) -> pd.DataFrame:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT Id, Date, Type, Category, Title, Amount, Mode "
        "FROM Transactions WHERE User_Id=? ORDER BY Date DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["ID","Date","Type","Category","Description","Amount","Mode"])
    df["ID"]   = range(1, len(df)+1)
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%d-%m-%Y")
    return df


def render_report_page():
    user_id  = st.session_state.get("user_id")
    is_guest = st.session_state.get("is_guest", False)
    email    = st.session_state.get("email", "")

    st.markdown("""
    <div class="mw-page-title">📄 Report Generation</div>
    <div class="mw-page-subtitle">Download your data and receive AI-powered monthly reports by email.</div>
    """, unsafe_allow_html=True)

    # ── Section 1: CSV Export ─────────────────────────────────────
    st.markdown("<div class='mw-section-header'>📥 Export All Transactions</div>",
                unsafe_allow_html=True)

    df = _load_all_transactions(user_id)

    if df.empty:
        st.info("No transactions found to export yet.")
    else:
        c1, c2 = st.columns([3, 1])
        with c1:
            first = df["Date"].iloc[-1]
            last  = df["Date"].iloc[0]
            st.markdown(f"""
            <div style="font-size:14px;color:#94a3b8;line-height:2;">
                📊 <b style="color:#f0f4ff;">{len(df)}</b> transactions ready<br>
                📅 Range: <b style="color:#f0f4ff;">{first}</b> → <b style="color:#f0f4ff;">{last}</b>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.download_button(
                "⬇️ Download CSV",
                df.to_csv(index=False).encode("utf-8"),
                f"moneywise_{date.today()}.csv",
                "text/csv",
                key="full_csv_dl",
                use_container_width=True,
            )
        with st.expander("👁 Preview first 10 rows"):
            st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    # ── Section 2: Monthly AI Report ─────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='mw-section-header'>📧 Monthly AI Report</div>",
                unsafe_allow_html=True)

    if is_guest:
        _demo_report_section()
    else:
        _user_report_section(email)

    # ── Section 3: Info card ──────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="mw-card">
        <div style="font-size:15px;font-weight:700;margin-bottom:10px;">ℹ️ About AI Reports</div>
        <div style="font-size:13px;color:#94a3b8;line-height:1.9;">
            🤖 <b style="color:#f0f4ff;">AI Analysis</b> — The LLM reads your spending patterns
            and generates personalised insights and suggestions.<br>
            📎 <b style="color:#f0f4ff;">CSV Attachment</b> — Every email includes the month's
            transactions as a CSV file.<br>
            🔒 <b style="color:#f0f4ff;">Secure</b> — Sent via encrypted Gmail SMTP.
        </div>
    </div>
    """, unsafe_allow_html=True)


def _user_report_section(email: str):
    today    = date.today()
    days_left = calendar.monthrange(today.year, today.month)[1] - today.day
    month_name = today.strftime("%B %Y")

    st.markdown(f"""
    <div class="mw-card">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
            <div style="font-size:28px;">📧</div>
            <div>
                <div style="font-size:13px;color:#94a3b8;">Report destination</div>
                <div style="font-size:15px;font-weight:600;color:#3b82f6;">{email}</div>
            </div>
        </div>
        <div class="mw-alert-info">
            ℹ️ <b>{month_name}</b> report will auto-send at month end.
            <span style="color:#3b82f6;font-weight:600;">{days_left} day(s) remaining.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:13px;color:#94a3b8;margin:12px 0 6px;'>Send now:</div>",
                unsafe_allow_html=True)
    if st.button(f"📬 Send {month_name} Report Now", key="send_report_user",
                 use_container_width=False):
        _send_report(
            receiver_email=email,
            month_str=today.strftime("%m"),
            year_str=today.strftime("%Y"),
            label=month_name,
        )


def _demo_report_section():
    st.markdown("""
    <div class="mw-alert-info" style="margin-bottom:16px;">
        🚀 <b>Demo Mode</b> — Enter any email address and pick any month to generate a real AI report.<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;If Email not received check spam folder
    </div>
    """, unsafe_allow_html=True)

    recipient = st.text_input("📧 Recipient email",
                              placeholder="yourname@example.com",
                              key="demo_email")

    today       = date.today()
    month_names = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]

    c1, c2 = st.columns(2)
    with c1:
        sel_month_name = st.selectbox(
            "📅 Month", month_names,
            index=max(today.month - 2, 0),
            key="demo_month",
        )
        sel_month = month_names.index(sel_month_name) + 1
    with c2:
        sel_year = st.selectbox(
            "📅 Year",
            list(range(2024, today.year + 1)),
            index=today.year - 2024,
            key="demo_year",
        )

    label = f"{sel_month_name} {sel_year}"
    if st.button(f"📬 Generate & Send {label} Report", key="send_demo_report",
                 use_container_width=True):
        if not recipient or "@" not in recipient:
            st.error("⚠️ Please enter a valid email address.")
        else:
            _send_report(
                receiver_email=recipient,
                month_str=f"{sel_month:02d}",
                year_str=str(sel_year),
                label=label,
            )


def _send_report(receiver_email: str, month_str: str, year_str: str, label: str):
    with st.spinner(f"🤖 Generating AI report for {label}…"):
        try:
            from services.report_service import execute_monthend_workflow
            result = execute_monthend_workflow(
                receiver_email=receiver_email,
                month_str=month_str,
                year_str=year_str,
            )
            st.session_state["last_report"] = result
            if receiver_email:
                st.success(f"✅ Report for **{label}** sent to **{receiver_email}**!")
            else:
                st.success(f"✅ Report for **{label}** generated!")
        except Exception as ex:
            st.error(f"❌ {ex}")

    if "last_report" in st.session_state:
        with st.expander("📑 View Generated Report"):
            st.text(st.session_state["last_report"])
