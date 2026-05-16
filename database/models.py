"""
database/models.py

Creates the Transactions and Goals tables if they don't already exist.
Call create_tables() once at startup (e.g., from main.py).
"""

from database.connection import get_connection


from database.connection import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)

def create_tables() -> None:
    """Creates the core tables for MoneyWise AI."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Username TEXT UNIQUE NOT NULL,
                Email TEXT UNIQUE NOT NULL,
                Password_Hash TEXT NOT NULL,
                Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Transactions (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                User_Id INTEGER NOT NULL,
                Date TEXT,
                Title TEXT,
                Amount REAL,
                Type TEXT,
                Category TEXT,
                Mode TEXT,
                FOREIGN KEY (User_Id) REFERENCES Users(Id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Goals (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                User_Id INTEGER NOT NULL,
                Title TEXT,
                Started_At TEXT,
                Deadline TEXT,
                Target_Amount REAL,
                Saved_Amount REAL,
                Status TEXT,
                FOREIGN KEY (User_Id) REFERENCES Users(Id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Password_Resets (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                User_Id INTEGER NOT NULL,
                OTP_Hash TEXT NOT NULL,
                Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                Expires_At TIMESTAMP NOT NULL,
                Failed_Attempts INTEGER DEFAULT 0,
                FOREIGN KEY (User_Id) REFERENCES Users(Id)
            )
        """)

        conn.commit()
        # Perform safe migration for existing installations
        migrate_to_real(conn)
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        conn.rollback()
    finally:
        conn.close()

def migrate_to_real(conn) -> None:
    """Safely migrates INTEGER amount columns to REAL for existing databases."""
    cursor = conn.cursor()
    
    # Check Transactions
    cursor.execute("PRAGMA table_info(Transactions)")
    cols = cursor.fetchall()
    amount_col = next((c for c in cols if c[1] == "Amount"), None)
    
    if amount_col and amount_col[2].upper() == "INTEGER":
        logger.info("Migrating Transactions.Amount from INTEGER to REAL")
        try:
            # SQLite doesn't support ALTER COLUMN, but it allows inserting floats into INTEGER columns.
            # However, to change the schema definition:
            cursor.execute("CREATE TABLE Transactions_new (Id INTEGER PRIMARY KEY AUTOINCREMENT, User_Id INTEGER NOT NULL, Date TEXT, Title TEXT, Amount REAL, Type TEXT, Category TEXT, Mode TEXT, FOREIGN KEY (User_Id) REFERENCES Users(Id))")
            cursor.execute("INSERT INTO Transactions_new SELECT * FROM Transactions")
            cursor.execute("DROP TABLE Transactions")
            cursor.execute("ALTER TABLE Transactions_new RENAME TO Transactions")
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to migrate Transactions table: {e}")
            conn.rollback()

    # Check Goals
    cursor.execute("PRAGMA table_info(Goals)")
    cols = cursor.fetchall()
    target_col = next((c for c in cols if c[1] == "Target_Amount"), None)
    
    if target_col and target_col[2].upper() == "INTEGER":
        logger.info("Migrating Goals amount columns from INTEGER to REAL")
        try:
            cursor.execute("CREATE TABLE Goals_new (Id INTEGER PRIMARY KEY AUTOINCREMENT, User_Id INTEGER NOT NULL, Title TEXT, Started_At TEXT, Deadline TEXT, Target_Amount REAL, Saved_Amount REAL, Status TEXT, FOREIGN KEY (User_Id) REFERENCES Users(Id))")
            cursor.execute("INSERT INTO Goals_new SELECT * FROM Goals")
            cursor.execute("DROP TABLE Goals")
            cursor.execute("ALTER TABLE Goals_new RENAME TO Goals")
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to migrate Goals table: {e}")
            conn.rollback()