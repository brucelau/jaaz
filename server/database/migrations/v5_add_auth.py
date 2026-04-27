from . import Migration
import sqlite3


class V5AddAuth(Migration):
    version = 5
    description = "Add auth tables (users, tokens)"

    def up(self, conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES auth_users(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_auth_tokens_expires_at ON auth_tokens(expires_at)
        """)

    def down(self, conn: sqlite3.Connection) -> None:
        conn.execute("DROP TABLE IF EXISTS auth_tokens")
        conn.execute("DROP TABLE IF EXISTS auth_users")