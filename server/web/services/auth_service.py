import sqlite3
import uuid
import time
import bcrypt
from pathlib import Path
from typing import Optional

import os
from web.services.config_service import DB_DIR
DB_PATH = os.path.join(DB_DIR, "localmanus.db")

def _get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auth_users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES auth_users(id)
            )
        """)
        conn.commit()

def register(username: str, email: str, password: str) -> dict:
    init_db()
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM auth_users WHERE username = ? OR email = ?", (username, email))
        if cur.fetchone():
            return {"status": "error", "message": "Username or email already exists"}

        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        created_at = time.time()

        cur.execute(
            "INSERT INTO auth_users (id, username, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, email, password_hash, created_at)
        )
        conn.commit()

    token = _generate_token(user_id)
    return {
        "status": "success",
        "token": token,
        "user_info": {
            "id": user_id,
            "username": username,
            "email": email,
        }
    }

def login(username: str, password: str) -> dict:
    init_db()
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, password_hash FROM auth_users WHERE username = ?", (username,))
        row = cur.fetchone()

    if not row:
        return {"status": "error", "message": "Invalid username or password"}

    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return {"status": "error", "message": "Invalid username or password"}

    token = _generate_token(row["id"])
    return {
        "status": "success",
        "token": token,
        "user_info": {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
        }
    }

def refresh_token(token: str) -> dict:
    init_db()
    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.user_id, t.expires_at, u.username, u.email
            FROM auth_tokens t JOIN auth_users u ON t.user_id = u.id
            WHERE t.token = ?
        """, (token,))
        row = cur.fetchone()

        if not row:
            return {"status": "error", "message": "Invalid token"}

        if row["expires_at"] < time.time():
            cur.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
            conn.commit()
            return {"status": "error", "message": "Token expired"}

        cur.execute("DELETE FROM tokens WHERE token = ?", (token,))
        conn.commit()

        user_id = row["user_id"]
        username = row["username"]
        email = row["email"]

    new_token = _generate_token(user_id)
    return {
        "status": "success",
        "new_token": new_token,
        "user_info": {
            "id": user_id,
            "username": username,
            "email": email,
        }
    }

def _generate_token(user_id: str) -> str:
    token = f"local_{uuid.uuid4().hex}"
    created_at = time.time()
    expires_at = created_at + 7 * 24 * 3600

    with _get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO auth_tokens (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, created_at, expires_at)
        )
        conn.commit()

    return token

init_db()
