from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional
import streamlit as st

from database.connection import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)

def _get_transactions_df(user_id: int):
    """Internal helper to fetch transactions as a DataFrame with user isolation."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Enforce user isolation with explicit column names
        cursor.execute("SELECT Id, Date, Title, Amount, Type, Category, Mode, User_Id FROM Transactions WHERE User_Id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return pd.DataFrame()
            
        df = pd.DataFrame(rows, columns=[
            "id", "date", "title", "amount", "type", "category", "mode", "user_id"
        ])
        df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
        return df
    except Exception as e:
        logger.error(f"Failed to fetch transactions DF for user {user_id}: {e}")
        return pd.DataFrame()

def _get_goals_df(user_id: int):
    """Internal helper to fetch goals as a DataFrame with user isolation."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Id, Title, Started_At, Deadline, Target_Amount, Saved_Amount, Status, User_Id FROM Goals WHERE User_Id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return pd.DataFrame()
            
        df = pd.DataFrame(rows, columns=[
            "id", "Title", "Started_at", "Deadline", "Target_Amount", "Saved_Amount", "Status", "user_id"
        ])
        df['Started_at'] = pd.to_datetime(df['Started_at'], errors='coerce')
        df['Deadline']   = pd.to_datetime(df['Deadline'],   errors='coerce')
        return df
    except Exception as e:
        logger.error(f"Failed to fetch goals DF for user {user_id}: {e}")
        return pd.DataFrame()

def plot_income_vs_expense(year: int, user_id: Optional[int] = None):
    u_id = user_id or st.session_state.get('user_id')
    if not u_id: return None

    try:
        df = _get_transactions_df(u_id)
        if df.empty:
            return None
            
        in_vs_ex_df = df[df['date'].dt.year == year].copy()
        if in_vs_ex_df.empty:
            return None
            
        in_vs_ex_df['month'] = in_vs_ex_df['date'].dt.strftime('%b')
        plot_df = in_vs_ex_df.groupby(['month', 'type'])['amount'].sum().reset_index()
        
        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        income, expense = [], []
        
        for month in month_order:
            iv = plot_df[(plot_df['month']==month) & (plot_df['type']=='Income')]['amount']
            ev = plot_df[(plot_df['month']==month) & (plot_df['type']=='Expense')]['amount']
            income.append(iv.values[0] if not iv.empty else 0)
            expense.append(ev.values[0] if not ev.empty else 0)
            
        x = np.arange(len(month_order))
        width = 0.35
        fig, ax = plt.subplots(figsize=(12, 5))
        b1 = ax.bar(x - width/2, income,  width, label='Income', color='#10b981')
        b2 = ax.bar(x + width/2, expense, width, label='Expense', color='#ef4444')
        
        ax.bar_label(b1, fmt='%.0f', padding=3, fontsize=8)
        ax.bar_label(b2, fmt='%.0f', padding=3, fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels(month_order)
        ax.set_title(f"Income vs Expense - {year}", fontsize=14, pad=20)
        ax.legend()
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Plotting income vs expense failed: {e}")
        return None

def plot_category_expense_donut(year: int, month: int, user_id: Optional[int] = None):
    u_id = user_id or st.session_state.get('user_id')
    if not u_id: return None

    try:
        df = _get_transactions_df(u_id)
        if df.empty: return None
        
        month_df = df[
            (df['date'].dt.year == year) & 
            (df['date'].dt.month == month) & 
            (df['type'] == 'Expense')
        ]
        if month_df.empty: return None
        
        cat_exp = month_df.groupby('category')['amount'].sum().sort_values(ascending=False)
        total_exp = cat_exp.sum()
        
        fig, ax = plt.subplots(figsize=(8, 8))
        colors = sns.color_palette("viridis", len(cat_exp))
        
        def fmt(pct):
            return f"{pct:.1f}%\n₹{int(pct/100*total_exp):,}"
            
        ax.pie(cat_exp, labels=cat_exp.index, autopct=fmt, startangle=90, 
               wedgeprops=dict(width=0.4, edgecolor='w'), colors=colors)
        
        month_name = pd.Timestamp(year=year, month=month, day=1).strftime('%B')
        ax.set_title(f"{month_name} {year} - Category Expenses", fontsize=14)
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Plotting category donut failed: {e}")
        return None

def plot_savings_trend(year: int, user_id: Optional[int] = None):
    u_id = user_id or st.session_state.get('user_id')
    if not u_id: return None

    try:
        df = _get_transactions_df(u_id)
        if df.empty: return None
        
        year_df = df[df['date'].dt.year == year].copy()
        if year_df.empty: return None
        
        year_df['month'] = year_df['date'].dt.strftime('%b')
        monthly = year_df.groupby(['month','type'])['amount'].sum().unstack(fill_value=0)
        
        for t in ['Income', 'Expense']:
            if t not in monthly: monthly[t] = 0
            
        monthly['Savings'] = monthly['Income'] - monthly['Expense']
        month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly = monthly.reindex(month_order).fillna(0)
        
        savings_df = monthly.reset_index()
        savings_df.rename(columns={'month': 'Month'}, inplace=True)
        
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.lineplot(data=savings_df, x='Month', y='Savings', marker='o', linewidth=3, ax=ax, color='#3b82f6')
        
        for i, v in enumerate(savings_df['Savings']):
            ax.text(i, v + (savings_df['Savings'].abs().max()*0.05), f'₹{int(v):,}', ha='center')
            
        ax.set_title(f"Savings Trend - {year}", fontsize=14)
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Plotting savings trend failed: {e}")
        return None

def plot_goal_progress(user_id: Optional[int] = None):
    u_id = user_id or st.session_state.get('user_id')
    if not u_id: return None

    try:
        df = _get_goals_df(u_id)
        if df.empty: return None
        
        df = df.copy()
        df['Progress'] = (df['Saved_Amount'] / df['Target_Amount'].replace(0,1) * 100).clip(0, 100)
        df = df.sort_values('Progress', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.barplot(data=df, x='Progress', y='Title', hue='Status', dodge=False, ax=ax)
        
        for i, v in enumerate(df['Progress']):
            ax.text(v + 1, i, f'{v:.1f}%', va='center')
            
        ax.set_xlim(0, 115)
        ax.set_title("Goal Progress Tracker", fontsize=14)
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Plotting goal progress failed: {e}")
        return None
