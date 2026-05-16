"""
ui/homepage.py

Scrollable landing page with hero section and feature cards.
Single "Get Started" CTA redirects to the auth page.
"""

import streamlit as st


def show_homepage():
    """Renders the landing page with hero + features."""

    # ── Hero Section ─────────────────────────────────────────────
    st.markdown("""
    <div class="landing-hero">
        <div class="landing-logo">💰 MoneyWise AI</div>
        <div class="landing-tagline">
            Your AI-powered personal finance assistant.<br>
            Track. Analyze. Grow.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Get Started Button ───────────────────────────────────────
    _, center, _ = st.columns([2, 1, 2])
    with center:
        if st.button("Get Started  →", key="btn_get_started", use_container_width=True):
            st.session_state.current_view = "auth"
            st.rerun()

    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)

    # ── Features Section ─────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; margin-bottom:32px;">
        <div style="font-size:22px; font-weight:700; color:var(--text-primary); margin-bottom:6px;">
            Everything you need to manage your finances
        </div>
        <div style="font-size:14px; color:var(--text-secondary);">
            Powered by AI. Built for simplicity.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards — use Streamlit columns for reliable layout (CSS grid doesn't apply to st.markdown)
    fc = [
        ("🤖", "AI Chat Assistant", "Add, update, and query transactions using natural language. No forms needed."),
        ("📊", "Smart Analytics", "Interactive charts showing spending patterns, category breakdowns, and trends."),
        ("🎯", "Savings Goals", "Set financial milestones and track progress with visual dashboards."),
        ("📧", "Monthly Reports", "AI-generated financial summaries delivered straight to your inbox."),
        ("🔒", "Secure & Private", "Bcrypt password hashing, user-isolated data, and parameterized queries."),
        ("💬", "Text2SQL", "Ask complex financial questions in plain English. AI translates to SQL."),
    ]
    row1 = st.columns(3, gap="medium")
    row2 = st.columns(3, gap="medium")
    for i, (icon, title, desc) in enumerate(fc):
        col = row1[i] if i < 3 else row2[i - 3]
        with col:
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;
                        padding:24px 20px;text-align:center;height:160px;
                        display:flex;flex-direction:column;align-items:center;justify-content:center;">
                <div style="font-size:30px;margin-bottom:8px;">{icon}</div>
                <div style="font-size:15px;font-weight:600;color:var(--text-primary);margin-bottom:6px;">{title}</div>
                <div style="font-size:12px;color:var(--text-secondary);line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

    # ── Footer ───────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; font-size:12px; color:var(--text-muted); padding:20px 0 40px;">
        MoneyWise AI &copy;  &nbsp;&middot;&nbsp; Built with Streamlit, LangChain & Groq
    </div>
    """, unsafe_allow_html=True)
