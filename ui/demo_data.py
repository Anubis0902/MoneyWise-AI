"""
ui/demo_data.py

Generates a high-fidelity, hyper-realistic financial dataset for the MoneyWise demo user.
Simulates 18+ months of transactions, income, investments, and goals for a typical 
Indian working professional.
"""

import random
import bcrypt
from datetime import date, timedelta, datetime
from database.connection import get_connection

DEMO_USER = {
    "username": "Demo User",
    "email": "demo@moneywise.ai",
    "password": "demo1234",
}

def _ensure_demo_user() -> int:
    """Insert the demo user if not present, return the user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (DEMO_USER["email"],))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]

    hashed = bcrypt.hashpw(DEMO_USER["password"].encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "INSERT INTO Users (Username, Email, Password_Hash) VALUES (?, ?, ?)",
        (DEMO_USER["username"], DEMO_USER["email"], hashed),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def _seed_transactions(user_id: int):
    """Generates 1000+ hyper-realistic Indian financial transactions."""
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing if any to ensure fresh start with the new high-fidelity data
    cursor.execute("DELETE FROM Transactions WHERE User_Id = ?", (user_id,))
    
    random.seed(42) # For consistent demo data generation
    
    # ── Configuration ───────────────────────────────────────────
    salary_base = 125_000
    rent_amt = 28_000
    emi_amt = 12_400  # Car loan or personal loan
    
    # ── Category Lists (Descriptions + Avg Amounts) ─────────────
    food_items = [
        ("Zomato – Pizza Hut", 550), ("Swiggy – Biryani Blues", 420), ("McDonald's Maharaja Mac", 380),
        ("Starbucks Coffee", 450), ("Local Chaat Center", 120), ("Haldiram's Lunch", 650),
        ("Subway Meal", 320), ("Tea Post – Ginger Tea", 80), ("Canteen Lunch", 150),
        ("Fine Dining – Dinner", 3500), ("Biryani House", 800), ("Cafe Coffee Day", 280),
        ("KFC – Bucket", 720), ("Domino's Delivery", 580), ("Barbeque Nation", 1800)
    ]
    
    grocery_items = [
        ("Blinkit – Weekly Grocery", 1400), ("Big Basket – Pantry", 2200), ("Local Milk & Bread", 250),
        ("Instamart – Snacks", 450), ("D-Mart Shopping", 4500), ("Fruit Vendor", 300)
    ]
    
    transport_items = [
        ("Uber Ride – Office", 350), ("Ola Auto – Local", 120), ("Rapido Bike", 60),
        ("Metro Card Recharge", 500), ("Petrol – Shell Station", 2500), ("Auto Rickshaw", 80),
        ("Ola Cab – Airport", 850), ("Parking Charges", 100), ("Toll Plaza Payment", 150),
        ("Petrol – HP Pump", 1800), ("Bluebook Car Service", 4500)
    ]
    
    shopping_items = [
        ("Amazon – Electronics", 2499), ("Flipkart – Clothes", 1200), ("Myntra – Sneakers", 4500),
        ("Meesho – Home Utility", 350), ("Nykaa – Grooming", 800), ("Uniqlo – T-shirt", 999),
        ("H&M – Shirt", 1500), ("Decathlon – Gym Wear", 2200), ("Zara – Jeans", 3999),
        ("Ajio – Jacket", 2800), ("Local Boutique", 1800)
    ]
    
    utilities_items = [
        ("Electricity Bill – Adani", 1800), ("Water Bill – Municipal", 350),
        ("Gas Bill – IGL", 950), ("Broadband – Airtel Fiber", 1060),
        ("Jio Recharge – 3 Months", 749), ("DTH Recharge – Tata Play", 450)
    ]
    
    entertainment_items = [
        ("Netflix Premium", 649), ("Spotify Duo", 149), ("Amazon Prime Yearly", 1499),
        ("BookMyShow – Movie", 750), ("PVR Cinemas Popcorn", 450), ("Steam Game Sale", 1200),
        ("Bowling & Arcade", 1500), ("Youtube Premium", 129), ("Club Entry Fee", 2000)
    ]
    
    healthcare_items = [
        ("Apollo Pharmacy", 650), ("Doctor Consultation Fee", 800), ("Lab Test – SRL", 1200),
        ("MedPlus – Vitamins", 450), ("Eye Checkup – Lenskart", 1500), ("Dentist Cleaning", 1800),
        ("Physiotherapy Session", 1000)
    ]
    
    travel_items = [
        ("IndiGo Flight – Bangalore", 5500), ("MakeMyTrip – Hotel", 4200), ("Train Ticket – IRCTC", 1200),
        ("Airbnb – Weekend Getaway", 8500), ("Uber Intercity – Pune", 3500), ("Travel Insurance", 850),
        ("Local Sightseeing", 2500), ("Cafe during travel", 600)
    ]
    
    stationery_items = [
        ("Stationery – Notebooks", 350), ("Parker Vector Pen", 550), ("Art Supplies", 1200),
        ("Office Supplies – Amazon", 800), ("Printer Ink Cartridge", 1800), ("Books – Crossword", 950)
    ]
    
    miscellaneous_items = [
        ("Laundry – Dhobi", 450), ("House Help – Salary", 5000), ("Gift for Friend", 2500),
        ("Charity – Donation", 1000), ("Misc Cash Withdrawal", 2000), ("Unknown – Small UPI", 45)
    ]

    investment_items = [
        ("SIP – Quant Small Cap", 5000), ("SIP – Parag Parikh Flexi", 5000),
        ("Zerodha – Nifty 50 ETF", 10000), ("PPF Account Deposit", 5000),
        ("Gold ETF – Groww", 2000), ("Crypto – CoinDCX", 1000)
    ]

    # ── Generation Loop ──────────────────────────────────────────
    today = date.today()
    start_date = date(2024, 1, 1)
    records = []
    
    cur = start_date.replace(day=1)
    while cur <= today:
        year, month = cur.year, cur.month
        last_day = (cur.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        last_day = min(last_day, today)
        
        # 1. Monthly Credits (Salary + Freelance)
        sal_day = date(year, month, random.randint(1, 2))
        if sal_day <= today:
            # Significant bonuses in March (Year-end) and October (Festive)
            bonus = 0
            if month == 3: bonus = random.randint(50000, 120000)
            if month == 10: bonus = random.randint(30000, 60000)
            
            records.append((user_id, str(sal_day), f"Salary Credit - {cur.strftime('%B')}", salary_base + bonus, "Income", "Salary", "Bank Transfer"))
        
        if random.random() < 0.4: # 40% chance of freelance income
            fl_day = date(year, month, random.randint(5, 25))
            if fl_day <= today:
                fl_title = random.choice(["Freelance – UI Design", "Consulting Fee", "Web Dev Project", "Logo Design Work"])
                records.append((user_id, str(fl_day), fl_title, random.randint(8000, 25000), "Income", "Freelance", "UPI"))

        # 2. Fixed Monthly Expenses (Rent, Bills, EMI)
        rent_day = date(year, month, random.randint(1, 3))
        if rent_day <= today:
            records.append((user_id, str(rent_day), "House Rent Payment", rent_amt, "Expense", "Rent", "Bank Transfer"))
            
        emi_day = date(year, month, 5) # Typical EMI date
        if emi_day <= today:
            records.append((user_id, str(emi_day), "HDFC Car Loan EMI", emi_amt, "Expense", "EMI", "Auto-Debit"))

        for title, base_amt in utilities_items:
            # Not all bills every month, some are quarterly/sporadic
            if random.random() < 0.85:
                d = date(year, month, random.randint(5, 15))
                if d <= today:
                    amt = base_amt + random.randint(-50, 100)
                    records.append((user_id, str(d), title, amt, "Expense", "Utilities", "UPI"))

        # 3. High Frequency Expenses (Food, Transport)
        # 12-20 food transactions per month (more realistic frequency)
        for _ in range(random.randint(12, 20)):
            d = date(year, month, random.randint(1, last_day.day))
            if d > today: continue
            title, base_amt = random.choice(food_items)
            is_weekend = d.weekday() >= 5
            amt = base_amt + random.randint(-50, (300 if is_weekend else 100))
            records.append((user_id, str(d), title, max(amt, 40), "Expense", "Food", "UPI"))

        # 8-15 transport transactions per month
        for _ in range(random.randint(8, 15)):
            d = date(year, month, random.randint(1, last_day.day))
            if d > today: continue
            title, base_amt = random.choice(transport_items)
            amt = base_amt + random.randint(-20, 100)
            records.append((user_id, str(d), title, max(amt, 50), "Expense", "Transport", "UPI"))

        # 4. Lifestyle & Shopping (Shopping, Entertainment)
        # 3-7 shopping per month
        for _ in range(random.randint(3, 7)):
            d = date(year, month, random.randint(1, last_day.day))
            if d > today: continue
            title, base_amt = random.choice(shopping_items)
            # Higher spikes in festival months (Oct/Nov for Diwali)
            mult = 1.8 if month in (10, 11) else 1.0
            amt = (base_amt * mult) + random.randint(-200, 500)
            records.append((user_id, str(d), title, max(amt, 200), "Expense", "Shopping", "Card"))

        # Entertainment spikes on weekends
        for _ in range(random.randint(2, 5)):
            d = date(year, month, random.randint(1, last_day.day))
            if d > today: continue
            title, base_amt = random.choice(entertainment_items)
            if d.weekday() >= 5 or random.random() < 0.2:
                records.append((user_id, str(d), title, base_amt, "Expense", "Entertainment", "Card"))

        # 5. Large / Seasonal Events
        # Travel: Vacation every ~4 months
        if month in (5, 10, 12):
            for _ in range(3):
                d = date(year, month, random.randint(10, 25))
                if d <= today:
                    title, base_amt = random.choice(travel_items)
                    records.append((user_id, str(d), title, base_amt + random.randint(-500, 1000), "Expense", "Travel", "Card"))
        
        # Festivals (Gifts/Spends)
        if month == 11: # Diwali Month example
            for _ in range(3):
                d = date(year, month, random.randint(15, 25))
                if d <= today:
                    records.append((user_id, str(d), "Diwali Gifts & Sweets", random.randint(2000, 8000), "Expense", "Gifts", "UPI"))
        
        # Large Purchase (Laptop, Phone)
        if year == 2024 and month == 9: # iPhone Launch month
            records.append((user_id, "2024-09-22", "Apple iPhone 16 Pro Max", 144900, "Expense", "Shopping", "Card"))
        if year == 2025 and month == 3:
            records.append((user_id, "2025-03-15", "Dell XPS 15 Laptop", 165000, "Expense", "Shopping", "Card"))

        # 6. Healthcare, Stationery, Groceries, Misc
        for cat, items, freq in [
            ("Healthcare", healthcare_items, 0.6), 
            ("Stationery", stationery_items, 0.4), 
            ("Groceries",  grocery_items, 0.9), 
            ("Miscellaneous", miscellaneous_items, 0.8)
        ]:
            if random.random() < freq:
                d = date(year, month, random.randint(1, last_day.day))
                if d <= today:
                    title, base_amt = random.choice(items)
                    records.append((user_id, str(d), title, base_amt + random.randint(-50, 50), "Expense", cat, "UPI"))

        # 7. Recurring Investments
        sip_day = date(year, month, 10)
        if sip_day <= today:
            for title, base_amt in investment_items[:2]:
                records.append((user_id, str(sip_day), title, base_amt, "Expense", "Investments", "Bank Transfer"))
        
        if random.random() < 0.5: # Occasional extra investment
            d = date(year, month, random.randint(15, 28))
            if d <= today:
                title, base_amt = random.choice(investment_items[2:])
                records.append((user_id, str(d), title, base_amt, "Expense", "Investments", "UPI"))

        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)

    # Shuffling records slightly so they don't look perfectly sorted by category in the batch insert
    random.shuffle(records)

    cursor.executemany(
        "INSERT INTO Transactions (User_Id, Date, Title, Amount, Type, Category, Mode) VALUES (?,?,?,?,?,?,?)",
        records,
    )
    conn.commit()
    conn.close()
    print(f"Generated {len(records)} realistic transactions for user {user_id}.")

def _seed_goals(user_id: int):
    """Generates realistic savings goals with varying progress."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Goals WHERE User_Id = ?", (user_id,))

    goals = [
        # (Title, Started_At, Deadline, Target_Amount, Saved_Amount, Status)
        ("Emergency Fund (6 Months)", "2024-01-01", "2024-12-31", 500_000, 500_000, "Completed"),
        ("Goa Trip with Friends",     "2024-03-01", "2024-05-30",  40_000,  40_000, "Completed"),
        ("New MacBook Air M3",        "2024-02-01", "2024-10-15", 115_000,  92_000, "Failed"), # Price hiked/missed deadline
        ("Car Down Payment",          "2024-06-01", "2025-06-30", 300_000, 300_000, "Completed"),
        ("iPhone 16 Pro Fund",        "2024-07-01", "2024-09-20", 130_000, 130_000, "Completed"),
        ("Europe Summer Trip 2026",   "2025-01-01", "2026-05-30", 450_000, 385_000, "Active"),
        ("Home Theatre Setup",        "2025-08-01", "2025-12-31",  80_000,  80_000, "Completed"),
        ("Mutual Fund Milestone",     "2024-01-01", "2025-01-01", 100_000, 100_000, "Completed"),
        ("Royal Enfield Hunter 350",  "2025-10-01", "2026-04-30", 220_000, 220_000, "Completed"),
        ("Health Insurance Corpus",   "2026-01-01", "2026-12-31",  50_000,  18_000, "Active"),
        ("Photography Gear (Sony)",   "2026-02-15", "2026-08-31", 180_000,  45_000, "Active"),
        ("Professional Certifications","2026-03-01", "2026-06-30",  25_000,  20_000, "Active"),
    ]

    cursor.executemany(
        "INSERT INTO Goals (User_Id, Title, Started_At, Deadline, Target_Amount, Saved_Amount, Status) VALUES (?,?,?,?,?,?,?)",
        [(user_id, *g) for g in goals],
    )
    conn.commit()
    conn.close()
    print(f"Generated {len(goals)} realistic goals for user {user_id}.")

def setup_demo_profile() -> int:
    """Entry point for seeding the demo user profile."""
    user_id = _ensure_demo_user()
    _seed_transactions(user_id)
    _seed_goals(user_id)
    return user_id

def get_demo_user_id() -> int:
    """Quick lookup of demo user_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (DEMO_USER["email"],))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
