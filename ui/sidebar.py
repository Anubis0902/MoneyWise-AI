"""
ui/sidebar.py

Sidebar navigation — brand, profile badge, API key, nav buttons, theme toggle, logout.
Smart API key section: demo users see "Using demo key", real users get input prompt.
"""

import os
import streamlit as st
from auth.auth import logout_user
from utils.backup_trigger import trigger_backup_now


NAV_ITEMS = [
    ("💳", "Transactions",       "transactions"),
    ("🎯", "Goals",              "goals"),
    ("📊", "Charts & Analytics", "analytics"),
    ("📄", "Report Generation",  "report"),
]


def render_sidebar() -> str:
    """Renders the sidebar and returns the active page key."""

    # Guarantee default
    if "current_page" not in st.session_state:
        st.session_state.current_page = "transactions"

    with st.sidebar:
        # ── Brand ────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center; padding:16px 0 20px;">
            <div style="font-size:28px; font-weight:800; color:var(--text-primary);">
                MoneyWise AI
            </div>
            <div style="font-size:11px; color:var(--text-muted); margin-top:4px;
                        text-transform:uppercase; letter-spacing:0.1em;">
                AI Finance Assistant
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border:1px solid var(--border); margin:0 0 16px;'>",
                    unsafe_allow_html=True)

        # ── Profile card ─────────────────────────────────────────
        username = st.session_state.get("username", "User") or "User"
        email    = st.session_state.get("email", "")
        is_guest = st.session_state.get("is_guest", False)

        badge_label = "DEMO" if is_guest else "LIVE"
        badge_color = "var(--orange)" if is_guest else "var(--green)"
        initial = username[0].upper() if username else "U"

        st.markdown(f"""
        <div style="background:var(--bg-card); border:1px solid var(--border); border-radius:10px;
                    padding:14px 16px; margin-bottom:16px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="width:36px;height:36px;border-radius:50%;
                            background:var(--accent);
                            display:flex;align-items:center;justify-content:center;
                            font-size:16px;font-weight:700;color:white;flex-shrink:0;">
                    {initial}
                </div>
                <div style="min-width:0; flex:1;">
                    <div style="font-weight:600;font-size:14px;color:var(--text-primary);
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {username}
                    </div>
                    <div style="font-size:11px;color:var(--text-muted);
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {email}
                    </div>
                </div>
                <div style="flex-shrink:0;">
                    <span style="background:rgba(0,0,0,0.1);color:{badge_color};
                    border:1px solid {badge_color};border-radius:10px;
                    padding:2px 8px;font-size:10px;font-weight:600;">{badge_label}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── API key section ──────────────────────────────────────
        if is_guest:
            st.markdown("""
            <div style="background:var(--bg-card); border:1px solid var(--border);
                        border-radius:8px; padding:10px 14px; margin-bottom:16px;
                        font-size:12px; color:var(--text-secondary);">
                🔑 Using demo API key &mdash; no setup needed.
            </div>
            """, unsafe_allow_html=True)
        else:
            with st.expander("🔑 AI API Key", expanded=False):
                st.markdown("""
                <div style="font-size:12px; color:var(--text-muted); margin-bottom:8px;">
                    Enter your Groq API key to enable AI features.<br>
                    Get a free key at <a href="https://console.groq.com" target="_blank" style="color:var(--accent);">console.groq.com</a>
                </div>
                """, unsafe_allow_html=True)
                api_key = st.text_input(
                    "API Key",
                    value=st.session_state.get("api_key", os.getenv("GROQ_API_KEY", "")),
                    type="password",
                    key="sidebar_api_key",
                    placeholder="gsk_...",
                    label_visibility="collapsed",
                )
                if api_key:
                    st.session_state.api_key = api_key
                    os.environ["GROQ_API_KEY"] = api_key
                    st.markdown(
                        "<div style='font-size:12px;color:var(--green);margin-top:4px;'>"
                        "✅ API key active</div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── DB Backup Panel ──────────────────────────────────────────
        with st.expander("🛡️ DB Backup", expanded=False):
            try:
                from utils.db_backup import get_backup_status
                status = get_backup_status()

                if not status["enabled"]:
                    st.markdown(
                        "<div style='font-size:12px;color:var(--text-muted);'>"
                        "⚠️ GitHub backup not configured.<br>"
                        "Add <code>GITHUB_TOKEN</code> & <code>GITHUB_REPO</code> "
                        "to Streamlit secrets to enable."
                        "</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    if status["remote_exists"]:
                        size_kb = round(status["remote_size_bytes"] / 1024, 1) if status["remote_size_bytes"] else "?"
                        st.markdown(
                            f"<div style='font-size:12px;color:var(--text-secondary);'>"
                            f"✅ <b>Backup active</b><br>"
                            f"SHA: <code>{status['remote_sha']}</code> &nbsp;|&nbsp; {size_kb} KB"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<div style='font-size:12px;color:var(--orange);'>"
                            "🟡 No remote backup found yet."
                            "</div>",
                            unsafe_allow_html=True,
                        )

                    # Manual backup button
                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                    if st.button("☁️ Backup Now", key="btn_backup_now", use_container_width=True):
                        trigger_backup_now()
                        st.success("Backup started in background!")

                    # Show last status message if any
                    msg = st.session_state.get("backup_status_msg", "")
                    if msg:
                        st.markdown(
                            f"<div style='font-size:11px;color:var(--text-muted);margin-top:4px;'>{msg}</div>",
                            unsafe_allow_html=True,
                        )
            except Exception as _be:
                st.markdown(
                    f"<div style='font-size:11px;color:var(--text-muted);'>Backup unavailable: {_be}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:11px;color:var(--text-muted);text-transform:uppercase;"
            "letter-spacing:0.08em;padding:0 4px;margin-bottom:6px;'>Navigation</div>",
            unsafe_allow_html=True,
        )

        # ── Nav buttons ──────────────────────────────────────────
        for icon, label, key in NAV_ITEMS:
            label_text = f"{icon}  {label}"
            clicked = st.button(
                label_text,
                key=f"nav_{key}",
                use_container_width=True,
            )
            if clicked:
                st.session_state.current_page = key
                st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border:1px solid var(--border); margin:0 0 12px;'>",
                    unsafe_allow_html=True)


        # ── Logout ───────────────────────────────────────────────
        if st.button("Logout", key="btn_logout", use_container_width=True):
            logout_user()
            for k in ["logged_in", "user_id", "username", "email", "is_guest",
                      "current_page", "current_view", "txn_chat_history",
                      "goal_chat_history", "api_key", "show_auth_form"]:
                st.session_state.pop(k, None)
            st.rerun()

        st.markdown("""
        <div style="text-align:center;font-size:10px;color:var(--text-muted);margin-top:16px;">
            MoneyWise AI &copy; 2024&ndash;2026
        </div>
        """, unsafe_allow_html=True)

    return st.session_state.get("current_page", "transactions")
