"""
agents/moneywise_agent.py

Assembles the MoneyWise AI LangChain agent (pure LangChain, no LangGraph).
Imports all @tool functions from services/ and builds an AgentExecutor.

Always call get_agent() per-request so the latest GROQ_API_KEY entered
via the sidebar is honoured.
"""

import os
from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

from services.transaction_service import (
    add_transaction,
    get_transactions,
    update_transactions,
    delete_transactions,
    get_savings,
)
from services.goal_service import (
    create_goal,
    get_goals,
    update_goals,
    delete_goal,
)
from services.sql_service import generate_and_execute_sql


SYSTEM_PROMPT = """
You are MoneyWise AI, a personal finance assistant. You MUST use the provided tools to answer questions. Never make up data.

TODAY'S DATE: {today}

RULES:
- Do NOT answer from memory. You MUST use the provided tools to interact with the database.
- IRRELEVANT QUERIES: If the user asks something completely unrelated to personal finance, budgeting, or this app, do NOT call any tools. Politely reply that you are a personal finance assistant and can only help with finance-related questions.
- No amount given for add → ask the user first.
- No results from tool → reply "No records found." DO NOT retry the same tool with different parameters if no records were found; simply report the result.
- Use ₹ for currency. ALWAYS use Indian number formatting: 1,00,000 (Lakhs) and 1,00,00,000 (Crores).
- SHORTHAND: When discussing large amounts in text, prefer "L" for Lakhs and "Cr" for Crores (e.g., ₹1.5L, ₹2Cr).
- IMPORTANT: Once a tool returns a success message or a list of records (like SQL results), you MUST IMMEDIATELY STOP calling tools and return your final answer to the user. Do NOT call any tool again for the same request!
- SQL RESULTS: Once you have the data from the SQL tool, summarize it clearly and STOP. Do not try to "refine" the query if you already have the data.
- CRITICAL: NEVER retry a tool call if it returns "No records found" or if you already have the data you need. Just tell the user the result.
- DISAMBIGUATION PROTOCOL (CRITICAL):
  - When a delete or update tool returns a message starting with "⚠️ Multiple", that IS your final answer. 
    Copy it EXACTLY to the user and STOP. Do NOT call any tool again.
  - Only call delete/update with Id=<integer> when the user explicitly gives you a specific ID number.
  - To delete multiple known records: use Ids=[id1, id2, ...] (never by name when duplicates exist).
  - DeleteAllMatches does NOT exist. Never use it.
- When returning a list of records (e.g. multiple transactions, goals, or SQL results), ALWAYS format the output as a clean, readable Markdown table.
- NEVER pass Id as a string. If you don't know the Id, DO NOT include the Id parameter in your tool call.
- NEVER pass user_id. DO NOT include the user_id parameter in your tool calls.
- If you do not know the value for any optional parameter (like Title, Amount, Category, Type, Mode, Date, etc.), DO NOT include that parameter in your tool call. NEVER pass the string "null" or "None".

DEADLINES FROM RELATIVE TIME:
- When the user says "for X months", "for X years", "in X years and Y months" etc., calculate the actual YYYY-MM-DD deadline by adding that duration to TODAY'S DATE shown above.
- Examples (if today is 2026-05-14):
  - "for 1 year" → Deadline="2027-05-14"
  - "for 6 months" → Deadline="2026-11-14"
  - "for 1 year and 3 months" → Deadline="2027-08-14"
  - "by December 2026" → Deadline="2026-12-31"
  - "by March 2027" → Deadline="2027-03-31"

AMOUNTS:
- ₹1.2L = 120000, ₹2.5L = 250000, ₹1Cr = 10000000
- Always convert shorthand to numeric before calling tools.

INTENT:
- show/list/fetch/get/history → get_transactions / get_goals / get_savings
- spent/bought/paid/received  → add_transaction
- update/change/edit          → update_transactions / update_goals
- delete/remove               → delete_transactions / delete_goal  [NEVER use SQL for delete]
- analytics/biggest/trend/compare/how much total → generate_and_execute_sql

CATEGORIES:
Expense: Food, Groceries, Transport, Education, Shopping, Entertainment, Healthcare, Bills, Travel, Subscription, Investment, Other
Income: Salary, Pocket Money, Freelancing, Business, Gift, Refund, Cashback, Other

Type: Expense = money going out. Income = money coming in.
Mode default for add_transaction: Online.
"""

_TOOLS = [
    generate_and_execute_sql,
    add_transaction,
    delete_transactions,
    update_transactions,
    get_transactions,
    get_savings,
    create_goal,
    delete_goal,
    update_goals,
    get_goals,
]


def get_agent():
    """
    Returns a fresh AgentExecutor using the correct API KEY.
    For demo users, uses ChatNVIDIA and NVIDIA_API_KEY.
    For real users, uses ChatGroq and GROQ_API_KEY.
    """
    import streamlit as st
    import os
    from langchain_core.prompts import ChatPromptTemplate
    from dotenv import load_dotenv

    load_dotenv(override=True)
    
    is_guest = False
    try:
        is_guest = st.session_state.get("is_guest", False)
    except Exception:
        pass

    # For guest, force NVIDIA demo
    if is_guest:
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        api_key = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY", "")
        llm = ChatNVIDIA(
            model="meta/llama-3.3-70b-instruct",
            api_key=api_key,
            temperature=0,
            max_tokens=2048,
        )
    else:
        # For logged-in users, try Groq first, then fallback to NVIDIA
        try:
            groq_key = st.session_state.get("api_key") or os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            groq_key = os.getenv("GROQ_API_KEY", "")
            
        if groq_key:
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=groq_key,
                temperature=0,
                max_tokens=2048,
            )
        else:
            nvidia_key = os.getenv("NVIDIA_API_KEY") or st.secrets.get("NVIDIA_API_KEY", "")
            if nvidia_key:
                from langchain_nvidia_ai_endpoints import ChatNVIDIA
                llm = ChatNVIDIA(
                    model="meta/llama-3.3-70b-instruct",
                    api_key=nvidia_key,
                    temperature=0,
                    max_tokens=2048,
                )
            else:
                from langchain_groq import ChatGroq
                llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    api_key="",
                    temperature=0,
                    max_tokens=2048,
                )

    from datetime import date as _date
    today_str = _date.today().isoformat()
    system_prompt_today = SYSTEM_PROMPT.format(today=today_str)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_today),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, _TOOLS, prompt)
    return AgentExecutor(
        agent=agent,
        tools=_TOOLS,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True,
    )


