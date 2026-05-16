import bcrypt
import streamlit as st
import secrets
from datetime import datetime, timedelta

from database.connection import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)

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


def request_password_reset(email):
    """Initiates password reset flow by sending an OTP."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return "If an account exists, a reset code has been sent."
        
    user_id = user[0]
    
    # Check cooldown (e.g., 1 minute)
    cursor.execute("""
        SELECT Created_At FROM Password_Resets 
        WHERE User_Id = ? AND Created_At > datetime('now', '-1 minute')
        ORDER BY Created_At DESC LIMIT 1
    """, (user_id,))
    recent = cursor.fetchone()
    if recent:
        conn.close()
        return "Please wait a moment before requesting another reset code."
        
    # Generate OTP
    logger.info(f"Password reset requested for {email}")
    otp = str(secrets.randbelow(1000000)).zfill(6)
    otp_hash = bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Invalidate older active OTPs for this user
    cursor.execute("DELETE FROM Password_Resets WHERE User_Id = ?", (user_id,))
    
    cursor.execute("""
        INSERT INTO Password_Resets (User_Id, OTP_Hash, Expires_At)
        VALUES (?, ?, ?)
    """, (user_id, otp_hash, expires_at))
    conn.commit()
    conn.close()
    
    # Simulate sending email
    logger.info(f"PASSWORD RESET OTP for {email}: {otp}")
    
    return "If an account exists, a reset code has been sent."


def verify_and_reset_password(email, otp, new_password):
    """Verifies OTP and resets the password."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT Id FROM Users WHERE Email = ?", (email,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return False, "Invalid OTP or expired."
        
    user_id = user[0]
    
    # Get active OTP
    cursor.execute("""
        SELECT Id, OTP_Hash, Expires_At, Failed_Attempts 
        FROM Password_Resets 
        WHERE User_Id = ?
    """, (user_id,))
    reset_record = cursor.fetchone()
    
    if not reset_record:
        conn.close()
        return False, "Invalid OTP or expired."
        
    record_id, otp_hash, expires_at, failed_attempts = reset_record
    
    # Check max failed attempts (e.g. 5)
    if failed_attempts >= 5:
        cursor.execute("DELETE FROM Password_Resets WHERE Id = ?", (record_id,))
        conn.commit()
        conn.close()
        logger.warning(f"Suspicious activity: Max password reset attempts reached for user_id {user_id}")
        return False, "Too many failed attempts. Please request a new code."
        
    # Check expiration
    if datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') > expires_at:
        cursor.execute("DELETE FROM Password_Resets WHERE Id = ?", (record_id,))
        conn.commit()
        conn.close()
        return False, "OTP has expired. Please request a new code."
        
    # Verify OTP
    if not bcrypt.checkpw(otp.encode(), otp_hash.encode()):
        cursor.execute("UPDATE Password_Resets SET Failed_Attempts = Failed_Attempts + 1 WHERE Id = ?", (record_id,))
        conn.commit()
        conn.close()
        logger.warning(f"Failed password reset attempt for user_id {user_id}")
        return False, "Invalid OTP."
        
    # Success! Update password
    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    cursor.execute("UPDATE Users SET Password_Hash = ? WHERE Id = ?", (new_hash, user_id))
    
    # Invalidate token
    cursor.execute("DELETE FROM Password_Resets WHERE User_Id = ?", (user_id,))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Password reset successfully for user_id {user_id}")
    return True, "Password reset successfully. You can now log in."


def logout_user():

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.is_guest = False