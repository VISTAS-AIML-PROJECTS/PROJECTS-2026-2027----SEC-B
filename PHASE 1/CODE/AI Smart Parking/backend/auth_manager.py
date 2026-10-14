import secrets
from datetime import datetime, timedelta
from .database import get_connection

# In-memory token store: {token: {admin_id, username, role, expires}}
_active_tokens = {}

TOKEN_EXPIRY_HOURS = 8


# ============================================================
# LOGIN
# ============================================================

def admin_login(username, password):

    username = username.strip()
    password = password.strip()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT admin_id, username, role
        FROM admin_users
        WHERE username = ? AND password = ?
        LIMIT 1
        """,
        (username, password)
    )

    admin = cursor.fetchone()
    connection.close()

    if admin is None:
        return {
            "success": False,
            "message": "Invalid username or password."
        }

    if admin["role"] != "admin":
        return {
            "success": False,
            "message": "Access denied. Admin credentials required."
        }

    token = secrets.token_hex(32)

    _active_tokens[token] = {
        "admin_id": admin["admin_id"],
        "username": admin["username"],
        "role":     admin["role"],
        "expires":  datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    }

    return {
        "success":  True,
        "token":    token,
        "username": admin["username"],
        "role":     admin["role"],
        "message":  "Login successful."
    }


def user_login(username, password):
    username = username.strip()
    password = password.strip()

    connection = get_connection()
    user = connection.execute(
        """
        SELECT admin_id, username, role
        FROM admin_users
        WHERE username = ? AND password = ? AND role = 'user'
        LIMIT 1
        """,
        (username, password)
    ).fetchone()
    connection.close()

    if user is None:
        return {"success": False, "message": "Invalid user credentials."}

    token = secrets.token_hex(32)
    _active_tokens[token] = {
        "admin_id": user["admin_id"],
        "username": user["username"],
        "role": user["role"],
        "expires": datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    return {
        "success": True,
        "token": token,
        "username": user["username"],
        "role": user["role"],
        "message": "Login successful.",
    }


# ============================================================
# VERIFY TOKEN
# ============================================================

def verify_token(token):

    if not token or token not in _active_tokens:
        return None

    data = _active_tokens[token]

    if datetime.now() > data["expires"]:
        del _active_tokens[token]
        return None

    return data


# ============================================================
# LOGOUT
# ============================================================

def admin_logout(token):

    if token in _active_tokens:
        del _active_tokens[token]

    return {"success": True, "message": "Logged out."}
