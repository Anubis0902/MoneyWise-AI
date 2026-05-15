"""
ui/analytics_page.py

Charts & Analytics — clean tabbed layout with a single year selector at top.
All charts use Plotly on a consistent dark theme.
Tabs: Overview | Spending | Savings | Goals
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from database.connection import get_connection
from utils.formatters import format_indian_currency, format_indian_shorthand

# ── Theme ─────────────────────────────────────────────────────────────────────
BLUE        = "#3b82f6"
PURPLE      = "#8b5cf6"
GREEN       = "#10b981"
ORANGE      = "#f59e0b"
RED         = "#ef4444"
TEAL        = "#14b8a6"

CATEGORY_COLORS = {
    "Food": "#3b82f6", "Transport": "#8b5cf6", "Shopping": "#f59e0b",
    "Rent": "#ef4444", "Entertainment": "#ec4899", "Bills": "#f97316",
    "Healthcare": "#14b8a6", "Investments": "#10b981", "Travel": "#06b6d4",
    "Groceries": "#84cc16", "Education": "#a78bfa", "Subscription": "#fb923c",
    "Salary": "#10b981", "Freelance": "#3b82f6", "Other": "#6b7280",
}

def _get_theme_colors():
    """Returns theme-appropriate colors for Plotly charts."""
    theme = st.session_state.get("theme", "dark")
    if theme == "light":
        return "#ffffff", "#e2e8f0", "#64748b", "#f1f5f9"
    return "#111111", "#222222", "#94a3b8", "#1e1e2e"

def _base_layout():
    bg, grid, text, hover_bg = _get_theme_colors()
    return dict(
        paper_bgcolor=bg,
        plot_bgcolor=bg,
        font=dict(color=text, family="Inter", size=13),
        margin=dict(l=16, r=16, t=48, b=16),
        xaxis=dict(gridcolor=grid, zerolinecolor=grid, showgrid=True),
        yaxis=dict(gridcolor=grid, zerolinecolor=grid, showgrid=True),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)",
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        ),
        hoverlabel=dict(bgcolor=hover_bg, font_color="white", bordercolor=grid),
    )

MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# ── Data loaders ──────────────────────────────────────────────────────────────

def _txn_df(user_id: int) -> pd.DataFrame:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT Date, Type, Category, Amount FROM Transactions WHERE User_Id=?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["Date","Type","Category","Amount"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df.dropna(subset=["Date"])


def _goals_df(user_id: int) -> pd.DataFrame:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT Title, Target_Amount, Saved_Amount, Status FROM Goals WHERE User_Id=?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=["Title","Target_Amount","Saved_Amount","Status"])

# ── Chart builders ────────────────────────────────────────────────────────────

def _chart_income_expense(df: pd.DataFrame, year: int) -> go.Figure | None:
    yr = df[df["Date"].dt.year == year].copy()
    if yr.empty:
        return None
    yr["Month"] = pd.Categorical(yr["Date"].dt.strftime("%b"), categories=MONTH_ORDER, ordered=True)
    agg = yr.groupby(["Month","Type"])["Amount"].sum().reset_index().sort_values("Month")

    fig = px.bar(
        agg, x="Month", y="Amount", color="Type", barmode="group",
        color_discrete_map={"Income": GREEN, "Expense": RED},
        labels={"Amount": "Amount (₹)", "Month": ""},
    )
    fig.update_traces(marker_line_width=0, opacity=0.9)
    fig.update_layout(**_base_layout(), title=f"Income vs Expense — {year}")
    return fig


def _chart_donut(df: pd.DataFrame, year: int, month: int) -> go.Figure | None:
    sel = df[(df["Date"].dt.year == year) & (df["Date"].dt.month == month) & (df["Type"] == "Expense")].copy()
    if sel.empty:
        return None
    agg    = sel.groupby("Category")["Amount"].sum().reset_index().sort_values("Amount", ascending=False)
    colors = [CATEGORY_COLORS.get(c, "#6b7280") for c in agg["Category"]]
    total  = agg["Amount"].sum()
    month_name = pd.Timestamp(year=year, month=month, day=1).strftime("%B %Y")

    fig = go.Figure(go.Pie(
        labels=agg["Category"], values=agg["Amount"],
        hole=0.58,
        marker_colors=colors,
        textinfo="label+percent",
        textfont=dict(size=12),
        customdata=agg["Amount"].apply(lambda x: format_indian_currency(x)).values,
        hovertemplate="<b>%{label}</b><br>%{customdata}<br>%{percent}<extra></extra>",
        pull=[0.04 if i == 0 else 0 for i in range(len(agg))],
    ))
    fig.add_annotation(
        text=f"<b>{format_indian_shorthand(total)}</b><br><span style='font-size:11px'>Total</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(color="white", size=14),
    )
    layout = {**_base_layout()}
    layout.update(title=f"Expense Breakdown — {month_name}", showlegend=True,
                  legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02))
    fig.update_layout(**layout)
    return fig


def _chart_savings_trend(df: pd.DataFrame, year: int) -> go.Figure | None:
    yr = df[df["Date"].dt.year == year].copy()
    if yr.empty:
        return None
    bg, grid, text, hover_bg = _get_theme_colors()
    yr["Month"] = yr["Date"].dt.month
    agg = yr.groupby(["Month","Type"])["Amount"].sum().unstack(fill_value=0).reindex(range(1,13), fill_value=0)
    for col in ["Income","Expense"]:
        if col not in agg:
            agg[col] = 0
    agg["Savings"]   = agg["Income"] - agg["Expense"]
    agg["MonthName"] = [pd.Timestamp(year=year, month=m, day=1).strftime("%b") for m in agg.index]

    bar_colors = [GREEN if s >= 0 else RED for s in agg["Savings"]]

    fig = go.Figure()
    # Income + Expense area
    fig.add_trace(go.Scatter(
        x=agg["MonthName"], y=agg["Income"],
        name="Income", mode="lines",
        line=dict(color=GREEN, width=2, dash="dot"),
        fill=None, opacity=0.7,
    ))
    fig.add_trace(go.Scatter(
        x=agg["MonthName"], y=agg["Expense"],
        name="Expense", mode="lines",
        line=dict(color=RED, width=2, dash="dot"),
        fill="tonexty", fillcolor="rgba(239,68,68,0.07)", opacity=0.7,
    ))
    # Savings bars
    fig.add_trace(go.Bar(
        x=agg["MonthName"], y=agg["Savings"],
        name="Net Savings",
        marker_color=bar_colors,
        opacity=0.85,
        customdata=agg["Savings"].apply(lambda x: format_indian_currency(x)).values,
        hovertemplate="<b>%{x}</b><br>Savings: %{customdata}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color=grid, opacity=0.6)
    fig.update_layout(**_base_layout(), title=f"Savings Trend — {year}", barmode="overlay")
    return fig


def _chart_heatmap(df: pd.DataFrame, year: int) -> go.Figure | None:
    yr = df[(df["Date"].dt.year == year) & (df["Type"] == "Expense")].copy()
    if yr.empty:
        return None
    bg, grid, text, hover_bg = _get_theme_colors()
    yr["Month"]    = yr["Date"].dt.month
    yr["Category"] = yr["Category"].fillna("Other")
    piv = yr.groupby(["Category","Month"])["Amount"].sum().unstack(fill_value=0).reindex(columns=range(1,13), fill_value=0)
    piv.columns = MONTH_ORDER

    ztext = [[format_indian_shorthand(v) if v > 0 else "" for v in row]
             for row in piv.values]

    fig = go.Figure(go.Heatmap(
        z=piv.values, x=list(piv.columns), y=list(piv.index),
        colorscale=[[0,"#0f0f0f"],[0.3,"#1e3a5f"],[0.7,"#2563eb"],[1,"#60a5fa"]],
        text=ztext, texttemplate="%{text}",
        textfont=dict(size=10, color="white"),
        customdata=[[format_indian_currency(v) for v in row] for row in piv.values],
        hovertemplate="<b>%{y} — %{x}</b><br>%{customdata}<extra></extra>",
        showscale=True,
        colorbar=dict(
            thickness=12, bgcolor=bg,
            tickfont=dict(color=text),
            title=dict(text="₹", font=dict(color=text)),
        ),
    ))
    layout = {**_base_layout()}
    layout.update(title=f"Spending Heatmap — {year}",
                  height=max(320, len(piv) * 40 + 80),
                  xaxis=dict(side="top", gridcolor=grid),
                  yaxis=dict(autorange="reversed", gridcolor=grid))
    fig.update_layout(**layout)
    return fig


def _chart_yoy(df: pd.DataFrame) -> go.Figure | None:
    years = sorted(df["Date"].dt.year.unique())
    if len(years) < 2:
        return None
    df2 = df.copy()
    df2["Year"]  = df2["Date"].dt.year
    df2["Month"] = df2["Date"].dt.month
    agg = df2.groupby(["Year","Month","Type"])["Amount"].sum().reset_index()
    exp = agg[agg["Type"] == "Expense"].pivot(index="Month", columns="Year", values="Amount").fillna(0)

    fig = go.Figure()
    palette = [BLUE, PURPLE, GREEN, ORANGE, TEAL, RED]
    for i, yr in enumerate(exp.columns):
        months_available = exp.index.tolist()
        fig.add_trace(go.Scatter(
            x=[MONTH_ORDER[m-1] for m in months_available],
            y=exp[yr].tolist(),
            mode="lines+markers",
            name=str(yr),
            line=dict(color=palette[i % len(palette)], width=2.5),
            marker=dict(size=7, symbol="circle"),
            customdata=exp[yr].apply(lambda x: format_indian_currency(x)).values,
            hovertemplate=f"<b>{yr}</b> — %{{x}}<br>%{{customdata}}<extra></extra>",
        ))
    fig.update_layout(**_base_layout(), title="Year-over-Year Expense Comparison")
    return fig


def _chart_goal_progress(gdf: pd.DataFrame) -> go.Figure | None:
    if gdf.empty:
        return None
    bg, grid, text, hover_bg = _get_theme_colors()
    gdf = gdf.copy()
    gdf["Pct"] = (gdf["Saved_Amount"] / gdf["Target_Amount"].replace(0,1) * 100).clip(0,100)
    gdf = gdf.sort_values("Pct", ascending=True)

    color_map = {"Active": BLUE, "Completed": GREEN, "Failed": RED, "Paused": ORANGE}
    colors = [color_map.get(s, BLUE) for s in gdf["Status"]]

    fig = go.Figure()
    # Track bar
    fig.add_trace(go.Bar(
        x=[100]*len(gdf), y=gdf["Title"], orientation="h",
        marker_color="rgba(255,255,255,0.04)", showlegend=False, hoverinfo="skip",
    ))
    # Progress bar
    fig.add_trace(go.Bar(
        x=gdf["Pct"], y=gdf["Title"], orientation="h",
        marker_color=colors,
        text=[f"  {p:.1f}%" for p in gdf["Pct"]],
        textposition="outside",
        textfont=dict(color=text, size=12),
        customdata=gdf.apply(lambda r: [format_indian_currency(r["Saved_Amount"]), format_indian_currency(r["Target_Amount"]), r["Status"]], axis=1).tolist(),
        hovertemplate=(
            "<b>%{y}</b><br>Progress: %{x:.1f}%<br>"
            "Saved: %{customdata[0]}<br>Target: %{customdata[1]}<br>"
            "Status: %{customdata[2]}<extra></extra>"
        ),
        showlegend=False,
    ))

    layout = {**_base_layout()}
    layout.update(
        barmode="overlay",
        xaxis=dict(range=[0,120], ticksuffix="%", gridcolor=grid),
        yaxis=dict(gridcolor=grid),
        height=max(300, len(gdf)*50 + 60),
        title="Goal Progress",
        margin=dict(l=10, r=100, t=48, b=16),
    )
    fig.update_layout(**layout)
    return fig

# ── Main renderer ─────────────────────────────────────────────────────────────

def render_analytics_page():
    user_id = st.session_state.get("user_id")

    st.markdown("""
    <div class="mw-page-title">📊 Charts & Analytics</div>
    <div class="mw-page-subtitle">Interactive visualizations of your financial data.</div>
    """, unsafe_allow_html=True)

    df  = _txn_df(user_id)
    gdf = _goals_df(user_id)

    if df.empty:
        st.info("No transaction data yet. Add transactions to unlock your analytics.")
        return

    years = sorted(df["Date"].dt.year.unique().tolist(), reverse=True)

    # ── Global control bar ────────────────────────────────────────
    with st.container():
        ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([1, 1, 4])
        with ctrl_c1:
            year = st.selectbox("📅 Year", years, key="analytics_year")
        with ctrl_c2:
            avail_months = sorted(
                df[df["Date"].dt.year == year]["Date"].dt.month.unique().tolist(),
                reverse=True,
            )
            month_fmt = {m: pd.Timestamp(year=year, month=m, day=1).strftime("%B") for m in avail_months}
            month = st.selectbox("📅 Month", avail_months,
                                 format_func=lambda m: month_fmt[m],
                                 key="analytics_month") if avail_months else 1
        with ctrl_c3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            yr_df = df[df["Date"].dt.year == year]
            total_inc = yr_df[yr_df["Type"]=="Income"]["Amount"].sum()
            total_exp = yr_df[yr_df["Type"]=="Expense"]["Amount"].sum()
            st.markdown(
                f"<div style='font-size:13px;color:#94a3b8;padding-top:6px;'>"
                f"<b style='color:#10b981;'>Income {format_indian_shorthand(total_inc)}</b>"
                f"&nbsp;&nbsp;|&nbsp;&nbsp;"
                f"<b style='color:#ef4444;'>Expenses {format_indian_shorthand(total_exp)}</b>"
                f"&nbsp;&nbsp;|&nbsp;&nbsp;"
                f"<b style='color:#3b82f6;'>Savings {format_indian_shorthand(total_inc-total_exp)}</b>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["💰 Overview", "🔥 Spending", "📈 Savings", "🎯 Goals"])

    # ── Tab 1: Overview ───────────────────────────────────────────
    with tab1:
        st.markdown("### Income vs Expense")
        fig = _chart_income_expense(df, year)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for selected year.")

        st.markdown("---")
        st.markdown(f"### Expense by Category — {month_fmt.get(month, '')}")
        fig2 = _chart_donut(df, year, month)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No expense data for selected month.")

    # ── Tab 2: Spending Heatmap ───────────────────────────────────
    with tab2:
        st.markdown("### Spending Heatmap by Category & Month")
        fig = _chart_heatmap(df, year)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data for selected year.")

        if len(years) >= 2:
            st.markdown("---")
            st.markdown("### Year-over-Year Expense Comparison")
            fig2 = _chart_yoy(df)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True)

    # ── Tab 3: Savings ────────────────────────────────────────────
    with tab3:
        st.markdown("### Monthly Savings Trend")
        fig = _chart_savings_trend(df, year)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for selected year.")

    # ── Tab 4: Goals ──────────────────────────────────────────────
    with tab4:
        if gdf.empty:
            st.info("No goals yet. Create goals via the AI assistant.")
        else:
            filt = st.multiselect(
                "Status filter",
                ["Active","Completed","Failed","Paused"],
                default=["Active","Completed","Failed","Paused"],
                key="analytics_goal_filter",
            )
            fgdf = gdf[gdf["Status"].isin(filt)] if filt else gdf
            fig = _chart_goal_progress(fgdf)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No goals match filter.")

            # Summary table
            st.markdown("---")
            disp = fgdf.copy()
            disp["Progress %"] = (disp["Saved_Amount"] / disp["Target_Amount"].replace(0,1) * 100).clip(0,100).round(1)
            disp["Saved"]  = disp["Saved_Amount"].apply(lambda x: format_indian_currency(x))
            disp["Target"] = disp["Target_Amount"].apply(lambda x: format_indian_currency(x))
            st.dataframe(
                disp[["Title","Status","Saved","Target","Progress %"]],
                use_container_width=True, hide_index=True,
            )
