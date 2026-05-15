<div align="center">

<h1>💰 MoneyWise AI</h1>

<p><strong>A production-grade, AI-powered personal finance assistant built with Streamlit, LangChain, and SQLite.</strong><br/>
Track transactions, manage savings goals, get AI-driven insights, and receive automated monthly financial reports — all in one beautifully designed app.</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-1.x-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangChain-0.3-121212?style=for-the-badge&logo=chainlink&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/Deployed-Streamlit_Cloud-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
</p>

<p>
  <img src="https://img.shields.io/badge/Keep--Alive-Playwright_+_GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white"/>
  <img src="https://img.shields.io/badge/Backup-GitHub_API-181717?style=for-the-badge&logo=github&logoColor=white"/>
  <img src="https://img.shields.io/badge/Tests-55_Passing-22c55e?style=for-the-badge&logo=pytest&logoColor=white"/>
</p>

<br/>

> 🎯 **[Live Demo →](https://your-app-url.streamlit.app)** &nbsp;&nbsp; | &nbsp;&nbsp; 💡 Use the **Demo Access** tab — no account needed

</div>

---

## 📖 Table of Contents

- [What is MoneyWise AI?](#-what-is-moneywise-ai)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Quick Start (Local)](#-quick-start-local)
- [Streamlit Cloud Deployment](#-streamlit-cloud-deployment)
- [Secrets & Environment Variables](#-secrets--environment-variables)
- [SQLite Backup & Recovery System](#-sqlite-backup--recovery-system)
- [GitHub Actions (Keep-Alive + Health Check)](#-github-actions-keep-alive--health-check)
- [AI Agent — How It Works](#-ai-agent--how-it-works)
- [Security](#-security)
- [Testing](#-testing)
- [QA Report Summary](#-qa-report-summary)
- [Known Limitations](#-known-limitations)

---

## 🧠 What is MoneyWise AI?

MoneyWise AI is a **full-stack personal finance application** that combines:

- A clean, dark-mode Streamlit UI for tracking income, expenses, and savings goals
- A conversational **LangChain AI agent** (powered by Groq / NVIDIA LLaMA 3.3 70B) that understands natural language — *"Add ₹2,500 for groceries"*, *"How much did I spend on food in April?"*, *"Set a savings goal of ₹1L for my laptop"*
- Interactive **Plotly analytics** — income vs expense bar charts, category donut charts, monthly savings trends, spending heatmaps, and year-over-year comparisons
- Automated **monthly financial reports** delivered by email (HTML + CSV)
- A production-grade **SQLite backup/restore system** using the GitHub Contents API to survive Streamlit's ephemeral filesystem
- **GitHub Actions + Playwright** automation to keep the app awake on Streamlit Community Cloud

This project was built to demonstrate **end-to-end software engineering** at a portfolio level — from natural language processing and agent tool orchestration to DevOps, security hardening, and cloud persistence.

---

## ✨ Features

### 💬 AI-Powered Finance Assistant
- Conversational interface powered by **LangChain `create_tool_calling_agent`** with LLaMA 3.3 70B
- Understands natural Indian currency formats: *"₹1.5L"*, *"2Cr"*, *"fifty thousand"*
- Calculates deadlines from relative time: *"save for 1 year and 3 months"* → `2027-08-15`
- Safe disambiguation: when multiple matching records exist, returns an ID table instead of auto-deleting
- Anti-hallucination: strict `max_iterations=5`, `return_direct=True` on write operations

### 📊 Transactions
- Add, edit, delete, and filter transactions via natural language or the UI
- Filter by title (LIKE), amount range, date range, month, year, type (Income/Expense), category, and payment mode
- 12 expense categories: Food, Groceries, Transport, Education, Shopping, Entertainment, Healthcare, Bills, Travel, Subscription, Investment, Other
- 8 income categories: Salary, Pocket Money, Freelancing, Business, Gift, Refund, Cashback, Other
- Bulk delete with `Ids=[id1, id2, ...]` — no guessing

### 🎯 Savings Goals
- Create goals with target amount and optional deadline
- Incremental savings tracking: *"add ₹5,000 to my laptop fund"*
- Status lifecycle: Active → Completed / Failed / Paused
- AI calculates exact deadline dates from relative expressions

### 📈 Analytics (4-Tab Dashboard)
| Tab | Charts |
|-----|--------|
| **Overview** | Income vs Expense grouped bar chart + Monthly category donut |
| **Spending** | Category × Month heatmap + Year-over-year comparison lines |
| **Savings** | Monthly savings trend with income/expense area fill |
| **Goals** | Horizontal progress bars with status colours |

All charts are **interactive Plotly figures** with hover tooltips in Indian currency format.

### 📧 Monthly Financial Reports
- AI-generated 200–300 word personalised financial summary (LLaMA 3.3 70B)
- Delivered as a professional HTML email with income/expense/savings cards
- Full transaction CSV attached
- Triggered from the Reports page — no scheduling required

### 🔐 Authentication
- Secure bcrypt password hashing (cost factor 12)
- Duplicate email **and** duplicate username detection
- Password reset via email (no verification email — trust-based for portfolio)
- Demo mode with pre-populated 1,000+ transaction dataset

### ☁️ Backup & Recovery
- Automatic SQLite backup to a private GitHub repository via the Contents API
- SHA-256 content verification — skips upload if nothing changed
- Atomic restore on startup if DB is missing or < 8 KB (empty schema detection)
- Manual "☁️ Backup Now" button in the sidebar with live status display

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit 1.x, Plotly, custom CSS (dark/light theme) |
| **AI / LLM** | LangChain 0.3, LangChain-Groq (ChatGroq), LangChain-NVIDIA (ChatNVIDIA) |
| **LLM Models** | `llama-3.3-70b-versatile` (Groq) · `meta/llama-3.3-70b-instruct` (NVIDIA NIM) |
| **Database** | SQLite 3 (WAL mode, bcrypt auth) |
| **Backup** | GitHub Contents API via `requests` + Base64 |
| **Keep-Alive** | Playwright (headless Chromium) + GitHub Actions |
| **Email** | Gmail SMTP via `smtplib` + `email.mime` |
| **Auth** | bcrypt password hashing |
| **CI/CD** | GitHub Actions (2 workflows) |
| **Deployment** | Streamlit Community Cloud (free tier) |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  User Browser                                                     │
│   Streamlit UI  (dark/light theme, 4 pages, Plotly charts)       │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼──────────────────────────────────────┐
│  Streamlit Community Cloud  (ephemeral container)                 │
│                                                                   │
│   app.py ──► restore_db_from_github()  ← on startup              │
│             ├── auth/auth.py           (bcrypt signup/login)      │
│             ├── services/             (LangChain @tools)          │
│             │     ├── transaction_service.py                      │
│             │     ├── goal_service.py                             │
│             │     ├── analytics_service.py (legacy, unused)       │
│             │     ├── report_service.py    (email + LLM)          │
│             │     └── sql_service.py       (Text2SQL)             │
│             ├── agents/moneywise_agent.py  (AgentExecutor)        │
│             ├── ui/analytics_page.py       (Plotly charts)        │
│             └── utils/backup_trigger.py    (background thread)    │
└──────────┬────────────────────────────┬─────────────────────────┘
           │ GitHub Contents API         │ Groq / NVIDIA NIM API
           │ (backup & restore)          │ (LLM inference)
┌──────────▼────────────────┐  ┌────────▼──────────────────────────┐
│  GitHub Backup Repo        │  │  LLaMA 3.3 70B                    │
│  MoneyWise.db (Base64)     │  │  (free tier inference)            │
└───────────────────────────┘  └───────────────────────────────────┘
           ▲
           │ Playwright HTTP ping (every 6 h)
┌──────────┴────────────────┐
│  GitHub Actions (free)     │
│  keep_alive.yml  (6 h)     │
│  db_backup.yml   (daily)   │
└───────────────────────────┘
```

---

## 📁 Project Structure

```
MoneyWise_AI/
│
├── app.py                          # Entry point — routing + startup restore
├── config.py                       # LLM client factory (Groq / NVIDIA)
├── requirements.txt                # All dependencies
│
├── auth/
│   └── auth.py                     # signup, login, reset_password
│
├── database/
│   ├── connection.py               # get_connection() with WAL + busy_timeout
│   └── models.py                   # CREATE TABLE IF NOT EXISTS schema
│
├── services/
│   ├── transaction_service.py      # LangChain @tools for transactions CRUD
│   ├── goal_service.py             # LangChain @tools for goals CRUD
│   ├── sql_service.py              # Text2SQL with multi-layer security
│   ├── analytics_service.py        # (Legacy matplotlib — not used by UI)
│   └── report_service.py           # LLM report + Gmail SMTP email
│
├── agents/
│   └── moneywise_agent.py          # AgentExecutor + system prompt
│
├── ui/
│   ├── auth_ui.py                  # Login / Sign Up / Demo tabs
│   ├── analytics_page.py           # Plotly charts (4-tab dashboard)
│   ├── transactions_page.py        # Transactions UI + AI chat
│   ├── goals_page.py               # Goals UI + AI chat
│   ├── report_page.py              # Monthly report generator
│   ├── sidebar.py                  # Navigation + backup status widget
│   ├── homepage.py                 # Landing page
│   ├── demo_data.py                # Demo user setup (1000+ transactions)
│   └── styles.py                   # Global CSS (dark/light, glassmorphism)
│
├── utils/
│   ├── db_backup.py                # GitHub API backup & restore logic
│   ├── backup_trigger.py           # Background-thread auto-backup trigger
│   ├── logger.py                   # Rotating file logger
│   ├── formatters.py               # Indian currency formatters
│   └── type_helpers.py             # Income/Expense type inference
│
├── prompts/
│   └── sql_prompt.py               # Text2SQL prompt template + schema
│
├── models/
│   ├── finance_command.py          # Pydantic models for transaction commands
│   └── goal_command.py             # Pydantic models for goal commands
│
├── scripts/
│   ├── keep_alive.py               # Playwright keep-alive script (CI)
│   ├── test_deployment.py          # 23-test deployment test suite
│   └── qa_runner.py                # 55-test automated QA runner
│
├── .github/
│   └── workflows/
│       ├── keep_alive.yml          # Playwright ping — every 6 hours
│       └── db_backup.yml           # DB health check — daily
│
└── .streamlit/
    ├── config.toml                 # Theme + server settings
    └── secrets.toml.template       # Template for required secrets
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.10+
- A free [Groq API key](https://console.groq.com) (or NVIDIA NIM key for the demo user)

### 1. Clone & install

```bash
git clone https://github.com/yourusername/MoneyWise_AI.git
cd MoneyWise_AI

python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure secrets

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY    = "gsk_your_groq_key_here"
NVIDIA_API_KEY  = "nvapi-your_nvidia_key_here"   # for demo user

# Optional — leave blank to disable backup/restore
GITHUB_TOKEN    = ""
GITHUB_REPO     = ""
GITHUB_DB_PATH  = "MoneyWise.db"
GITHUB_BRANCH   = "main"

# Optional — for monthly email reports
EMAIL_USER      = ""
EMAIL_PASS      = ""
```

### 3. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) — use the **Demo Access** tab for instant access with pre-populated data.

---

## ☁️ Streamlit Cloud Deployment

### Step 1 — Deploy the app

1. Push this repo to GitHub (your own fork)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your repo, branch `main`, main file `app.py`
4. Add secrets in **Settings → Secrets** (see below)

### Step 2 — Create the backup repository

1. Create a new **private** GitHub repository (e.g. `moneywise-db-backup`)
2. Initialize it with a README so the `main` branch exists

### Step 3 — Generate a GitHub Personal Access Token

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. **Scopes:** ✅ `repo` (full control)
3. **Expiry:** 1 year

### Step 4 — Set Streamlit Cloud secrets

```toml
GROQ_API_KEY    = "gsk_..."
NVIDIA_API_KEY  = "nvapi-..."
GITHUB_TOKEN    = "ghp_..."
GITHUB_REPO     = "yourusername/moneywise-db-backup"
GITHUB_DB_PATH  = "MoneyWise.db"
GITHUB_BRANCH   = "main"
```

### Step 5 — Set GitHub Actions secrets

In your **app repo** → Settings → Secrets → Actions:

| Secret | Value |
|--------|-------|
| `STREAMLIT_APP_URL` | Full URL of your deployed app |
| `BACKUP_GITHUB_TOKEN` | Same PAT from Step 3 |
| `BACKUP_GITHUB_REPO` | `yourusername/moneywise-db-backup` |

---

## 🔑 Secrets & Environment Variables

| Key | Required | Description |
|-----|----------|-------------|
| `GROQ_API_KEY` | Yes (real users) | Groq API key for LLaMA 3.3 70B |
| `NVIDIA_API_KEY` | Yes (demo user) | NVIDIA NIM key for demo AI |
| `GITHUB_TOKEN` | Recommended | PAT for DB backup/restore |
| `GITHUB_REPO` | Recommended | `user/repo` for backup storage |
| `GITHUB_DB_PATH` | Recommended | File path in backup repo |
| `GITHUB_BRANCH` | Recommended | Branch name (default: `main`) |
| `EMAIL_USER` | Optional | Gmail address for reports |
| `EMAIL_PASS` | Optional | Gmail App Password |
| `STREAMLIT_APP_URL` | CI only | Full app URL for keep-alive |
| `BACKUP_GITHUB_TOKEN` | CI only | PAT for health check workflow |
| `BACKUP_GITHUB_REPO` | CI only | Backup repo for health check |

All keys are loaded from `.streamlit/secrets.toml` (Streamlit Cloud) or `.env` (local). **Never commit either file** — both are gitignored.

---

## 🔄 SQLite Backup & Recovery System

Streamlit Community Cloud uses an **ephemeral filesystem** — the container can restart at any time, wiping the local SQLite database. MoneyWise AI solves this with a two-phase system:

### Restore (on startup)
```
App starts
    │
    ├── DB missing or < 8 KB? ──YES──► Download from GitHub backup repo
    │                                   Validate SQLite magic bytes
    │                                   Write atomically (temp file → rename)
    │                                   Log: "✅ Restore complete (X bytes)"
    │
    └── DB exists + > 8 KB? ──NO───► Skip (data is already there)
    │
    ▼
create_tables()   ← CREATE TABLE IF NOT EXISTS — safe no-op on restored DB
```

The **8 KB threshold** is key: a freshly created SQLite file with only the schema (no data) is typically 12–24 KB. A blank file or race-condition stub is 0–4 KB. The old code only checked file existence — the new code checks both existence AND size.

### Backup (during runtime)
- **Auto-trigger:** Every 10 write operations OR every 5 minutes (whichever comes first), a background thread calls `backup_db_to_github()`
- **SHA-256 check:** Computes local file hash and compares to remote. Skips the upload if content hasn't changed — no unnecessary GitHub commits
- **Manual:** Sidebar → "☁️ Backup Now" button
- **Invalid backup rejection:** Remote files < 8 KB are silently rejected on restore to prevent overwriting real data with a corrupted stub

### What gets stored in the backup repo
```
moneywise-db-backup/
└── MoneyWise.db    ← single Base64-encoded SQLite file
                      updated in-place with each backup commit
```

Git commit history in the backup repo provides a lightweight version trail.

---

## ⚙️ GitHub Actions (Keep-Alive + Health Check)

### `keep_alive.yml` — runs every 6 hours

Prevents Streamlit Community Cloud from putting the app to sleep (which happens after ~7 days of zero traffic):

```yaml
schedule:
  - cron: '0 0,6,12,18 * * *'  # 00:00, 06:00, 12:00, 18:00 UTC
```

1. Installs Playwright + Chromium
2. Runs `scripts/keep_alive.py` — opens the app in headless Chrome
3. Waits for `[data-testid='stApp']` selector (confirms full Streamlit render)
4. Holds for 8 seconds, then closes
5. Exits with code 1 if `STREAMLIT_APP_URL` secret is missing (clear error message)

**Free tier usage:** ~600 min/month (limit: 2,000 min/month) ✅

### `db_backup.yml` — runs daily at 03:00 UTC

Health check — does **not** create backups (only the live app can do that). It:
1. Downloads the backup DB from GitHub
2. Validates SQLite magic bytes (`SQLite format 3\x00`)
3. Checks if the backup is fresh (alert if > 48 hours old)
4. Logs a diagnostic report

---

## 🤖 AI Agent — How It Works

The AI assistant is built on **LangChain's `create_tool_calling_agent`** with a strict system prompt and 10 tools:

```
User message
    │
    ▼
AgentExecutor (max_iterations=5, handle_parsing_errors=True)
    │
    ├── Intent: add/spent/received    → add_transaction()
    ├── Intent: show/list/get         → get_transactions() / get_goals()
    ├── Intent: update/change/edit    → update_transactions() / update_goals()
    ├── Intent: delete/remove         → delete_transactions() / delete_goal()
    ├── Intent: analytics/trend/total → generate_and_execute_sql()
    ├── Intent: goal create           → create_goal()
    └── Intent: savings/how much left → get_savings()
```

### Safety features
- **Disambiguation protocol:** If a delete/update matches multiple records by name, the tool returns a markdown table of IDs and **stops** — it never auto-deletes ambiguous matches
- **User isolation:** Every tool call enforces `User_Id = ?` — users cannot read or write each other's data
- **Text2SQL security:** Multi-layer validation — forbidden keyword blocklist, SELECT-only enforcement, sensitive table blocklist, User_Id injection
- **Whitelist for updates:** Only pre-approved field names (`Title`, `Amount`, `Category`, `Mode`, `Type`, `Date`) can be updated — no arbitrary column writes

### Dual LLM mode
| User type | Model | API |
|-----------|-------|-----|
| Demo user | `meta/llama-3.3-70b-instruct` | NVIDIA NIM (free) |
| Real user | `llama-3.3-70b-versatile` | Groq (free tier) |

---

## 🔒 Security

| Area | Implementation |
|------|---------------|
| Passwords | bcrypt hash, cost factor 12 — ~300 ms per hash |
| SQL queries | Parameterised everywhere (`?` placeholders, never f-strings) |
| User data isolation | All queries filter by `User_Id = ?` — cross-user access impossible |
| Text2SQL | Forbidden DML keywords + sensitive table blocklist + SELECT-only enforcement |
| Secrets | Loaded from `secrets.toml` / `.env` — never hardcoded, both files gitignored |
| Session | `st.rerun()` on login/logout clears render context |
| Email | `email.mime` — no header injection risk |
| CSV export | `User_Id` column stripped before export |
| Duplicate auth | Both email AND username uniqueness enforced at DB + application layer |

---

## 🧪 Testing

### Deployment test suite (23 tests)
```bash
# Mocked — safe, no API calls (~0.2 s)
python scripts/test_deployment.py

# Live — real GitHub API calls
python scripts/test_deployment.py --live
```

Covers: config loading, restore logic, backup upload, SHA verification, skip-if-unchanged, environment detection, keep-alive URL validation.

### Full QA runner (55 tests)
```bash
$env:PYTHONIOENCODING='utf-8'; python scripts/qa_runner.py
```

Covers: DB init, WAL mode, SQLite CRUD, 11 auth scenarios, 5 SQL injection payloads, user isolation, 5 transaction filters, 10-thread concurrent writes, GitHub backup system, Text2SQL security, null-string edge cases, requirements integrity, workflow file presence.

**Final results:**
```
✅ 55 PASS  |  ❌ 0 FAIL  |  ⚠️  2 WARN
```

---

## 📋 QA Report Summary

| Metric | Score |
|--------|-------|
| Overall Deployment | **8.2 / 10** |
| Portfolio Readiness | **9.0 / 10** |
| Recruiter Demo Readiness | **9.5 / 10** |

### Bugs found and fixed during QA

| Severity | Bug | Fix |
|----------|-----|-----|
| 🔴 Critical | `bcrypt` missing from `requirements.txt` | Added to requirements |
| 🟠 High | `signup_user` crashes on duplicate username | Added pre-check + rollback |
| 🟡 Medium | `str(None) == "null"` broken null check | New `_null_str()` helper |
| 🔵 Low | SQLite in `delete` journal mode | Enabled WAL + busy_timeout |
| 🔵 Low | Double `conn.close()` in sql_service | Removed redundant close |

---

## ⚠️ Known Limitations

| Limitation | Notes |
|------------|-------|
| SQLite ephemeral disk | DB resets on Streamlit container restart — handled by backup/restore |
| Single-file backup | No point-in-time restore — GitHub commit history provides some history |
| No login rate limiting | Brute-force possible; low priority for portfolio grade |
| UNION injection in Text2SQL | Non-blocklisted tables could be queried; attacker must be authenticated |
| NVIDIA NIM key required | Demo user requires a valid NVIDIA NIM API key in secrets |
| Email optional | Monthly report email requires Gmail App Password configuration |
| GitHub Actions pause | Scheduled workflows pause after 60 days of repo inactivity — make at least one commit every 60 days |

---

## 📄 License

This project is for **portfolio and educational purposes**.  
Feel free to fork, learn from, and adapt the code — attribution appreciated.

---

<div align="center">

**Built with ❤️ using Python, LangChain, Streamlit, and a lot of ₹ signs**

<br/>

*MoneyWise AI — because your finances deserve more than a spreadsheet.*

</div>
