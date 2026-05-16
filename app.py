"""
app.py — MoneyWise AI Entry Point
Run: streamlit run app.py

Three-state router: homepage → auth → dashboard
Supports dark/light theme toggle.
"""

import streamlit as st

st.set_page_config(
    page_title="MoneyWise AI — Personal Finance Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None,
                "About": "MoneyWise AI — Your intelligent personal finance companion."},
)

# ── DB Restore on startup (GitHub backup → local SQLite) ─────────────────────
# Runs once per Streamlit session; restores the DB if the ephemeral filesystem
# doesn't have it yet (e.g. after a Streamlit Cloud reboot).
if "db_restored" not in st.session_state:
    try:
        from utils.db_backup import restore_db_from_github
        restored = restore_db_from_github()  # no-op if local file already exists
        st.session_state["db_restored"] = True
        if restored:
            st.session_state["db_just_restored"] = True
    except Exception as _restore_err:
        import logging
        logging.getLogger(__name__).warning(f"DB restore skipped: {_restore_err}")
        st.session_state["db_restored"] = True

from database.models import create_tables
create_tables()

from ui.styles import inject_styles
inject_styles()

# ── Session-state defaults ─────────────────────────────────────────────────────
_DEFAULTS = {
    "logged_in":          False,
    "user_id":            None,
    "username":           None,
    "email":              "",
    "is_guest":           False,
    "current_view":       "homepage",     # "homepage" | "auth" | "dashboard"
    "current_page":       "transactions",
    "show_auth_form":     False,
    "txn_chat_history":   [],             # Transactions page chat
    "goal_chat_history":  [],             # Goals page chat
    "api_key":            "",
    "theme":              "dark",         # "dark" | "light"
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Router ────────────────────────────────────────────────────────────────────
view = st.session_state.current_view

if view == "homepage" and not st.session_state.logged_in:
    from ui.homepage import show_homepage
    show_homepage()

elif view == "auth" and not st.session_state.logged_in:
    from ui.auth_ui import show_auth_screen
    show_auth_screen()

elif st.session_state.logged_in:
    # Force dashboard view when logged in
    st.session_state.current_view = "dashboard"

    from ui.sidebar import render_sidebar
    page = render_sidebar()

    try:
        if page == "transactions":
            from ui.transactions_page import render_transactions_page
            render_transactions_page()

        elif page == "goals":
            from ui.goals_page import render_goals_page
            render_goals_page()

        elif page == "analytics":
            from ui.analytics_page import render_analytics_page
            render_analytics_page()

        elif page == "report":
            from ui.report_page import render_report_page
            render_report_page()

        else:
            st.error(f"Unknown page: {page!r}")

    except Exception as exc:
        st.error(f"**Page error:** {exc}")
        import traceback
        with st.expander("Full traceback"):
            st.code(traceback.format_exc())

else:
    # Fallback: if not logged in and view is dashboard, go to homepage
    st.session_state.current_view = "homepage"
    st.rerun()
