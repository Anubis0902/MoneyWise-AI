"""
ui/styles.py

Injects custom CSS into the Streamlit app.
Supports dark (default) and light themes via CSS custom properties.
Professional, minimal aesthetic — no heavy gradients.
"""

import streamlit as st


def inject_styles():
    theme = st.session_state.get("theme", "dark")
    theme_class = "light-theme" if theme == "light" else ""

    st.markdown(f"""
    <style>
    /* ── Google Fonts ─────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Dark Theme (default) ─────────────────────────────────── */
    :root {{
        --bg-primary:    #000000;
        --bg-secondary:  #0a0a0a;
        --bg-card:       #111111;
        --bg-card-hover: #1a1a1a;
        --bg-input:      #111111;
        --border:        #222222;
        --border-hover:  #333333;
        --accent:        #3b82f6;
        --accent-hover:  #2563eb;
        --accent-subtle: rgba(59, 130, 246, 0.08);
        --green:         #10b981;
        --red:           #ef4444;
        --orange:        #f59e0b;
        --purple:        #8b5cf6;
        --teal:          #14b8a6;
        --text-primary:  #f0f4ff;
        --text-secondary:#94a3b8;
        --text-muted:    #475569;
        --shadow:        0 1px 3px rgba(0, 0, 0, 0.3);
        --shadow-hover:  0 4px 12px rgba(0, 0, 0, 0.4);
    }}

    /* ── Light Theme ──────────────────────────────────────────── */
    .light-theme {{
        --bg-primary:    #f8fafc;
        --bg-secondary:  #ffffff;
        --bg-card:       #ffffff;
        --bg-card-hover: #f1f5f9;
        --bg-input:      #f8fafc;
        --border:        #e2e8f0;
        --border-hover:  #cbd5e1;
        --accent:        #2563eb;
        --accent-hover:  #1d4ed8;
        --accent-subtle: rgba(37, 99, 235, 0.06);
        --green:         #059669;
        --red:           #dc2626;
        --orange:        #d97706;
        --purple:        #7c3aed;
        --teal:          #0d9488;
        --text-primary:  #1e293b;
        --text-secondary:#64748b;
        --text-muted:    #94a3b8;
        --shadow:        0 1px 3px rgba(0, 0, 0, 0.08);
        --shadow-hover:  0 4px 12px rgba(0, 0, 0, 0.1);
    }}

    /* ── Global Reset ──────────────────────────────────────────── */
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif !important;
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }}

    .stApp {{
        background: var(--bg-primary) !important;
    }}

    /* Reduce default Streamlit padding at the top */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }}

    /* ── Hide Streamlit default elements ───────────────────────── */
    #MainMenu, footer {{ visibility: hidden; }}
    header {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}

    /* ── Sidebar toggle — ALWAYS visible ─────────────────────── */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarOpenButton"] {{
        visibility: visible !important;
        opacity: 1 !important;
        display: flex !important;
        pointer-events: all !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        width: 32px !important;
        height: 32px !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: var(--shadow) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }}
    [data-testid="stSidebarCollapseButton"]:hover,
    [data-testid="stSidebarOpenButton"]:hover {{
        background: var(--accent) !important;
        border-color: var(--accent) !important;
    }}
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarOpenButton"] svg {{
        fill: var(--text-secondary) !important;
        width: 14px !important;
        height: 14px !important;
    }}
    [data-testid="stSidebarCollapseButton"]:hover svg,
    [data-testid="stSidebarOpenButton"]:hover svg {{
        fill: white !important;
    }}
    header *,
    header [data-testid],
    [data-testid="stBaseButton-header"],
    button[aria-label*="sidebar"],
    button[aria-label*="Sidebar"] {{
        visibility: visible !important;
        opacity: 1 !important;
        display: flex !important;
        pointer-events: all !important;
    }}

    /* ── Sidebar ───────────────────────────────────────────────── */
    [data-testid="stSidebar"] {{
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }}
    [data-testid="stSidebar"] * {{
        color: var(--text-primary) !important;
    }}

    /* ── Cards ─────────────────────────────────────────────────── */
    .mw-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: var(--shadow);
        transition: all 0.2s ease;
    }}
    .mw-card:hover {{
        border-color: var(--border-hover);
        box-shadow: var(--shadow-hover);
    }}

    /* ── Metric Cards ───────────────────────────────────────────── */
    .mw-metric {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        transition: all 0.2s ease;
    }}
    .mw-metric:hover {{
        border-color: var(--border-hover);
    }}
    .mw-metric-value {{
        font-size: 26px;
        font-weight: 700;
        margin: 6px 0 4px;
    }}
    .mw-metric-label {{
        font-size: 12px;
        color: var(--text-secondary);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .mw-metric-icon {{
        font-size: 22px;
        margin-bottom: 2px;
    }}

    /* ── Page Title ─────────────────────────────────────────────── */
    .mw-page-title {{
        font-size: 26px;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 4px;
    }}
    .mw-page-subtitle {{
        font-size: 14px;
        color: var(--text-secondary);
        margin-bottom: 24px;
    }}

    /* ── Section Headers ────────────────────────────────────────── */
    .mw-section-header {{
        font-size: 17px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 12px;
        padding-bottom: 4px;
    }}

    /* ── Badges ─────────────────────────────────────────────────── */
    .badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }}
    .badge-income  {{ background: rgba(16, 185, 129, 0.12); color: var(--green); border: 1px solid rgba(16, 185, 129, 0.25); }}
    .badge-expense {{ background: rgba(239, 68, 68, 0.12);  color: var(--red);   border: 1px solid rgba(239, 68, 68, 0.25); }}
    .badge-active  {{ background: rgba(59, 130, 246, 0.12); color: var(--accent); border: 1px solid rgba(59, 130, 246, 0.25); }}
    .badge-completed {{ background: rgba(16, 185, 129, 0.12); color: var(--green); border: 1px solid rgba(16, 185, 129, 0.25); }}
    .badge-failed  {{ background: rgba(239, 68, 68, 0.12);  color: var(--red);   border: 1px solid rgba(239, 68, 68, 0.25); }}
    .badge-paused  {{ background: rgba(245, 158, 11, 0.12); color: var(--orange); border: 1px solid rgba(245, 158, 11, 0.25); }}

    /* ── Progress Bar Custom ────────────────────────────────────── */
    .mw-progress-container {{
        background: var(--border);
        border-radius: 6px;
        height: 8px;
        overflow: hidden;
        margin: 8px 0;
    }}
    .mw-progress-bar {{
        height: 100%;
        border-radius: 6px;
        transition: width 0.6s ease;
    }}

    /* ── Buttons ───────────────────────────────────────────────── */
    .stButton > button {{
        background: var(--accent) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 10px 24px !important;
        transition: all 0.15s ease !important;
        font-family: 'Inter', sans-serif !important;
    }}
    .stButton > button:hover {{
        background: var(--accent-hover) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25) !important;
    }}

    /* ── Chat Send button (black) — keyed overrides ─────────────── */
    .st-key-txn_send_btn button,
    .st-key-goal_send_btn button {{
        background: #1a1a1a !important;
        color: white !important;
        border: 1px solid #333333 !important;
        padding: 0 !important;
        min-width: 50px !important;
        width: 50px !important;
        height: 50px !important;
        min-height: 50px !important;
        font-size: 18px !important;
        border-radius: 12px !important;
        box-shadow: none !important;
        transform: none !important;
    }}
    .st-key-txn_send_btn button:hover,
    .st-key-goal_send_btn button:hover {{
        background: #333333 !important;
        border-color: #555555 !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    /* ── Chat Clear button (red) — keyed overrides ──────────────── */
    .st-key-txn_clear_chat button,
    .st-key-goal_clear_chat button {{
        background: #ef4444 !important;
        color: white !important;
        border: none !important;
        padding: 0 !important;
        min-width: 52px !important;
        width: 52px !important;
        height: 52px !important;
        min-height: 52px !important;
        font-size: 18px !important;
        border-radius: 12px !important;
        box-shadow: none !important;
        transform: none !important;
    }}
    .st-key-txn_clear_chat button:hover,
    .st-key-goal_clear_chat button:hover {{
        background: #dc2626 !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    /* Sidebar buttons */
    [data-testid="stSidebar"] .stButton > button {{
        background: var(--accent) !important;
    }}

    /* ── Ghost / Suggestion Buttons ───────────────────────────── */
    .mw-ghost-btn .stButton > button {{
        background: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        font-size: 12px !important;
        font-weight: 400 !important;
        padding: 6px 12px !important;
        min-height: 34px !important;
        height: 34px !important;
        border-radius: 6px !important;
        box-shadow: none !important;
    }}
    .mw-ghost-btn .stButton > button:hover {{
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--accent-subtle) !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    /* ── Unified Chat Input Bar ───────────────────────────────── */
    /* Outer pill container — wraps columns */
    .mw-chat-row > div > div [data-testid="stHorizontalBlock"] {{
        gap: 0 !important;
        background: var(--bg-card) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        align-items: stretch !important;
        transition: border-color 0.2s ease !important;
    }}
    .mw-chat-row > div > div [data-testid="stHorizontalBlock"]:focus-within {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
    }}
    /* Remove column padding */
    .mw-chat-row > div > div [data-testid="stHorizontalBlock"] > div {{
        padding: 0 !important;
    }}
    /* Text input — transparent inside bar */
    .mw-chat-row [data-testid="stTextInput"] {{
        margin: 0 !important;
        padding: 0 !important;
    }}
    .mw-chat-row [data-testid="stTextInput"] label {{
        display: none !important;
    }}
    .mw-chat-row [data-testid="stTextInput"] > div {{
        padding: 0 !important;
    }}
    .mw-chat-row [data-testid="stTextInput"] > div > div {{
        border: none !important;
        background: transparent !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        height: 50px !important;
        padding: 0 16px !important;
    }}
    .mw-chat-row [data-testid="stTextInput"] input {{
        height: 50px !important;
        font-size: 14px !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: var(--text-primary) !important;
        padding: 0 !important;
    }}

    /* Send button (⬆️) */
    div[data-testid="stButton"] button:has(p:contains("⬆️")),
    div[data-testid="stButton"] button:has(span:contains("⬆️")) {{
        background: #000000 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        width: 50px !important;
        height: 50px !important;
        min-height: 50px !important;
        padding: 0 !important;
        margin-top: 0 !important; /* Reset alignment */
        box-shadow: none !important;
        transition: background 0.15s ease !important;
    }}
    div[data-testid="stButton"] button:has(p:contains("⬆️")):hover {{
        background: #333333 !important;
    }}

    /* Clear button (🗑️) */
    div[data-testid="stButton"] button:has(p:contains("🗑️")),
    div[data-testid="stButton"] button:has(span:contains("🗑️")) {{
        background: var(--red) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 16px !important;
        width: 52px !important;
        height: 52px !important;
        min-height: 52px !important;
        padding: 0 !important;
        margin-top: 26px !important; /* Align with form-nested buttons */
        box-shadow: none !important;
        transition: all 0.15s ease !important;
    }}
    div[data-testid="stButton"] button:has(p:contains("🗑️")):hover {{
        background: #dc2626 !important;
        opacity: 0.9 !important;
    }}

    /* ── Secondary / Outline Buttons ──────────────────────────── */
    .mw-outline-btn .stButton > button {{
        background: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }}
    .mw-outline-btn .stButton > button:hover {{
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--accent-subtle) !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    /* ── Chat Input ───────────────────────────────────────────── */
    [data-testid="stChatInput"] {{
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        background: var(--bg-input) !important;
    }}
    [data-testid="stChatInput"]:focus-within {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }}

    /* ── Input Fields ───────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }}
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.12) !important;
    }}

    /* ── Tabs ────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        background: var(--bg-card) !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 4px 4px 0 !important;
        gap: 4px !important;
        border: 1px solid var(--border) !important;
        border-bottom: none !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 8px 8px 0 0 !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 10px 20px !important;
        border: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: var(--accent) !important;
        color: white !important;
        font-weight: 600 !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 0 10px 10px 10px !important;
        padding: 20px !important;
    }}

    /* ── Dataframe ──────────────────────────────────────────────── */
    .stDataFrame {{
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid var(--border) !important;
    }}

    /* ── Alert boxes ─────────────────────────────────────────────── */
    .mw-alert-success {{
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 8px;
        padding: 12px 16px;
        color: var(--green);
        font-weight: 500;
        margin: 8px 0;
    }}
    .mw-alert-error {{
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 8px;
        padding: 12px 16px;
        color: var(--red);
        font-weight: 500;
        margin: 8px 0;
    }}
    .mw-alert-info {{
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 8px;
        padding: 12px 16px;
        color: var(--accent);
        font-weight: 500;
        margin: 8px 0;
    }}

    /* ── Divider ────────────────────────────────────────────────── */
    .mw-divider {{
        height: 1px;
        background: var(--border);
        margin: 20px 0;
    }}

    /* ── Landing / Homepage ─────────────────────────────────────── */
    .landing-hero {{
        text-align: center;
        padding: 30px 20px 40px;
    }}
    .landing-logo {{
        font-size: 48px;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1.1;
        margin-bottom: 12px;
    }}
    .landing-tagline {{
        font-size: 18px;
        color: var(--text-secondary);
        margin-bottom: 32px;
        font-weight: 400;
    }}

    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        padding: 0 20px;
        max-width: 900px;
        margin: 0 auto;
    }}
    @media (max-width: 768px) {{
        .feature-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    .feature-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 24px 20px;
        text-align: center;
        transition: all 0.2s ease;
    }}
    .feature-card:hover {{
        border-color: var(--border-hover);
        box-shadow: var(--shadow-hover);
    }}
    .feature-card-icon {{ font-size: 32px; margin-bottom: 10px; }}
    .feature-card-title {{
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 6px;
    }}
    .feature-card-desc {{
        font-size: 12px;
        color: var(--text-secondary);
        line-height: 1.5;
    }}

    /* ── Auth Cards ─────────────────────────────────────────────── */
    .landing-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 32px 24px;
        min-height: 240px;
        cursor: pointer;
        transition: all 0.2s ease;
        text-align: center;
    }}
    .landing-card:hover {{
        border-color: var(--accent);
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
    }}
    .landing-card-icon {{ font-size: 40px; margin-bottom: 14px; }}
    .landing-card-title {{
        font-size: 18px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 8px;
    }}
    .landing-card-desc {{
        font-size: 13px;
        color: var(--text-secondary);
        line-height: 1.6;
    }}

    /* ── Goal Cards ─────────────────────────────────────────────── */
    .goal-card {{
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid var(--border);
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }}
    .goal-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
    }}
    .goal-active::before    {{ background: var(--accent); }}
    .goal-completed::before {{ background: var(--green); }}
    .goal-failed::before    {{ background: var(--red); }}
    .goal-paused::before    {{ background: var(--orange); }}
    .goal-card:hover {{ border-color: var(--border-hover); }}

    /* ── Scrollbar ──────────────────────────────────────────────── */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}

    /* ── Number/Date Input ───────────────────────────────────────── */
    .stNumberInput input,
    .stDateInput input {{
        background: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }}

    /* ── Expander ───────────────────────────────────────────────── */
    .streamlit-expanderHeader {{
        background: var(--bg-card) !important;
        border-radius: 8px !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }}

    /* ── Checkbox / Radio ────────────────────────────────────────── */
    .stCheckbox label, .stRadio label {{
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }}

    /* ── Native container border ─────────────────────────────────── */
    [data-testid="stVerticalBlockBorderWrapper"] > div {{
        border-color: var(--border) !important;
        border-radius: 12px !important;
        background: var(--bg-card) !important;
        padding: 16px !important;
    }}

    /* ── st.metric ────────────────────────────────────────────────── */
    [data-testid="stMetric"] {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
    }}
    [data-testid="stMetricLabel"] {{
        color: var(--text-secondary) !important;
        font-size: 12px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}
    [data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-size: 22px !important;
        font-weight: 700 !important;
    }}

    /* ── Progress bar ────────────────────────────────────────────── */
    div[data-testid="stProgressBar"],
    .stProgress > div > div {{
        background: var(--border) !important;
        border-radius: 8px !important;
        height: 8px !important;
        overflow: hidden !important;
    }}
    div[data-testid="stProgressBar"] > div,
    .stProgress > div > div > div {{
        background: var(--green) !important;
        border-radius: 8px !important;
        transition: width 0.6s ease !important;
    }}

    /* ── Plotly override ────────────────────────────────────────── */
    .js-plotly-plot .plotly .modebar {{ background: transparent !important; }}

    /* ── Theme toggle button ────────────────────────────────────── */
    .mw-theme-btn .stButton > button {{
        background: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--text-secondary) !important;
        font-size: 13px !important;
        padding: 6px 12px !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }}
    .mw-theme-btn .stButton > button:hover {{
        border-color: var(--accent) !important;
        color: var(--accent) !important;
        background: var(--accent-subtle) !important;
        transform: none !important;
        box-shadow: none !important;
    }}

    /* ── Back link ───────────────────────────────────────────────── */
    .mw-back-link {{
        font-size: 14px;
        color: var(--text-secondary);
        margin-bottom: 16px;
        cursor: pointer;
    }}
    .mw-back-link:hover {{ color: var(--accent); }}

    </style>
    <script>
        // Apply theme class to root
        const theme = "{theme_class}";
        if (theme) {{
            document.documentElement.classList.add(theme);
            document.body.classList.add(theme);
            // Also apply to Streamlit's app container
            const app = document.querySelector('.stApp');
            if (app) app.classList.add(theme);
        }} else {{
            document.documentElement.classList.remove('light-theme');
            document.body.classList.remove('light-theme');
            const app = document.querySelector('.stApp');
            if (app) app.classList.remove('light-theme');
        }}
    </script>
    """, unsafe_allow_html=True)
