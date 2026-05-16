"""
services/report_service.py

Month-end financial report: fetch data → LLM summary → email with CSV attachment.
Refactored for security, user isolation, and production readiness.
"""

import os
import smtplib
from datetime import date
from typing import Optional, Tuple
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid
import streamlit as st

from config import get_client
from database.connection import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_month_end_data(user_id: int, month_str: str = None, year_str: str = None) -> Tuple[Optional[pd.DataFrame], float, float, float]:
    """Fetch and aggregate transactions for the given month/year with user isolation."""
    try:
        if not month_str or not year_str:
            today = date.today()
            month_str = today.strftime("%m")
            year_str  = today.strftime("%Y")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT Id, Date, Title, Amount, Type, Category, Mode, User_Id FROM Transactions "
            "WHERE User_Id=? AND strftime('%m', Date)=? AND strftime('%Y', Date)=?",
            (user_id, month_str, year_str),
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None, 0, 0, 0

        month_df = pd.DataFrame(rows, columns=[
            "Id", "Date", "Title", "Amount", "Type", "Category", "Mode", "User_Id"
        ])
        
        # Security: Remove User_Id before any report generation or export
        month_df = month_df.drop(columns=["User_Id"])
        month_df["Id"] = range(1, len(month_df) + 1)

        expense = month_df[month_df["Type"] == "Expense"]["Amount"].sum()
        income  = month_df[month_df["Type"] == "Income"]["Amount"].sum()
        savings = income - expense

        return month_df, income, expense, savings
    except Exception as e:
        logger.error(f"Error generating month end data for user {user_id}: {e}")
        return None, 0, 0, 0

def generate_ai_report(month_df: pd.DataFrame, income: float, expense: float, savings: float, month_str: str = None, year_str: str = None) -> str:
    """Use the LLM to write a personalized financial summary."""
    try:
        if month_df is None or month_df.empty:
            return "No financial activity recorded for this month."

        category_summary = (
            month_df[month_df["Type"] == "Expense"]
            .groupby("Category")["Amount"]
            .sum()
            .sort_values(ascending=False)
            .to_string()
        )

        if month_str and year_str:
            report_period = date(int(year_str), int(month_str), 1).strftime('%B %Y')
        else:
            report_period = date.today().strftime('%B %Y')

        prompt = f"""You are a professional personal finance assistant.
Analyse the user's financial data for {report_period} and generate a personalised financial report.

Monthly Summary ({report_period}):
Total Income:  ₹{income:,.2f}
Total Expense: ₹{expense:,.2f}
Net Savings:   ₹{savings:,.2f}

Category-wise Expenses:
{category_summary}

Recent Transactions:
{month_df.head(15).to_string(index=False)}

Rules: 
- Address the user directly ("you").
- 200-300 words.
- Professional but encouraging tone.
- Provide 2-3 specific insights based on the data.
"""
        client = get_client()
        response = client.invoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"AI Report generation failed: {e}")
        return "Error: Could not generate AI summary at this time."

def send_monthly_report_email(receiver_email: str, llm_report: str, csv_data_bytes: bytes,
                              income: float = 0, expense: float = 0, savings: float = 0,
                              month_str: str = None, year_str: str = None):
    """Send the report + CSV via Gmail SMTP. Secrets loaded from environment."""
    # Task 8: Secrets handling
    EMAIL_USER = os.getenv("EMAIL_USER") or st.secrets.get("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS") or st.secrets.get("EMAIL_PASS")

    if not EMAIL_USER or not EMAIL_PASS:
        logger.error("Email credentials missing in environment/secrets.")
        raise ValueError("Email credentials not configured.")

    if month_str and year_str:
        report_period = date(int(year_str), int(month_str), 1).strftime('%B %Y')
    else:
        report_period = date.today().strftime('%B %Y')

    try:
        msg = MIMEMultipart()
        msg["Subject"]  = f"💰 MoneyWise Financial Report — {report_period}"
        msg["From"]     = f"MoneyWise AI <{EMAIL_USER}>"
        msg["To"]       = receiver_email
        msg["Date"]     = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="moneywise.ai")

        html_body = f"""
        <html>
        <body style="margin:0;padding:0;background:#f8fafc;font-family:'Segoe UI',Arial,sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:24px 0;">
                <tr><td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;border:1px solid #e2e8f0;overflow:hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="background:#1e293b;padding:24px 32px;">
                                <h1 style="color:#ffffff;font-size:22px;font-weight:700;margin:0;">MoneyWise AI</h1>
                                <p style="color:#94a3b8;font-size:13px;margin:4px 0 0;">Financial Report - {report_period}</p>
                            </td>
                        </tr>

                        <!-- Summary Cards -->
                        <tr>
                            <td style="padding:24px 32px 0;">
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td width="33%" style="padding:0 6px 0 0;">
                                            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:14px;text-align:center;">
                                                <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">Income</div>
                                                <div style="font-size:20px;font-weight:700;color:#059669;margin-top:4px;">&#x20B9;{income:,.0f}</div>
                                            </div>
                                        </td>
                                        <td width="33%" style="padding:0 3px;">
                                            <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:14px;text-align:center;">
                                                <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">Expenses</div>
                                                <div style="font-size:20px;font-weight:700;color:#dc2626;margin-top:4px;">&#x20B9;{expense:,.0f}</div>
                                            </div>
                                        </td>
                                        <td width="33%" style="padding:0 0 0 6px;">
                                            <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:14px;text-align:center;">
                                                <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">Net Savings</div>
                                                <div style="font-size:20px;font-weight:700;color:#2563eb;margin-top:4px;">&#x20B9;{savings:,.0f}</div>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- AI Analysis -->
                        <tr>
                            <td style="padding:24px 32px;">
                                <h2 style="font-size:16px;font-weight:600;color:#1e293b;margin:0 0 12px;border-bottom:1px solid #e2e8f0;padding-bottom:8px;">AI Analysis</h2>
                                <div style="white-space:pre-wrap;line-height:1.7;font-size:14px;color:#334155;">{llm_report}</div>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background:#f8fafc;padding:16px 32px;border-top:1px solid #e2e8f0;">
                                <p style="font-size:12px;color:#94a3b8;margin:0;text-align:center;">
                                    Generated by MoneyWise AI &middot; {date.today().strftime('%d %B %Y')}<br>
                                    Full transaction data attached as CSV.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td></tr>
            </table>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html"))

        attachment = MIMEApplication(csv_data_bytes, Name="monthly_transactions.csv")
        attachment["Content-Disposition"] = 'attachment; filename="monthly_transactions.csv"'
        msg.attach(attachment)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        logger.info(f"Report email sent to {receiver_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {receiver_email}: {e}")
        raise

def execute_monthend_workflow(receiver_email: str = None, month_str: str = None, year_str: str = None, user_id: Optional[int] = None) -> str:
    """Full pipeline: fetch → AI summary → optionally email."""
    u_id = user_id or st.session_state.get('user_id')
    if not u_id:
        return "Error: Authentication required."

    month_df, income, expense, savings = generate_month_end_data(u_id, month_str, year_str)

    if month_df is None or month_df.empty:
        return "No transactions found for the specified period."

    report = generate_ai_report(month_df, income, expense, savings, month_str, year_str)

    if receiver_email:
        try:
            csv_bytes = month_df.to_csv(index=False).encode("utf-8")
            send_monthly_report_email(receiver_email, report, csv_bytes,
                                      income=income, expense=expense, savings=savings,
                                      month_str=month_str, year_str=year_str)
        except Exception as e:
            return f"{report}\n\n---\n⚠️ Error sending email: {str(e)}"

    return report
