import bcrypt
import streamlit as st

from database.connection import get_connection


def signup_user(username, email, password):

    conn = get_connection()
    cursor = conn.cursor()

    # Check duplicate email
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return False, "Email already registered"

    # Check duplicate username
    cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username already taken. Please choose a different name."

    hashed_password = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    try:
        cursor.execute("""
            INSERT INTO Users (Username, Email, Password_Hash)
            VALUES (?, ?, ?)
        """, (username, email, hashed_password))
        conn.commit()
        return True, "Account created successfully"
    except Exception as e:
        conn.rollback()
        return False, f"Registration failed: {e}"
    finally:
        conn.close()


def login_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Id, Username, Password_Hash
        FROM Users
        WHERE Email = ?
    """, (email,))

    user = cursor.fetchone()

    conn.close()

    if not user:
        return False, "User not found"

    user_id, username, stored_hash = user

    password_correct = bcrypt.checkpw(
        password.encode(),
        stored_hash.encode()
    )

    if not password_correct:
        return False, "Incorrect password"

    st.session_state.logged_in = True
    st.session_state.user_id = user_id
    st.session_state.username = username
    st.session_state.is_guest = False

    return True, "Login successful"


def reset_password(email, new_password):
    """Reset a user's password by email. Returns (success, message)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return False, "No account found with this email address."

    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    cursor.execute("UPDATE Users SET Password_Hash = ? WHERE Email = ?", (hashed, email))
    conn.commit()
    conn.close()

    return True, "Password reset successfully. You can now log in."


def logout_user():

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.is_guest = False