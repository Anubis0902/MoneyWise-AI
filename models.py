from database import get_connection

conn = get_connection()
cursor = conn.cursor()

def create_tables():
    cursor.execute(
        """ CREATE TABLE IF NOT EXISTS expenses (
                Id INTEGER PRIMARY KEY AUTOINCREMENT , 
                Date TEXT ,
                Title TEXT,
                Amount INTEGER ,
                Category TEXT
                )"""
    )

    cursor.execute(
        """ CREATE TABLE IF NOT EXISTS income (
                Id INTEGER PRIMARY KEY AUTOINCREMENT ,
                Date TEXT ,
                Source TEXT
                Amount INTEGER ,
                Title TEXT
                )"""
    )
    cursor.execute(
        """ CREATE TABLE IF NOT EXISTS goals (
                Id INTEGER PRIMARY KEY AUTOINCREMENT ,
                Title TEXT ,
                Started_At TEXT
                Deadline TEXT ,
                Target_Amount INTEGER ,
                Saved_Amount INTEGER ,
                Status TEXT
                )"""
    )

    conn.commit()
    conn.close()

create_tables()