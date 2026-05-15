"""
ui/auth_ui.py

Authentication page with three tabs:
  - Login (with forgot password)
  - Sign Up
  - Demo Access (auto-filled credentials)

Dynamic password visibility toggle. Back-to-home navigation.
"""

import streamlit as st
from auth.auth import signup_user, login_user, reset_password
from ui.demo_data import setup_demo_profile, DEMO_USER


def show_auth_screen():
    """Renders the auth page with Login / Sign Up / Demo tabs."""

    # ── Back to Home ─────────────────────────────────────────────
    if st.button("← Back to Home", key="btn_back_home"):
        st.session_state.current_view = "homepage"
        st.rerun()

    # ── Header ───────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:40px 0 24px;">
        <div style="font-size:36px; font-weight:800; color:var(--text-primary); margin-bottom:6px;">
            MoneyWise AI
        </div>
        <div style="font-size:15px; color:var(--text-secondary);">
            Sign in to manage your finances
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Handle post-signup redirect ──────────────────────────────
    if st.session_state.get("signup_success"):
        st.markdown("<div class='mw-alert-success'>Account created! Please log in.</div>",
                    unsafe_allow_html=True)
        st.session_state.signup_success = False

    # ── Tabs ─────────────────────────────────────────────────────
    _, center, _ = st.columns([1, 2, 1])
    with center:
        tab_login, tab_signup, tab_demo = st.tabs(["Login", "Sign Up", "Demo Access"])

        with tab_login:
            _login_form()

        with tab_signup:
            _signup_form()

        with tab_demo:
            _demo_form()


def _login_form():
    """Login form with dynamic password toggle and forgot password."""
    email = st.text_input("Email Address", key="login_email",
                          placeholder="you@example.com")

    # Dynamic password visibility
    show_pw = st.checkbox("Show password", key="login_show_pw", value=False)
    password = st.text_input(
        "Password",
        type="default" if show_pw else "password",
        key="login_pass",
        placeholder="Your password"
    )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("Login", key="btn_login", use_container_width=True):
        if not email or not password:
            st.markdown("<div class='mw-alert-error'>Please fill in all fields.</div>",
                        unsafe_allow_html=True)
            return
        if "@" not in email:
            st.markdown("<div class='mw-alert-error'>Please enter a valid email address.</div>",
                        unsafe_allow_html=True)
            return
        with st.spinner("Authenticating..."):
            ok, msg = login_user(email, password)
        if ok:
            from database.connection import get_connection
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT Email FROM Users WHERE Id = ?", (st.session_state.user_id,))
            row = cur.fetchone()
            conn.close()
            st.session_state.email = row[0] if row else email
            st.session_state.current_view = "dashboard"
            st.rerun()
        else:
            st.markdown(f"<div class='mw-alert-error'>{msg}</div>", unsafe_allow_html=True)

    # ── Forgot Password ──────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    with st.expander("Forgot password?"):
        _forgot_password_form()


def _forgot_password_form():
    """Inline forgot password: enter email → set new password."""
    reset_email = st.text_input("Enter your registered email",
                                key="reset_email", placeholder="you@example.com")

    show_new_pw = st.checkbox("Show new password", key="reset_show_pw", value=False)
    new_pass = st.text_input(
        "New Password",
        type="default" if show_new_pw else "password",
        key="reset_new_pass",
        placeholder="At least 6 characters"
    )
    confirm_pass = st.text_input(
        "Confirm New Password",
        type="default" if show_new_pw else "password",
        key="reset_confirm_pass",
        placeholder="Repeat new password"
    )

    if st.button("Reset Password", key="btn_reset_pw", use_container_width=True):
        if not reset_email or "@" not in reset_email:
            st.markdown("<div class='mw-alert-error'>Enter a valid email.</div>",
                        unsafe_allow_html=True)
            return
        if len(new_pass) < 6:
            st.markdown("<div class='mw-alert-error'>Password must be at least 6 characters.</div>",
                        unsafe_allow_html=True)
            return
        if new_pass != confirm_pass:
            st.markdown("<div class='mw-alert-error'>Passwords do not match.</div>",
                        unsafe_allow_html=True)
            return
        ok, msg = reset_password(reset_email, new_pass)
        if ok:
            st.markdown(f"<div class='mw-alert-success'>{msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='mw-alert-error'>{msg}</div>", unsafe_allow_html=True)


def _signup_form():
    """Sign up form with dynamic password toggle."""
    username = st.text_input("Full Name", key="signup_name", placeholder="John Doe")
    email = st.text_input("Email Address", key="signup_email", placeholder="you@example.com")

    show_pw = st.checkbox("Show passwords", key="signup_show_pw", value=False)
    password = st.text_input(
        "Password",
        type="default" if show_pw else "password",
        key="signup_pass",
        placeholder="At least 6 characters"
    )
    password2 = st.text_input(
        "Confirm Password",
        type="default" if show_pw else "password",
        key="signup_pass2",
        placeholder="Repeat password"
    )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("Create Account", key="btn_signup", use_container_width=True):
        if not all([username, email, password, password2]):
            st.markdown("<div class='mw-alert-error'>Please fill in all fields.</div>",
                        unsafe_allow_html=True)
            return
        if "@" not in email:
            st.markdown("<div class='mw-alert-error'>Enter a valid email address.</div>",
                        unsafe_allow_html=True)
            return
        if len(password) < 6:
            st.markdown("<div class='mw-alert-error'>Password must be at least 6 characters.</div>",
                        unsafe_allow_html=True)
            return
        if password != password2:
            st.markdown("<div class='mw-alert-error'>Passwords do not match.</div>",
                        unsafe_allow_html=True)
            return
        with st.spinner("Creating your account..."):
            ok, msg = signup_user(username, email, password)
        if ok:
            st.session_state.signup_success = True
            st.rerun()
        else:
            st.markdown(f"<div class='mw-alert-error'>{msg}</div>", unsafe_allow_html=True)


def _demo_form():
    """Demo access with auto-filled credentials."""
    st.markdown("""
    <div class="mw-alert-info" style="margin-bottom:16px;">
        <strong>Demo credentials are pre-filled below.</strong><br>
        Click "Login as Demo User" to explore a fully populated account with 18+ months
        of realistic transactions, goals, and analytics.
    </div>
    """, unsafe_allow_html=True)

    demo_email = st.text_input("Email", value=DEMO_USER["email"],
                               key="demo_login_email", disabled=True)
    demo_pass = st.text_input("Password", value=DEMO_USER["password"],
                              key="demo_login_pass", disabled=True)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("Login as Demo User", key="btn_demo_login", use_container_width=True):
        with st.spinner("Setting up demo profile..."):
            user_id = setup_demo_profile()
        st.session_state.logged_in = True
        st.session_state.user_id = user_id
        st.session_state.username = "Demo User"
        st.session_state.email = DEMO_USER["email"]
        st.session_state.is_guest = True
        st.session_state.current_view = "dashboard"
        st.rerun()

    st.markdown("""
    <div style="text-align:center; margin-top:16px; font-size:13px; color:var(--text-muted);">
        Want to use your own account? Switch to the <strong>Login</strong> or <strong>Sign Up</strong> tab above.
    </div>
    """, unsafe_allow_html=True)
